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
