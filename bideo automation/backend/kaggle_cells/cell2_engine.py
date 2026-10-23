# Cell 2: Autonomous 24/7 Bideo Cloud Automation Engine
import os
import re
import sys
import time
import json
import shutil
import tempfile
import subprocess
import requests
import yt_dlp
from datetime import datetime

# -------------------------------------------------------------
# CONFIGURATION (Auto-Injected by Server)
# -------------------------------------------------------------
FIREBASE_DB_URL = "https://secret-gpt-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_ROOT = "bideo_automation"
BIDEO_API_BASE = "https://bideo.in/api"

# 11 Hours 30 Minutes Session Cap (41,400 seconds)
MAX_RUNTIME_SECONDS = 11.5 * 3600
START_TIME = time.time()

print("=" * 65)
print("🚀 [Kaggle Bideo Engine] Starting 11.5-Hour Autonomous Mega Engine")
print(f"⏰ Session Started At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"⏱️ Auto-Renew Cutoff: In 11 Hours 30 Minutes")
print("=" * 65)


# -------------------------------------------------------------
# FIREBASE REST HELPERS
# -------------------------------------------------------------
def fb_url(path):
    return f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/{path.strip('/')}.json"

def fb_get(path):
    try:
        r = requests.get(fb_url(path), timeout=10)
        return r.json() if r.ok else None
    except Exception as e:
        print(f"[Firebase Error] GET /{path}: {e}")
        return None

def fb_put(path, data):
    try:
        r = requests.put(fb_url(path), json=data, timeout=10)
        return r.ok
    except Exception as e:
        print(f"[Firebase Error] PUT /{path}: {e}")
        return False

def fb_patch(path, data):
    try:
        r = requests.patch(fb_url(path), json=data, timeout=10)
        return r.ok
    except Exception as e:
        print(f"[Firebase Error] PATCH /{path}: {e}")
        return False

def fb_delete(path):
    try:
        r = requests.delete(fb_url(path), timeout=10)
        return r.ok
    except Exception as e:
        print(f"[Firebase Error] DELETE /{path}: {e}")
        return False

total_uploaded_count = 0


# -------------------------------------------------------------
# HEARTBEAT & STATUS REPORTING
# -------------------------------------------------------------
def update_heartbeat(current_task="Idle - Monitoring channels & queue", is_busy=False):
    elapsed = int(time.time() - START_TIME)
    remaining = max(0, int(MAX_RUNTIME_SECONDS - elapsed))
    
    h = elapsed // 3600
    m = (elapsed % 3600) // 60
    s = elapsed % 60
    uptime_str = f"{h}h {m}m {s}s"
    
    rem_h = remaining // 3600
    rem_m = (remaining % 3600) // 60
    renew_in_str = f"{rem_h}h {rem_m}m"

    status_data = {
        "is_running": True,
        "last_heartbeat": time.time(),
        "last_heartbeat_iso": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_seconds": elapsed,
        "uptime_str": uptime_str,
        "remaining_seconds": remaining,
        "renew_in_str": renew_in_str,
        "is_busy": is_busy,
        "current_task": current_task,
        "total_uploaded_count": total_uploaded_count,
        "engine_host": "Kaggle Cloud (Google Infrastructure)"
    }
    fb_put("kaggle_status", status_data)


# -------------------------------------------------------------
# FFmpeg & VIDEO PROCESSING HELPERS
# -------------------------------------------------------------
def extract_video_info(video_path):
    """Extracts duration and dimensions using ffprobe."""
    duration = 15.0
    width = 1080
    height = 1920
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=width,height",
            "-of", "json", video_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            if "format" in data and "duration" in data["format"]:
                duration = float(data["format"]["duration"])
            if "streams" in data:
                for s in data["streams"]:
                    if s.get("width") and s.get("height"):
                        width = int(s["width"])
                        height = int(s["height"])
                        break
    except Exception as e:
        print(f"[FFprobe Notice] {e}")

    is_short = (height >= width)
    return {"duration": round(duration, 2), "width": width, "height": height, "is_short": is_short}


def enforce_storage_safeguard(video_path, output_dir, max_mb=470):
    """
    STRICT STORAGE SAFEGUARD (< 500MB):
    If file exceeds 470MB, dynamically compresses to 720p or 480p to fit under 500MB.
    """
    if not os.path.exists(video_path):
        return video_path

    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    if size_mb <= max_mb:
        return video_path

    print(f"⚠️ [Storage Safeguard] Video is {size_mb:.1f}MB (> {max_mb}MB)! Compressing with FFmpeg...")
    safe_path = os.path.join(output_dir, "compressed_safe.mp4")

    # Step 1: Compress to 720p with CRF 28
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", "scale='min(1280,iw)':-2",
        "-c:v", "libx264", "-crf", "28", "-preset", "faster",
        "-c:a", "aac", "-b:a", "128k",
        safe_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(safe_path) and (os.path.getsize(safe_path) / (1024 * 1024) > max_mb):
        # Step 2: Aggressive 480p compression if still over limit
        low_path = os.path.join(output_dir, "compressed_low.mp4")
        cmd_low = [
            "ffmpeg", "-y", "-i", safe_path,
            "-vf", "scale='min(854,iw)':-2",
            "-c:v", "libx264", "-crf", "32", "-preset", "faster",
            "-c:a", "aac", "-b:a", "96k",
            low_path
        ]
        subprocess.run(cmd_low, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(low_path) and os.path.getsize(low_path) > 0:
            os.remove(safe_path)
            safe_path = low_path

    if os.path.exists(safe_path) and os.path.getsize(safe_path) > 0:
        new_mb = os.path.getsize(safe_path) / (1024 * 1024)
        print(f"✅ [Storage Safeguard] Compressed down to {new_mb:.1f}MB (< 500MB)!")
        return safe_path

    return video_path


def generate_thumbnail(video_path, output_thumb_path):
    """Extracts a crisp frame from 1-second mark."""
    cmd = [
        "ffmpeg", "-y", "-ss", "00:00:01",
        "-i", video_path,
        "-vframes", "1", "-q:v", "2",
        output_thumb_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.exists(output_thumb_path) and os.path.getsize(output_thumb_path) > 0


# -------------------------------------------------------------
# FAST KAGGLE YOUTUBE DOWNLOADER
# -------------------------------------------------------------
def download_youtube_video(video_url, output_dir):
    """
    Downloads YouTube video in crisp 1080p using Kaggle's Google Cloud network.
    Zero bot detection and multi-gigabit speed!
    """
    os.makedirs(output_dir, exist_ok=True)
    outtmpl = os.path.join(output_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bv*[height<=1080]+ba/b[height<=1080]/bv*[height<=720]+ba/b[height<=720]/bv*+ba/b/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "writethumbnail": True,
        "concurrent_fragment_downloads": 4
    }

    # Load cookies if available
    if os.path.exists("cookies.txt") and os.path.getsize("cookies.txt") > 10:
        ydl_opts["cookiefile"] = "cookies.txt"

    meta = None
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        meta = ydl.extract_info(video_url, download=True)

    video_id = meta.get("id")
    title = meta.get("title", "YouTube Video")
    description = meta.get("description", "")
    
    # Locate downloaded mp4
    downloaded_video = os.path.join(output_dir, f"{video_id}.mp4")
    if not os.path.exists(downloaded_video):
        for f in os.listdir(output_dir):
            if f.startswith(video_id) and f.endswith((".mp4", ".mkv", ".webm")):
                downloaded_video = os.path.join(output_dir, f)
                break

    # Apply strict < 500MB safeguard
    final_video_path = enforce_storage_safeguard(downloaded_video, output_dir, max_mb=470)

    # Locate or generate thumbnail
    thumb_path = os.path.join(output_dir, f"{video_id}_thumb.jpg")
    native_thumb = None
    for ext in [".webp", ".jpg", ".png", ".jpeg"]:
        cand = os.path.join(output_dir, f"{video_id}{ext}")
        if os.path.exists(cand):
            native_thumb = cand
            break

    if native_thumb:
        cmd = ["ffmpeg", "-y", "-i", native_thumb, "-q:v", "2", thumb_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
        generate_thumbnail(final_video_path, thumb_path)

    v_info = extract_video_info(final_video_path)

    return {
        "video_id": video_id,
        "title": title,
        "description": description,
        "video_path": final_video_path,
        "thumb_path": thumb_path,
        "duration": v_info["duration"],
        "width": v_info["width"],
        "height": v_info["height"],
        "is_short": v_info["is_short"]
    }


# -------------------------------------------------------------
# BIDEO PUBLISHER
# -------------------------------------------------------------
def upload_to_bideo(token, video_path, thumb_path, title, description, category_id, is_short, meta):
    """Uploads video directly to Bideo API."""
    upload_type = "short" if is_short else "video"

    try:
        with open(video_path, "rb") as vf, open(thumb_path, "rb") as tf:
            files = {
                "video": (os.path.basename(video_path), vf, "video/mp4"),
                "thumbnail": ("thumbnail.jpg", tf, "image/jpeg")
            }
            data = {
                "title": title[:100],
                "description": description[:5000],
                "uploadType": upload_type,
                "duration": str(meta.get("duration", 15.0)),
                "width": str(meta.get("width", 1080)),
                "height": str(meta.get("height", 1920)),
                "visibility": "public"
            }
            if category_id:
                data["category"] = category_id

            auth_header = f"Bearer {token}" if not token.startswith("Bearer ") else token
            headers = {"Authorization": auth_header}

            r = requests.post(f"{BIDEO_API_BASE}/videos/upload", files=files, data=data, headers=headers, timeout=120)
            res_json = r.json()
            if r.ok and res_json.get("success"):
                return True, res_json.get("data", res_json), None
            return False, None, res_json.get("message", "Upload failed")
    except Exception as e:
        return False, None, str(e)


# -------------------------------------------------------------
# WORKER: PROCESS SINGLE UPLOAD QUEUE
# -------------------------------------------------------------
def process_single_upload_queue():
    """Checks Firebase /single_upload_queue for single YouTube URLs requested by user."""
    queue_data = fb_get("single_upload_queue") or {}
    if not queue_data:
        return

    for item_id, item in list(queue_data.items()):
        if not isinstance(item, dict) or item.get("status") != "pending":
            continue

        video_url = item.get("video_url")
        bideo_user_id = item.get("bideo_user_id")
        category_id = item.get("category_id")
        custom_title = item.get("title")
        custom_desc = item.get("description")

        print(f"\n⚡ [Single Upload Task] Processing {video_url} for user {bideo_user_id}...")
        update_heartbeat(f"Single Upload: {video_url}", is_busy=True)
        fb_patch(f"single_upload_queue/{item_id}", {"status": "processing", "started_at": datetime.now().isoformat()})

        # Fetch Bideo account token
        account = fb_get(f"accounts/{bideo_user_id}")
        if not account or not account.get("token"):
            fb_patch(f"single_upload_queue/{item_id}", {"status": "failed", "error": "Bideo account not logged in"})
            continue

        token = account["token"]

        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                dl = download_youtube_video(video_url, tmp_dir)
                final_title = custom_title or dl["title"]
                final_desc = custom_desc or dl["description"]

                success, bideo_res, err = upload_to_bideo(
                    token=token,
                    video_path=dl["video_path"],
                    thumb_path=dl["thumb_path"],
                    title=final_title,
                    description=final_desc,
                    category_id=category_id,
                    is_short=dl["is_short"],
                    meta={"duration": dl["duration"], "width": dl["width"], "height": dl["height"]}
                )

                if success:
                    global total_uploaded_count
                    total_uploaded_count += 1
                    bideo_vid_id = (bideo_res.get("_id") or bideo_res.get("id")) if isinstance(bideo_res, dict) else "ok"
                    fb_patch(f"single_upload_queue/{item_id}", {
                        "status": "completed",
                        "completed_at": datetime.now().isoformat(),
                        "bideo_video_id": bideo_vid_id,
                        "title": final_title
                    })
                    print(f"🎉 [Single Upload Success] '{final_title}' uploaded to Bideo!")
                else:
                    fb_patch(f"single_upload_queue/{item_id}", {"status": "failed", "error": err})
                    print(f"❌ [Single Upload Failed] {err}")
            except Exception as e:
                fb_patch(f"single_upload_queue/{item_id}", {"status": "failed", "error": str(e)})
                print(f"❌ [Single Upload Exception] {e}")


# -------------------------------------------------------------
# WORKER: PROCESS CHANNEL PAIRINGS
# -------------------------------------------------------------
def process_channel_pairings():
    """Checks all active YouTube -> Bideo pairings and syncs unposted videos."""
    pairings_data = fb_get("pairings") or {}
    if not pairings_data:
        return

    posted_videos = fb_get("posted_videos") or {}
    posted_ids = set(posted_videos.keys()) if isinstance(posted_videos, dict) else set()

    for p_id, pairing in list(pairings_data.items()):
        if not isinstance(pairing, dict) or not pairing.get("active", True):
            continue

        yt_input = pairing.get("yt_channel_input") or pairing.get("yt_channel_name")
        bideo_user_id = pairing.get("bideo_user_id")
        category_id = pairing.get("category_id")

        if not yt_input or not bideo_user_id:
            continue

        account = fb_get(f"accounts/{bideo_user_id}")
        if not account or not account.get("token"):
            continue

        token = account["token"]

        # Fetch latest videos from channel via yt-dlp flat extraction
        update_heartbeat(f"Scanning channel '{pairing.get('yt_channel_name', yt_input)}' for new videos")
        channel_url = yt_input if yt_input.startswith("http") else (f"https://www.youtube.com/{yt_input}" if yt_input.startswith("@") else f"https://www.youtube.com/@{yt_input}")

        ydl_opts = {
            "extract_flat": True,
            "playlistend": 20,
            "quiet": True,
            "ignoreerrors": True,
            "no_warnings": True
        }
        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"

        entries = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"{channel_url.rstrip('/')}/videos", download=False)
                if info and "entries" in info:
                    entries = [e for e in info["entries"] if e and e.get("id")]
        except Exception as e:
            # Fallback to search
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch10:{yt_input}", download=False)
                    if info and "entries" in info:
                        entries = [e for e in info["entries"] if e and e.get("id")]
            except Exception:
                pass

        # Filter unposted videos
        unposted = [e for e in entries if e.get("id") not in posted_ids]
        if not unposted:
            continue

        print(f"\n📺 [Channel Sync] Found {len(unposted)} unposted video(s) for '{pairing.get('yt_channel_name', yt_input)}'")

        for entry in unposted:
            vid_id = entry.get("id")
            vid_url = f"https://www.youtube.com/watch?v={vid_id}"
            vid_title = entry.get("title", "YouTube Video")

            print(f"📥 [Downloading Video] {vid_title} ({vid_id})...")
            update_heartbeat(f"Syncing: {vid_title}", is_busy=True)

            with tempfile.TemporaryDirectory() as tmp_dir:
                try:
                    dl = download_youtube_video(vid_url, tmp_dir)
                    success, b_res, err = upload_to_bideo(
                        token=token,
                        video_path=dl["video_path"],
                        thumb_path=dl["thumb_path"],
                        title=dl["title"],
                        description=dl["description"],
                        category_id=category_id,
                        is_short=dl["is_short"],
                        meta={"duration": dl["duration"], "width": dl["width"], "height": dl["height"]}
                    )

                    if success:
                        global total_uploaded_count
                        total_uploaded_count += 1
                        posted_ids.add(vid_id)
                        # Save to posted_videos in Firebase
                        fb_put(f"posted_videos/{vid_id}", {
                            "yt_id": vid_id,
                            "title": dl["title"],
                            "bideo_user_id": bideo_user_id,
                            "pairing_id": p_id,
                            "posted_at": datetime.now().isoformat()
                        })
                        # Update pairing count
                        current_count = pairing.get("published_count", 0) + 1
                        pairing["published_count"] = current_count
                        pairing["last_published_at"] = datetime.now().isoformat()
                        fb_patch(f"pairings/{p_id}", {
                            "published_count": current_count,
                            "last_published_at": datetime.now().isoformat()
                        })
                        print(f"🎉 [Sync Success] '{dl['title']}' published to Bideo!")
                    else:
                        print(f"❌ [Sync Upload Failed] {err}")
                except Exception as ex:
                    print(f"❌ [Sync Error] {ex}")

            # Brief pause between videos
            time.sleep(3)


# -------------------------------------------------------------
# MAIN 11.5-HOUR AUTONOMOUS LOOP
# -------------------------------------------------------------
print("\n🌟 [Kaggle Bideo Engine] Main Loop Active. Listening to Firebase...")

while True:
    elapsed = time.time() - START_TIME

    # Check 11.5 Hour Session Cutoff
    if elapsed >= MAX_RUNTIME_SECONDS:
        print("\n" + "=" * 65)
        print("🛑 [11.5 Hour Cutoff Reached] Gracefully closing current session.")
        print("🔄 Notifying Server to cancel and automatically launch the next session.")
        print("=" * 65)
        fb_put("kaggle_status", {
            "is_running": False,
            "state": "renew_ready",
            "last_heartbeat": time.time(),
            "reason": "11.5h runtime limit completed cleanly",
            "total_uploaded_count": total_uploaded_count
        })
        break

    try:
        # 1. Update live heartbeat
        update_heartbeat("Monitoring Channels & Upload Queue", is_busy=False)

        # 2. Check and process any single upload requests from dashboard
        process_single_upload_queue()

        # 3. Check and process any new channel pairing videos
        process_channel_pairings()

    except Exception as loop_err:
        print(f"[Loop Notice] {loop_err}")

    # Sleep 20 seconds between monitoring cycles
    time.sleep(20)

print("🏁 Kaggle Bideo Engine session ended cleanly.")
