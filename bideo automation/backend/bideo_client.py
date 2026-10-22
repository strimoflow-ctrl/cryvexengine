import os
import requests

BIDEO_API_BASE = "https://bideo.in/api"


class BideoClient:
    """Official Bideo API Client"""

    @staticmethod
    def login(phone_or_login, password):
        """
        Login with phone number/username and password.
        Returns (success, token, user_data, error_message)
        """
        clean_val = phone_or_login.strip()
        payload = {
            "phone": clean_val,
            "login": clean_val,
            "username": clean_val,
            "password": password
        }

        try:
            r = requests.post(
                f"{BIDEO_API_BASE}/auth/login",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            data = r.json()
            if r.ok and data.get("success"):
                return True, data.get("token"), data.get("user"), None
            return False, None, None, data.get("message", "Login failed")
        except Exception as e:
            return False, None, None, f"Connection error: {str(e)}"

    @staticmethod
    def get_categories():
        """Fetch all video categories from Bideo."""
        try:
            r = requests.get(f"{BIDEO_API_BASE}/categories", timeout=10)
            data = r.json()
            cats = data.get("data", data) if isinstance(data, dict) else data
            return cats if isinstance(cats, list) else []
        except Exception as e:
            print(f"[Bideo Warning] get_categories error: {e}")
            return []

    @staticmethod
    def get_user_profile(token):
        """Fetch current user profile data."""
        try:
            r = requests.get(
                f"{BIDEO_API_BASE}/users/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            if r.ok:
                return r.json().get("data", r.json())
            return None
        except Exception:
            return None

    @staticmethod
    def upload_video(token, video_path, thumb_path, title, description, category_id, is_short, meta=None):
        """
        Uploads video directly to user's channel via POST /api/videos/upload.
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

        # Read files for multipart upload
        try:
            with open(video_path, "rb") as vf, open(thumb_path, "rb") as tf:
                filename = os.path.basename(video_path)
                files = {
                    "video": (filename, vf, "video/mp4"),
                    "thumbnail": ("thumbnail.jpg", tf, "image/jpeg")
                }

                data = {
                    "title": title[:100],  # Max title length safeguard
                    "description": description[:5000],
                    "uploadType": upload_type,
                    "duration": str(duration),
                    "width": str(width),
                    "height": str(height),
                    "visibility": "public"
                }

                if category_id:
                    data["category"] = category_id

                headers = {
                    "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token
                }

                r = requests.post(
                    f"{BIDEO_API_BASE}/videos/upload",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=300  # 5 min timeout for large file uploads
                )

                resp_data = r.json()
                if r.ok and resp_data.get("success", True):
                    return True, resp_data.get("data", resp_data), None
                return False, None, resp_data.get("message", "Upload failed on Bideo server")

        except requests.exceptions.Timeout:
            return False, None, "Upload request timed out on Bideo server"
        except Exception as e:
            return False, None, f"Upload error: {str(e)}"
