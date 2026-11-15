import os
import requests

BIDEO_API_BASE = "https://bideo.in/api"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

FALLBACK_CATEGORIES = [
    {"_id": "6a2f13458b8b9c8e631b188a", "name": "Comedy", "slug": "comedy", "videosCount": 39148},
    {"_id": "6a7c8fbab377a28c2a051a7e", "name": "Education", "slug": "education-", "videosCount": 5000},
    {"_id": "6a1c0373fc86d90963e20ae8", "name": "Entertainment", "slug": "entertainment", "videosCount": 20000},
    {"_id": "6a12f4d6c69d0eddde28b4ad", "name": "Food", "slug": "food", "videosCount": 4500},
    {"_id": "6a1c03a2fc86d90963e20ae9", "name": "Gaming", "slug": "gaming", "videosCount": 12000},
    {"_id": "6ab55282bbaabc57e22b9f62", "name": "Health & Fitness", "slug": "health-&-fitness", "videosCount": 3500},
    {"_id": "6a1c03e5fc86d90963e20aea", "name": "Music", "slug": "music", "videosCount": 18000},
    {"_id": "6a08764d700dc1864041ac6c", "name": "News", "slug": "news", "videosCount": 6000},
    {"_id": "6ab5528ebbaabc57e22ba002", "name": "Sports", "slug": "sports", "videosCount": 8500},
    {"_id": "6a1c036cfc86d90963e20ae7", "name": "Tech", "slug": "tech", "videosCount": 15000},
    {"_id": "6a1c0364fc86d90963e20ae6", "name": "Vlogs", "slug": "vlogs", "videosCount": 14000}
]


class BideoClient:
    """Official Bideo API Client with Session Validation and Auto-Recovery"""

    @staticmethod
    def login(phone_or_login, password):
        """
        Login with phone number/username and password.
        Returns (success, token, user_data, error_message)
        """
        clean_val = str(phone_or_login).strip()
        payload = {
            "phone": clean_val,
            "login": clean_val,
            "username": clean_val,
            "password": password
        }

        headers = {**DEFAULT_HEADERS, "Content-Type": "application/json"}

        try:
            r = requests.post(
                f"{BIDEO_API_BASE}/auth/login",
                json=payload,
                headers=headers,
                timeout=15
            )
            data = r.json()
            if r.ok and data.get("success"):
                return True, data.get("token"), data.get("user"), None
            return False, None, None, data.get("message", "Login failed")
        except Exception as e:
            return False, None, None, f"Connection error: {str(e)}"

    _cached_categories = None

    @classmethod
    def get_categories(cls):
        """Fetch all video categories from Bideo with cache and instant fallback."""
        if cls._cached_categories:
            return cls._cached_categories
        try:
            r = requests.get(f"{BIDEO_API_BASE}/categories", headers=DEFAULT_HEADERS, timeout=3)
            if r.ok:
                data = r.json()
                cats = data.get("data", data) if isinstance(data, dict) else data
                if isinstance(cats, dict) and "categories" in cats:
                    cats = cats["categories"]
                if isinstance(cats, list) and len(cats) > 0:
                    cls._cached_categories = cats
                    return cats
        except Exception as e:
            print(f"[Bideo Warning] get_categories live fetch failed: {e}. Using fallback.")
        cls._cached_categories = list(FALLBACK_CATEGORIES)
        return cls._cached_categories

    @staticmethod
    def get_user_profile(token):
        """
        Fetch current user profile data via /api/auth/me.
        Returns profile dict if token is active/valid, otherwise None.
        """
        if not token:
            return None
        clean_tok = token.replace("Bearer ", "").strip()
        headers = {**DEFAULT_HEADERS, "Authorization": f"Bearer {clean_tok}"}
        try:
            r = requests.get(
                f"{BIDEO_API_BASE}/auth/me",
                headers=headers,
                timeout=10
            )
            if r.ok:
                res_data = r.json()
                return res_data.get("data", res_data)
            return None
        except Exception:
            return None

    @staticmethod
    def upload_video(token, video_path, thumb_path, title, description, category_id, is_short, meta=None, phone=None, password=None):
        """
        Uploads video directly to user's channel via POST /api/videos/upload.
        Includes session validation and automatic relogin recovery if token expires.
        Returns (success, video_data, error_message)
        """
        if not os.path.exists(video_path):
            return False, None, "Video file not found"
        if not os.path.exists(thumb_path):
            return False, None, "Thumbnail file not found"

        meta = meta or {}
        duration = meta.get("duration", 10.0)
        width = meta.get("width", 1080)
        height = meta.get("height", 1920)

        upload_type = "short" if is_short else "video"

        # Verify token before opening heavy file
        current_token = token.replace("Bearer ", "").strip() if token else ""
        profile = BideoClient.get_user_profile(current_token)
        if not profile and phone and password:
            print(f"[BideoClient] Session expired for {phone}. Re-authenticating...")
            ok, new_tok, _, _ = BideoClient.login(phone, password)
            if ok and new_tok:
                current_token = new_tok
                print(f"[BideoClient] Fresh session recovered successfully!")

        try:
            with open(video_path, "rb") as vf, open(thumb_path, "rb") as tf:
                filename = os.path.basename(video_path)
                files = {
                    "video": (filename, vf, "video/mp4"),
                    "thumbnail": ("thumbnail.jpg", tf, "image/jpeg")
                }

                data = {
                    "title": (title or "Video")[:100],
                    "description": (description or "")[:900],
                    "uploadType": upload_type,
                    "duration": str(duration),
                    "width": str(width),
                    "height": str(height),
                    "visibility": "public"
                }

                if category_id:
                    data["category"] = category_id

                headers = {
                    **DEFAULT_HEADERS,
                    "Authorization": f"Bearer {current_token}"
                }

                r = requests.post(
                    f"{BIDEO_API_BASE}/videos/upload",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=300
                )

                try:
                    resp_data = r.json()
                except Exception:
                    if r.status_code == 413:
                        return False, None, "File too large for Bideo server (HTTP 413 Payload Too Large)"
                    return False, None, f"Server HTTP {r.status_code}: {r.text[:100]}"

                # If token expired during upload and we have creds, retry once
                if r.status_code in [401, 403] and phone and password:
                    print(f"[BideoClient] Upload returned {r.status_code}. Retrying with fresh login...")
                    ok, fresh_tok, _, _ = BideoClient.login(phone, password)
                    if ok and fresh_tok:
                        vf.seek(0)
                        tf.seek(0)
                        headers["Authorization"] = f"Bearer {fresh_tok}"
                        r2 = requests.post(
                            f"{BIDEO_API_BASE}/videos/upload",
                            headers=headers,
                            files=files,
                            data=data,
                            timeout=300
                        )
                        try:
                            resp_data = r2.json()
                            if r2.ok and resp_data.get("success", True):
                                return True, resp_data.get("data", resp_data), None
                        except Exception:
                            pass

                if r.ok and resp_data.get("success", True):
                    return True, resp_data.get("data", resp_data), None
                return False, None, resp_data.get("message", "Upload failed on Bideo server")

        except requests.exceptions.Timeout:
            return False, None, "Upload request timed out on Bideo server"
        except Exception as e:
            return False, None, f"Upload error: {str(e)}"
