import os
import sys
import time
import shutil
import tempfile
import threading
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from firebase_client import FirebaseClient
from bideo_client import BideoClient
from youtube_worker import YouTubeWorker

SYNC_INTERVAL_SECONDS = 30 * 60  # 30 Minutes


class AutomationScheduler:
    """
    Background worker that runs every 30 minutes:
    - Scrapes paired YouTube channels
    - Detects new and unposted old videos
    - Downloads 1080p MP4 with exact Title & Description
    - Uploads directly to the paired Bideo channel
    - Records state in Firebase to guarantee ZERO duplicates across restarts/redeployments
    - Cleans up disk space immediately
    """

    _thread = None
    _running = False

    @classmethod
    def start(cls):
        if cls._running:
            return
        cls._running = True
        cls._thread = threading.Thread(target=cls._loop, daemon=True)
        cls._thread.start()
        print("[Scheduler] 30-Minute YouTube to Bideo Automation Pipeline Started!")

    @classmethod
    def _loop(cls):
        # Initial wait of 10 seconds on startup
        time.sleep(10)
        while cls._running:
            try:
                cls.run_all_pairings()
            except Exception as e:
                print(f"[Scheduler Loop Error] {e}")

            # Sleep 30 minutes
            time.sleep(SYNC_INTERVAL_SECONDS)

    @classmethod
    def run_all_pairings(cls):
        """Execute automation for all active channel pairings."""
        pairings = FirebaseClient.get_pairings()
        if not pairings:
            return

        print(f"[Scheduler] Running automation cycle across {len(pairings)} channel pairings...")
        for pairing in pairings:
            if not pairing.get("is_active", True):
                continue
            cls.sync_pairing(pairing)

    @classmethod
    def sync_pairing(cls, pairing):
        """
        Sync a single YouTube <---> Bideo pairing:
        Finds unposted video, downloads in 1080p, uploads to Bideo, marks in Firebase.
        """
        pairing_id = pairing.get("id")
        yt_channel_url = pairing.get("yt_channel_url")
        bideo_user_id = pairing.get("bideo_user_id")
        category_id = pairing.get("category_id", "")
        yt_name = pairing.get("yt_channel_name", yt_channel_url)

        if not yt_channel_url or not bideo_user_id:
            return False, "Invalid pairing configuration"

        # 1. Fetch Bideo account credentials from Firebase
        account = FirebaseClient.get_account_by_id(bideo_user_id)
        if not account or not account.get("token"):
            msg = f"Account {bideo_user_id} token missing or not found"
            print(f"[Sync Warning] {msg}")
            FirebaseClient.add_log("Auth Error", msg, "error", {"pairing_id": pairing_id})
            return False, msg

        token = account["token"]
        bideo_channel_name = account.get("name", "Bideo Channel")

        # 2. Scrape videos from YouTube channel
        channel_meta, videos = YouTubeWorker.get_channel_info_and_videos(yt_channel_url, max_results=30)
        if not videos:
            msg = f"No videos found on YouTube channel: {yt_channel_url}"
            print(f"[Sync Notice] {msg}")
            return False, msg

        # Update pairing channel name and canonical URL in Firebase if changed or resolved
        updates = {}
        if channel_meta.get("channel_name") and channel_meta["channel_name"] != yt_name:
            updates["yt_channel_name"] = channel_meta["channel_name"]
            yt_name = channel_meta["channel_name"]
        if channel_meta.get("channel_url") and channel_meta["channel_url"] != yt_channel_url:
            updates["yt_channel_url"] = channel_meta["channel_url"]
            yt_channel_url = channel_meta["channel_url"]
        if updates:
            FirebaseClient.update_pairing(pairing_id, updates)

        # 3. Find candidate unposted video (checks Firebase for duplicate prevention)
        unposted_video = None
        for v in videos:
            vid_id = v.get("id")
            if not FirebaseClient.is_video_posted(vid_id):
                unposted_video = v
                break

        if not unposted_video:
            print(f"[Sync OK] All videos for '{yt_name}' are already posted to Bideo. No new videos.")
            FirebaseClient.update_pairing(pairing_id, {"last_polled_at": datetime.utcnow().isoformat()})
            return True, "Up to date"

        vid_id = unposted_video["id"]
        vid_title = unposted_video["title"]
        print(f"[Sync Action] Found unposted video: '{vid_title}' ({vid_id}) for '{bideo_channel_name}'")

        # 4. Download 1080p MP4 in temporary folder
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                print(f"[Sync Downloading] Fetching 1080p stream for {vid_id}...")
                dl_result = YouTubeWorker.download_video_1080p(vid_id, tmp_dir)

                video_path = dl_result["video_path"]
                thumb_path = dl_result["thumb_path"]
                final_title = dl_result["title"] or vid_title
                description = dl_result["description"] or ""
                is_short = dl_result["is_short"]

                meta = {
                    "duration": dl_result["duration"],
                    "width": dl_result["width"],
                    "height": dl_result["height"]
                }

                # 5. Upload to Bideo API directly under user's channel
                print(f"[Sync Uploading] Publishing '{final_title}' to Bideo channel: {bideo_channel_name}...")
                success, bideo_data, err_msg = BideoClient.upload_video(
                    token=token,
                    video_path=video_path,
                    thumb_path=thumb_path,
                    title=final_title,
                    description=description,
                    category_id=category_id,
                    is_short=is_short,
                    meta=meta
                )

                if not success:
                    fail_msg = f"Failed to upload '{final_title}' to Bideo: {err_msg}"
                    print(f"❌ [Sync Error] {fail_msg}")
                    FirebaseClient.add_log("Upload Failed", fail_msg, "error", {"vid_id": vid_id, "pairing_id": pairing_id})
                    return False, fail_msg

                # 6. Record in Firebase Realtime DB (Guarantees zero re-uploads across restarts)
                bideo_vid_id = bideo_data.get("_id") or bideo_data.get("id", "unknown")
                record = {
                    "yt_video_id": vid_id,
                    "title": final_title,
                    "bideo_video_id": bideo_vid_id,
                    "bideo_user_id": bideo_user_id,
                    "bideo_channel_name": bideo_channel_name,
                    "yt_channel_name": yt_name,
                    "is_short": is_short,
                    "duration": meta["duration"]
                }
                FirebaseClient.mark_video_posted(vid_id, record)

                # 7. Update Pairing Counters
                current_count = pairing.get("total_posted", 0) + 1
                FirebaseClient.update_pairing(pairing_id, {
                    "total_posted": current_count,
                    "last_posted_at": datetime.utcnow().isoformat(),
                    "last_polled_at": datetime.utcnow().isoformat()
                })

                success_msg = f"Successfully published '{final_title}' to '{bideo_channel_name}'!"
                print(f"✅ [Sync Complete] {success_msg}")
                FirebaseClient.add_log("Video Published", success_msg, "success", record)

                return True, success_msg

            except Exception as e:
                err = f"Pipeline execution error for {vid_id}: {str(e)}"
                print(f"❌ [Sync Error] {err}")
                FirebaseClient.add_log("Sync Error", err, "error", {"vid_id": vid_id})
                return False, err
