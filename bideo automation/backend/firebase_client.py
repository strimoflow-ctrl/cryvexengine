import os
import requests
from datetime import datetime

FIREBASE_DB_URL = os.environ.get(
    "FIREBASE_DB_URL",
    "https://secret-gpt-default-rtdb.asia-southeast1.firebasedatabase.app"
).rstrip("/")

BASE_NODE = f"{FIREBASE_DB_URL}/bideo_automation"


class FirebaseClient:
    """
    Firebase Realtime Database REST Client for state persistence and duplicate prevention.
    Stores data under /bideo_automation/
    """

    @staticmethod
    def _url(path):
        return f"{BASE_NODE}/{path.strip('/')}.json"

    # -------------------------------------------------------------
    # Bideo Accounts Management
    # -------------------------------------------------------------
    @classmethod
    def save_account(cls, user_data, token, phone):
        """Save or update logged-in Bideo account."""
        user_id = user_data.get("_id") or user_data.get("id")
        if not user_id:
            return False

        record = {
            "_id": user_id,
            "name": user_data.get("name", "Channel"),
            "avatar": user_data.get("avatar", ""),
            "channelName": user_data.get("channelName", ""),
            "followersCount": user_data.get("followersCount", 0),
            "phone": phone,
            "token": token,
            "updatedAt": datetime.utcnow().isoformat()
        }

        try:
            r = requests.put(cls._url(f"accounts/{user_id}"), json=record, timeout=8)
            return r.ok
        except Exception as e:
            print(f"[Firebase Warning] save_account error: {e}")
            return False

    @classmethod
    def get_accounts(cls):
        """Fetch all saved Bideo accounts."""
        try:
            r = requests.get(cls._url("accounts"), timeout=8)
            data = r.json()
            if isinstance(data, dict):
                return list(data.values())
            return []
        except Exception as e:
            print(f"[Firebase Warning] get_accounts error: {e}")
            return []

    @classmethod
    def get_account_by_id(cls, user_id):
        try:
            r = requests.get(cls._url(f"accounts/{user_id}"), timeout=8)
            return r.json()
        except Exception:
            return None

    # -------------------------------------------------------------
    # Channel Pairings (YouTube Channel <---> Bideo Account)
    # -------------------------------------------------------------
    @classmethod
    def save_pairing(cls, pairing_id, pairing_data):
        try:
            r = requests.put(cls._url(f"pairings/{pairing_id}"), json=pairing_data, timeout=8)
            return r.ok
        except Exception as e:
            print(f"[Firebase Warning] save_pairing error: {e}")
            return False

    @classmethod
    def get_pairings(cls):
        try:
            r = requests.get(cls._url("pairings"), timeout=8)
            data = r.json()
            if isinstance(data, dict):
                return list(data.values())
            return []
        except Exception as e:
            print(f"[Firebase Warning] get_pairings error: {e}")
            return []

    @classmethod
    def delete_pairing(cls, pairing_id):
        try:
            r = requests.delete(cls._url(f"pairings/{pairing_id}"), timeout=8)
            return r.ok
        except Exception as e:
            print(f"[Firebase Warning] delete_pairing error: {e}")
            return False

    @classmethod
    def update_pairing(cls, pairing_id, updates):
        try:
            r = requests.patch(cls._url(f"pairings/{pairing_id}"), json=updates, timeout=8)
            return r.ok
        except Exception as e:
            print(f"[Firebase Warning] update_pairing error: {e}")
            return False

    # -------------------------------------------------------------
    # Posted Videos Tracker (Duplicate Prevention)
    # -------------------------------------------------------------
    @classmethod
    def is_video_posted(cls, yt_video_id):
        """Check if YouTube video has already been posted to Bideo."""
        if not yt_video_id:
            return True
        try:
            r = requests.get(cls._url(f"posted_videos/{yt_video_id}"), timeout=8)
            return r.json() is not None
        except Exception as e:
            print(f"[Firebase Warning] is_video_posted error: {e}")
            return False

    @classmethod
    def mark_video_posted(cls, yt_video_id, record):
        """Record video as posted to prevent ever re-uploading."""
        try:
            record["postedAt"] = datetime.utcnow().isoformat()
            r = requests.put(cls._url(f"posted_videos/{yt_video_id}"), json=record, timeout=8)
            return r.ok
        except Exception as e:
            print(f"[Firebase Warning] mark_video_posted error: {e}")
            return False

    @classmethod
    def get_posted_videos(cls):
        """Fetch all posted videos dictionary from Firebase."""
        try:
            r = requests.get(cls._url("posted_videos"), timeout=8)
            data = r.json()
            if isinstance(data, dict):
                return data
            return {}
        except Exception:
            return {}

    # -------------------------------------------------------------
    # Automation Activity Logs (STRICTLY LOCAL SERVER MEMORY - ZERO FIREBASE CHARGES)
    # -------------------------------------------------------------
    _local_logs = []

    @classmethod
    def add_log(cls, title, message, status="success", meta=None):
        """Stores logs in local server memory only to prevent any Firebase RTDB charges."""
        try:
            log_id = f"log_{int(datetime.utcnow().timestamp() * 1000)}"
            entry = {
                "id": log_id,
                "title": title,
                "message": message,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "meta": meta or {}
            }
            cls._local_logs.insert(0, entry)
            if len(cls._local_logs) > 80:
                cls._local_logs.pop()
        except Exception:
            pass

    @classmethod
    def get_logs(cls, limit=30):
        """Returns logs from local server memory."""
        return cls._local_logs[:limit]

    @classmethod
    def purge_firebase_logs(cls):
        """Deletes any past logs from Firebase to completely free up database space."""
        try:
            requests.delete(cls._url("logs"), timeout=5)
        except Exception:
            pass

    # -------------------------------------------------------------
    # Channel & Video Library Catalog (Persistent Storage)
    # -------------------------------------------------------------
    @classmethod
    def get_channel_slug(cls, channel_url, channel_name):
        """Generates a clean, unique slug for channel identification."""
        raw = channel_url or channel_name or "default_channel"
        # Extract handle or channel id if possible
        if "@" in raw:
            handle = raw.split("@")[-1].split("/")[0].strip()
            slug = "".join(c for c in handle if c.isalnum() or c in "_-")
            if slug:
                return f"ch_{slug.lower()}"
        slug = "".join(c for c in raw.lower() if c.isalnum() or c in "_-")[:30]
        return f"ch_{slug}" if slug else "ch_main"

    @classmethod
    def save_channel_and_videos(cls, channel_meta, new_videos):
        """
        Saves channel info and updates its video catalog in Firebase.
        Preserves existing 'uploaded' state so previously posted videos are never overwritten.
        """
        ch_url = channel_meta.get("channel_url", "")
        ch_name = channel_meta.get("channel_name", "")
        ch_id = cls.get_channel_slug(ch_url, ch_name)

        # 1. Fetch existing channel data & posted_videos to preserve upload flags
        existing_videos = {}
        try:
            r = requests.get(cls._url(f"channels/{ch_id}/videos"), timeout=8)
            existing_videos = r.json() or {}
        except Exception:
            existing_videos = {}

        posted_videos = cls.get_posted_videos()

        # 2. Merge new videos into catalog
        videos_map = dict(existing_videos) if isinstance(existing_videos, dict) else {}
        for v in new_videos:
            vid_id = v.get("id")
            if not vid_id:
                continue

            prev = videos_map.get(vid_id) or {}
            is_posted = prev.get("uploaded", False) or (vid_id in posted_videos)

            videos_map[vid_id] = {
                "id": vid_id,
                "title": v.get("title", "YouTube Video"),
                "url": v.get("url") or f"https://www.youtube.com/watch?v={vid_id}",
                "thumbnail": v.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                "duration": v.get("duration", 0),
                "is_short": v.get("is_short", False),
                "channel_id": ch_id,
                "channel_name": ch_name,
                "uploaded": is_posted,
                "bideo_video_id": prev.get("bideo_video_id") or (posted_videos.get(vid_id, {}).get("bideo_video_id") if isinstance(posted_videos.get(vid_id), dict) else None),
                "uploaded_at": prev.get("uploaded_at") or (posted_videos.get(vid_id, {}).get("postedAt") if isinstance(posted_videos.get(vid_id), dict) else None)
            }

        total_vids = len(videos_map)
        uploaded_count = sum(1 for v in videos_map.values() if v.get("uploaded"))

        ch_data = {
            "id": ch_id,
            "channel_name": ch_name,
            "channel_url": ch_url,
            "total_videos": total_vids,
            "uploaded_count": uploaded_count,
            "last_fetched": datetime.utcnow().isoformat()
        }

        try:
            # Save channel meta
            requests.patch(cls._url(f"channels/{ch_id}"), json=ch_data, timeout=8)
            # Save videos map
            requests.put(cls._url(f"channels/{ch_id}/videos"), json=videos_map, timeout=12)
            ch_data["videos"] = list(videos_map.values())
            return ch_data
        except Exception as e:
            print(f"[Firebase Warning] save_channel_and_videos error: {e}")
            ch_data["videos"] = list(videos_map.values())
            return ch_data

    @classmethod
    def get_all_channels(cls):
        """Fetches all stored YouTube channels from Firebase."""
        try:
            r = requests.get(cls._url("channels"), timeout=8)
            data = r.json()
            if not isinstance(data, dict):
                return []
            channels = []
            for ch_id, ch in data.items():
                if not isinstance(ch, dict):
                    continue
                vids = ch.get("videos") or {}
                if isinstance(vids, dict):
                    total = len(vids)
                    uploaded = sum(1 for v in vids.values() if isinstance(v, dict) and v.get("uploaded"))
                else:
                    total = ch.get("total_videos", 0)
                    uploaded = ch.get("uploaded_count", 0)
                channels.append({
                    "id": ch_id,
                    "channel_name": ch.get("channel_name", "YouTube Channel"),
                    "channel_url": ch.get("channel_url", ""),
                    "total_videos": total,
                    "uploaded_count": uploaded,
                    "last_fetched": ch.get("last_fetched", "")
                })
            return channels
        except Exception as e:
            print(f"[Firebase Warning] get_all_channels error: {e}")
            return []

    @classmethod
    def get_channel_videos(cls, ch_id):
        """Fetches all stored videos for a given channel, synced with posted_videos."""
        try:
            r = requests.get(cls._url(f"channels/{ch_id}/videos"), timeout=8)
            v_dict = r.json() or {}
            if not isinstance(v_dict, dict):
                return []

            posted_videos = cls.get_posted_videos()
            video_list = []
            for vid_id, v in v_dict.items():
                if not isinstance(v, dict):
                    continue
                is_uploaded = v.get("uploaded", False) or (vid_id in posted_videos)
                v["uploaded"] = is_uploaded
                if not v.get("bideo_video_id") and isinstance(posted_videos.get(vid_id), dict):
                    v["bideo_video_id"] = posted_videos[vid_id].get("bideo_video_id")
                video_list.append(v)

            return video_list
        except Exception as e:
            print(f"[Firebase Warning] get_channel_videos error: {e}")
            return []

    @classmethod
    def mark_video_uploaded_in_channel(cls, ch_id, vid_id, bideo_video_id, title=""):
        """Marks video as uploaded both in channel and posted_videos tracker."""
        now_iso = datetime.utcnow().isoformat()
        # 1. Update posted_videos
        cls.mark_video_posted(vid_id, {
            "yt_video_id": vid_id,
            "title": title,
            "bideo_video_id": bideo_video_id,
            "postedAt": now_iso
        })
        # 2. Update channels/{ch_id}/videos/{vid_id}
        if ch_id:
            try:
                requests.patch(cls._url(f"channels/{ch_id}/videos/{vid_id}"), json={
                    "uploaded": True,
                    "bideo_video_id": bideo_video_id,
                    "uploaded_at": now_iso
                }, timeout=5)
            except Exception:
                pass

    # -------------------------------------------------------------
    # Active Batch Queue Management
    # -------------------------------------------------------------
    @classmethod
    def save_active_batch(cls, batch_data):
        """Saves current active video batch to Firebase."""
        try:
            r = requests.put(cls._url("active_batch"), json=batch_data, timeout=8)
            return r.ok
        except Exception as e:
            print(f"[Firebase Warning] save_active_batch error: {e}")
            return False

    @classmethod
    def get_active_batch(cls):
        """Fetches active video batch from Firebase."""
        try:
            r = requests.get(cls._url("active_batch"), timeout=8)
            return r.json() or {}
        except Exception:
            return {}

    @classmethod
    def clear_active_batch(cls):
        """Cancels or removes active batch from Firebase."""
        try:
            requests.delete(cls._url("active_batch"), timeout=5)
            return True
        except Exception:
            return False

