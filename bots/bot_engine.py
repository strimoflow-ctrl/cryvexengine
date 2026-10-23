import os
import sys
import time
import math
import threading
import random
import string
import requests
from datetime import datetime

# Windows console encoding fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BIDEO_API_BASE = "https://bideo.in/api"
FIREBASE_DB_URL = os.environ.get(
    "FIREBASE_DB_URL",
    "https://secret-gpt-default-rtdb.asia-southeast1.firebasedatabase.app"
).rstrip("/")
BASE_NODE = f"{FIREBASE_DB_URL}/bideo_automation"

# Dedicated default channel for the user
DEFAULT_CRYVEX_CHANNEL_ID = "6ada0b9dfb39968c7c48dd7b"
DEFAULT_CRYVEX_USERNAME = "cryvex"

NAME_PREFIXES = [
    "creator", "alex", "rohit", "vikram", "sam", "aryan", "kavya",
    "rahul", "neha", "deepak", "aditi", "manish", "priya", "varun",
    "sneha", "amit", "divya", "kunal", "pooja", "yash", "ananya"
]

NAME_TAGS = [
    "vlogs", "shorts", "daily", "zone", "beats", "clips", "reels",
    "official", "hub", "media", "live", "vibes", "star", "pro"
]


class BotEngine:
    """
    Bideo Bot & Growth Engine:
    - 1-Click Instant Account Generation (No OTP required)
    - Full details vault (Phone, Username, Password, Token)
    - Channel Search and Resolution (Default: cryvex)
    - Controllable Follow Booster (Exact quantity control, No duplicates, Never deletes bots)
    - Controllable Video Booster (Exact Views, Watch-Time, Likes)
    - Video Management Pipeline (Fetch all cryvex videos, view review status, bulk boost)
    - Coin Farming & Home Feed Highlight Pinning
    """

    @staticmethod
    def _firebase_url(path):
        return f"{BASE_NODE}/{path.strip('/')}.json"

    @classmethod
    def get_cryvex_token(cls):
        """Fetches Cryvex account token from Firebase."""
        try:
            r = requests.get(cls._firebase_url(f"accounts/{DEFAULT_CRYVEX_CHANNEL_ID}"), timeout=6)
            if r.ok and r.json():
                return r.json().get("token")
            return None
        except Exception:
            return None

    # ---------------------------------------------------------
    # Account Generation Logic
    # ---------------------------------------------------------
    @classmethod
    def generate_random_credentials(cls):
        """Generates realistic phone, username, and password."""
        prefix = random.choice(["6", "7", "8", "9"])
        phone = prefix + "".join(random.choices(string.digits, k=9))

        p1 = random.choice(NAME_PREFIXES)
        p2 = random.choice(NAME_TAGS)
        num = random.randint(10, 999)
        username = f"{p1}_{p2}_{num}"

        pwd_digits = "".join(random.choices(string.digits, k=4))
        password = f"BideoPass@{pwd_digits}"

        return phone, username, password

    @classmethod
    def create_single_bot(cls, custom_name=None, import_to_uploader=True):
        """
        Creates a new verified Bideo account on the official server in 1 click (No OTP).
        """
        phone, username, password = cls.generate_random_credentials()
        if custom_name:
            clean = "".join(c for c in custom_name if c.isalnum() or c in "._")
            if len(clean) >= 3:
                username = clean

        payload = {
            "name": username,
            "phone": phone,
            "password": password
        }

        try:
            r = requests.post(f"{BIDEO_API_BASE}/auth/signup", json=payload, timeout=12)
            data = r.json()

            if not r.ok or not data.get("success"):
                err = data.get("message", "Signup failed on Bideo server")
                return False, None, err

            token = data.get("token")
            user_info = data.get("user") or {}
            user_id = user_info.get("_id") or user_info.get("id")

            bot_record = {
                "_id": user_id,
                "name": username,
                "phone": phone,
                "password": password,
                "token": token,
                "avatar": user_info.get("avatar") or f"https://api.dicebear.com/9.x/initials/svg?seed={username}",
                "channelName": user_info.get("channelName", username),
                "created_at": datetime.utcnow().isoformat(),
                "followers_count": 0,
                "following_count": 0
            }

            # Save in Firebase under /bideo_automation/bots/{id}
            requests.put(cls._firebase_url(f"bots/{user_id}"), json=bot_record, timeout=8)

            if import_to_uploader:
                account_record = {
                    "_id": user_id,
                    "name": username,
                    "avatar": bot_record["avatar"],
                    "channelName": username,
                    "followersCount": 0,
                    "phone": phone,
                    "token": token,
                    "is_bot": True,
                    "updatedAt": datetime.utcnow().isoformat()
                }
                requests.put(cls._firebase_url(f"accounts/{user_id}"), json=account_record, timeout=8)

            log_id = f"log_{int(datetime.utcnow().timestamp() * 1000)}"
            requests.put(cls._firebase_url(f"logs/{log_id}"), json={
                "id": log_id,
                "title": "Bot Account Created",
                "message": f"New account '{username}' created successfully without OTP!",
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }, timeout=5)

            return True, bot_record, None

        except requests.exceptions.Timeout:
            return False, None, "Server timed out while creating account"
        except Exception as e:
            return False, None, f"Network error: {str(e)}"

    @classmethod
    def bulk_create_bots(cls, count=5, import_to_uploader=True):
        """Create multiple bot accounts in batch."""
        results = []
        for _ in range(count):
            ok, bot, err = cls.create_single_bot(import_to_uploader=import_to_uploader)
            if ok:
                results.append(bot)
            time.sleep(0.4)
        return results

    @classmethod
    def get_all_bots(cls):
        """Fetch all bot accounts from Firebase."""
        try:
            r = requests.get(cls._firebase_url("bots"), timeout=8)
            data = r.json()
            if isinstance(data, dict):
                bots = list(data.values())
                bots.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                return bots
            return []
        except Exception as e:
            print(f"[BotEngine Warning] get_all_bots error: {e}")
            return []

    @classmethod
    def delete_bot(cls, bot_id):
        """Delete bot record from Firebase."""
        try:
            requests.delete(cls._firebase_url(f"bots/{bot_id}"), timeout=8)
            requests.delete(cls._firebase_url(f"accounts/{bot_id}"), timeout=8)
            return True
        except Exception:
            return False

    # ---------------------------------------------------------
    # Channel Discovery & Resolution
    # ---------------------------------------------------------
    @classmethod
    def search_channels(cls, query, sample_token=None):
        """Search Bideo channels by name or handle."""
        headers = {}
        if sample_token:
            headers["Authorization"] = f"Bearer {sample_token}"
        else:
            bots = cls.get_all_bots()
            if bots and bots[0].get("token"):
                headers["Authorization"] = f"Bearer {bots[0]['token']}"

        try:
            r = requests.get(f"{BIDEO_API_BASE}/users/search", params={"q": query}, headers=headers, timeout=10)
            data = r.json()
            if r.ok and data.get("success"):
                return data.get("data", [])
            return []
        except Exception as e:
            print(f"[Search Error] {e}")
            return []

    @classmethod
    def resolve_channel_id(cls, target_input=None):
        """
        Intelligently resolves input to actual Bideo Channel ID.
        Defaults to cryvex channel if empty.
        """
        if not target_input or not str(target_input).strip():
            return DEFAULT_CRYVEX_CHANNEL_ID, DEFAULT_CRYVEX_USERNAME

        raw = str(target_input).strip()
        clean = raw.rstrip("/").split("/")[-1].split("?")[0]
        if clean.startswith("@"):
            clean = clean[1:]

        if clean.lower() == "cryvex":
            return DEFAULT_CRYVEX_CHANNEL_ID, "cryvex"

        # Check if 24-hex ObjectId
        if len(clean) == 24 and all(c in "0123456789abcdefABCDEF" for c in clean):
            return clean, clean

        # Search Bideo API
        results = cls.search_channels(clean)
        if results:
            for ch in results:
                name_match = (ch.get("name") or "").lower() == clean.lower()
                handle_match = (ch.get("channelName") or "").lower() == clean.lower()
                if name_match or handle_match:
                    return ch.get("_id"), ch.get("name") or ch.get("channelName") or clean
            top = results[0]
            return top.get("_id"), top.get("name") or top.get("channelName") or clean

        return clean, clean

    # ---------------------------------------------------------
    # Video Management & Pipeline
    # ---------------------------------------------------------
    @classmethod
    def get_channel_videos(cls, channel_id=None):
        """
        Fetches all uploaded videos of a channel.
        Maps the monetization review status (Passed vs In Review) onto each video.
        """
        target_id, name = cls.resolve_channel_id(channel_id)
        url = f"{BIDEO_API_BASE}/videos?owner={target_id}"

        try:
            r = requests.get(url, timeout=10)
            if r.ok:
                data = r.json().get("data", [])

                # Map monetization review status (Pass via Ads / In Review)
                cryvex_token = cls.get_cryvex_token()
                review_map = {}
                if cryvex_token:
                    try:
                        r_mon = requests.get(
                            f"{BIDEO_API_BASE}/users/monetization/status",
                            headers={"Authorization": f"Bearer {cryvex_token}"},
                            timeout=6
                        )
                        if r_mon.ok:
                            reviews = r_mon.json().get("data", {}).get("reviews", [])
                            for rev in reviews:
                                vid = (rev.get("video") or {}).get("_id")
                                if vid:
                                    review_map[vid] = {
                                        "reviewId": rev.get("_id"),
                                        "status": rev.get("status", "pending"),
                                        "adsWatched": rev.get("adsWatched", 0),
                                        "adsRequired": rev.get("adsRequired", 4),
                                        "passedVia": rev.get("passedVia")
                                    }
                    except Exception:
                        pass

                for v in data:
                    vid = v.get("_id")
                    if vid in review_map:
                        v["reviewId"] = review_map[vid]["reviewId"]
                        v["reviewStatus"] = review_map[vid]["status"]
                        v["adsWatched"] = review_map[vid]["adsWatched"]
                        v["adsRequired"] = review_map[vid]["adsRequired"]
                        v["passedVia"] = review_map[vid]["passedVia"]
                    else:
                        v["reviewId"] = None
                        v["reviewStatus"] = "passed" if v.get("isApproved") else "pending"
                        v["adsWatched"] = 0
                        v["adsRequired"] = 4

                return {
                    "success": True,
                    "channel_id": target_id,
                    "channel_name": name,
                    "count": len(data),
                    "videos": data
                }
            return {"success": False, "channel_id": target_id, "count": 0, "videos": []}
        except Exception as e:
            return {"success": False, "message": str(e), "videos": []}

    # ---------------------------------------------------------
    # Cryvex Coins & Boost System
    # ---------------------------------------------------------
    @classmethod
    def get_cryvex_coins_status(cls):
        """Fetches live coins and daily ad limits for Cryvex."""
        token = cls.get_cryvex_token()
        if not token:
            return {"success": False, "message": "Cryvex account token not found in Firebase"}
        headers = {"Authorization": f"Bearer {token}"}
        try:
            r = requests.get(f"{BIDEO_API_BASE}/boost/status", headers=headers, timeout=8)
            if r.ok:
                d = r.json().get("data", {})
                return {
                    "success": True,
                    "coins": d.get("coins", 0),
                    "dailyAds": d.get("dailyAds", {}),
                    "boostTiers": d.get("boostTiers", []),
                    "activeHighlights": d.get("globalQueue", {}).get("activeHighlights", [])
                }
            return {"success": False, "message": "Failed to fetch boost status"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @classmethod
    def claim_cryvex_ad_coins(cls):
        """Claims free ad reward coins directly on Cryvex's account."""
        token = cls.get_cryvex_token()
        if not token:
            return {"success": False, "message": "Cryvex account token not found"}
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        try:
            r = requests.post(f"{BIDEO_API_BASE}/boost/claim-ad-reward", headers=headers, json={}, timeout=8)
            data = r.json()
            if r.ok and data.get("success"):
                d = data.get("data", {})
                return {
                    "success": True,
                    "message": f"🎉 Successfully claimed free coins! New Balance: {d.get('totalCoins')} coins",
                    "totalCoins": d.get("totalCoins"),
                    "coinsEarned": d.get("coinsEarned"),
                    "dailyWatched": d.get("dailyWatched"),
                    "remainingDaily": d.get("remainingDaily"),
                    "sessionCount": d.get("sessionCount"),
                    "cooldownSeconds": d.get("cooldownSeconds", 0)
                }
            msg = data.get("message", "Cooldown active or ad claim failed.")
            return {"success": False, "message": msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @classmethod
    def pass_video_review(cls, review_id=None, video_id=None):
        """
        Bypasses the 4 rewarded ads required to pass monetization review.
        Calls POST /api/users/monetization/watch-review-ad/{review_id} until passed.
        """
        token = cls.get_cryvex_token()
        if not token:
            return {"success": False, "message": "Cryvex token not found"}

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # If only video_id is provided, resolve review_id
        actual_rev_id = review_id
        if not actual_rev_id and video_id:
            try:
                r_mon = requests.get(f"{BIDEO_API_BASE}/users/monetization/status", headers=headers, timeout=6)
                if r_mon.ok:
                    reviews = r_mon.json().get("data", {}).get("reviews", [])
                    for rev in reviews:
                        if (rev.get("video") or {}).get("_id") == video_id:
                            actual_rev_id = rev.get("_id")
                            break
            except Exception:
                pass

        if not actual_rev_id:
            return {"success": False, "message": "Pending review ID not found for this video"}

        url = f"{BIDEO_API_BASE}/users/monetization/watch-review-ad/{actual_rev_id}"

        ads_watched = 0
        final_status = "pending"
        for i in range(4):
            try:
                r = requests.post(url, headers=headers, json={}, timeout=8)
                if r.ok:
                    d = r.json().get("data", {})
                    ads_watched = d.get("adsWatched", i + 1)
                    final_status = d.get("status", "pending")
                    if final_status == "passed" or ads_watched >= 4:
                        return {
                            "success": True,
                            "review_id": actual_rev_id,
                            "status": "passed",
                            "adsWatched": 4,
                            "message": "🎉 Video audit review successfully passed without watching ads!"
                        }
                time.sleep(0.4)
            except Exception:
                time.sleep(0.4)

        return {
            "success": final_status == "passed",
            "review_id": actual_rev_id,
            "status": final_status,
            "adsWatched": ads_watched,
            "message": "Review ad progress updated"
        }

    @classmethod
    def pass_all_pending_reviews(cls):
        """Bypasses and passes ALL pending video reviews for Cryvex in one go."""
        token = cls.get_cryvex_token()
        if not token:
            return {"success": False, "message": "Cryvex token not found"}

        headers = {"Authorization": f"Bearer {token}"}
        try:
            r_mon = requests.get(f"{BIDEO_API_BASE}/users/monetization/status", headers=headers, timeout=8)
            if not r_mon.ok:
                return {"success": False, "message": "Failed to fetch monetization status"}

            reviews = r_mon.json().get("data", {}).get("reviews", [])
            pending = [r for r in reviews if r.get("status") == "pending"]

            passed_count = 0
            for rev in pending:
                rev_id = rev.get("_id")
                res = cls.pass_video_review(review_id=rev_id)
                if res.get("success"):
                    passed_count += 1
                time.sleep(0.5)

            return {
                "success": True,
                "total_pending": len(pending),
                "passed_count": passed_count,
                "message": f"🎉 Successfully passed {passed_count} of {len(pending)} videos without watching ads!"
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ---------------------------------------------------------
    # Follow Booster (With Duplicate Check & Never Deletes Bots)
    # ---------------------------------------------------------
    @classmethod
    def get_followed_bots_for_channel(cls, channel_id):
        """Retrieves set of bot IDs that have ALREADY followed this channel."""
        try:
            r = requests.get(cls._firebase_url(f"follows/{channel_id}"), timeout=6)
            data = r.json()
            if isinstance(data, dict):
                return set(data.keys())
            return set()
        except Exception:
            return set()

    @classmethod
    def record_bot_follow(cls, channel_id, bot_id, bot_name):
        """Records that a bot followed this channel, ensuring it never re-follows."""
        try:
            requests.put(cls._firebase_url(f"follows/{channel_id}/{bot_id}"), json={
                "bot_id": bot_id,
                "bot_name": bot_name,
                "timestamp": datetime.utcnow().isoformat()
            }, timeout=5)
        except Exception:
            pass

    @classmethod
    def follow_channel(cls, bot_token, target_channel_id):
        """Sends follow request from a single bot."""
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        url = f"{BIDEO_API_BASE}/followers/{target_channel_id}"

        try:
            r = requests.post(url, headers=headers, json={}, timeout=8)
            data = r.json()
            if r.status_code == 201:
                return True, "Followed"
            if r.status_code == 200 and "unfollowed" in str(data.get("message", "")).lower():
                r2 = requests.post(url, headers=headers, json={}, timeout=8)
                return r2.ok, "Followed (restored)"
            if r.status_code == 200:
                return True, data.get("message", "Followed")
            return False, data.get("message", f"HTTP {r.status_code}")
        except Exception as e:
            return False, str(e)

    @classmethod
    def boost_followers(cls, target_channel_input=None, count=None):
        """
        Sends controlled number of followers to target channel (default: cryvex).
        - Skips bots that ALREADY followed this channel.
        - NEVER deletes any bot accounts (they remain active for views/likes).
        """
        actual_id, resolved_name = cls.resolve_channel_id(target_channel_input)
        bots = cls.get_all_bots()
        if not bots:
            return {
                "success": False,
                "message": "Koi bot account nahi mila! Pehle '1-Click Generate' se naye bot accounts banayein.",
                "followed_count": 0
            }

        already_followed_ids = cls.get_followed_bots_for_channel(actual_id)

        available_bots = [
            b for b in bots
            if b.get("_id") not in already_followed_ids
            and b.get("_id") != actual_id
            and b.get("token")
        ]

        if not available_bots:
            return {
                "success": False,
                "message": f"Sare {len(bots)} bot accounts already '{resolved_name}' ko follow kar chuke hain! Naye followers ke liye 'Generate Bots' se naye accounts banayein.",
                "total_bots": len(bots),
                "already_followed": len(already_followed_ids),
                "followed_count": 0
            }

        if count is not None and int(count) > 0:
            bots_to_use = available_bots[:int(count)]
        else:
            bots_to_use = available_bots

        success_count = 0
        details = []

        for bot in bots_to_use:
            token = bot["token"]
            bot_name = bot.get("name", "bot")
            bot_id = bot.get("_id")

            ok, msg = cls.follow_channel(token, actual_id)
            if ok:
                success_count += 1
                cls.record_bot_follow(actual_id, bot_id, bot_name)
                details.append({"bot": bot_name, "status": "success", "info": msg})
            else:
                details.append({"bot": bot_name, "status": "error", "error": msg})
            time.sleep(0.3)

        log_id = f"log_{int(datetime.utcnow().timestamp() * 1000)}"
        requests.put(cls._firebase_url(f"logs/{log_id}"), json={
            "id": log_id,
            "title": "Follower Booster Sent",
            "message": f"Sent {success_count} controlled followers to channel '{resolved_name}'! (Total bots intact: {len(bots)})",
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }, timeout=5)

        return {
            "success": True,
            "target_channel_id": actual_id,
            "target_channel_name": resolved_name,
            "requested_count": count or len(bots_to_use),
            "followed_count": success_count,
            "total_bots_in_vault": len(bots),
            "total_channel_followers_from_bots": len(already_followed_ids) + success_count,
            "remaining_available_bots": len(available_bots) - success_count,
            "details": details
        }

    @classmethod
    def get_follow_stats(cls, target_channel_input=None):
        """Returns statistics of bot followers for a channel."""
        actual_id, resolved_name = cls.resolve_channel_id(target_channel_input)
        bots = cls.get_all_bots()
        already_followed_ids = cls.get_followed_bots_for_channel(actual_id)

        available_count = sum(
            1 for b in bots
            if b.get("_id") not in already_followed_ids
            and b.get("_id") != actual_id
            and b.get("token")
        )

        return {
            "channel_id": actual_id,
            "channel_name": resolved_name,
            "total_bots": len(bots),
            "already_followed": len(already_followed_ids),
            "available_to_follow": available_count
        }

    # ---------------------------------------------------------
    # Views, Watch-Time & Likes Booster (Controlled Quantities)
    # ---------------------------------------------------------
    @classmethod
    def boost_video(cls, video_id, views_count=10, likes_count=5, watch_time=30):
        """
        Sends controlled views, watch-time, and likes to a video.
        - views_count: exact number of views to deliver
        - likes_count: exact number of likes to deliver
        - watch_time: authentic retention seconds (e.g. 30s, 60s)
        """
        clean_vid = str(video_id).strip().split("/")[-1].split("?")[0]
        bots = cls.get_all_bots()
        if not bots:
            return {"success": False, "message": "Koi bot account nahi mila! Pehle bot generate karein."}

        active_bots = [b for b in bots if b.get("token")]
        if not active_bots:
            return {"success": False, "message": "Koi active bot token nahi mila!"}

        random.shuffle(active_bots)

        delivered_views = 0
        delivered_likes = 0

        views_to_send = min(int(views_count), len(active_bots)) if views_count else len(active_bots)
        view_bots = active_bots[:views_to_send]

        for bot in view_bots:
            token = bot["token"]
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            try:
                r1 = requests.post(f"{BIDEO_API_BASE}/videos/{clean_vid}/view", headers=headers, json={}, timeout=6)
                if r1.ok:
                    delivered_views += 1
                if watch_time and int(watch_time) > 0:
                    requests.post(f"{BIDEO_API_BASE}/videos/{clean_vid}/watch-time", headers=headers, json={"watchTime": int(watch_time)}, timeout=6)
            except Exception:
                pass
            time.sleep(0.2)

        likes_to_send = min(int(likes_count), len(active_bots)) if likes_count else 0
        like_bots = active_bots[:likes_to_send]

        for bot in like_bots:
            token = bot["token"]
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            try:
                r2 = requests.post(f"{BIDEO_API_BASE}/videos/{clean_vid}/like", headers=headers, json={}, timeout=6)
                if r2.ok:
                    delivered_likes += 1
            except Exception:
                pass
            time.sleep(0.2)

        return {
            "success": True,
            "video_id": clean_vid,
            "views_delivered": delivered_views,
            "likes_delivered": delivered_likes,
            "watch_time_seconds": watch_time,
            "total_bots_used": max(len(view_bots), len(like_bots))
        }

    @classmethod
    def batch_boost_channel_videos(cls, channel_id=None, views_per_video=5, likes_per_video=3, watch_time=30):
        """Boosts all uploaded videos of the channel in one go."""
        videos_res = cls.get_channel_videos(channel_id)
        videos = videos_res.get("videos", [])
        if not videos:
            return {"success": False, "message": "Channel par koi video nahi mila!"}

        total_views = 0
        total_likes = 0
        results = []

        for v in videos:
            vid_id = v.get("_id")
            res = cls.boost_video(vid_id, views_count=views_per_video, likes_count=likes_per_video, watch_time=watch_time)
            if res.get("success"):
                total_views += res.get("views_delivered", 0)
                total_likes += res.get("likes_delivered", 0)
                results.append({
                    "video_id": vid_id,
                    "title": v.get("title", "")[:40],
                    "views": res.get("views_delivered", 0),
                    "likes": res.get("likes_delivered", 0)
                })
            time.sleep(0.5)

        return {
            "success": True,
            "channel_id": videos_res.get("channel_id"),
            "videos_boosted": len(results),
            "total_views_delivered": total_views,
            "total_likes_delivered": total_likes,
            "results": results
        }

    # ---------------------------------------------------------
    # Coin Farming & Home Feed Highlight Pinning
    # ---------------------------------------------------------
    @classmethod
    def pin_video_to_highlight(cls, video_id, duration_hours=1):
        """
        Pins a video to the top 4 Highlight Slots on the Home Feed.
        Requires 100 coins for 1 hour.
        """
        token = cls.get_cryvex_token()
        if not token:
            return {"success": False, "message": "Cryvex account token nahi mila!"}

        status_res = cls.get_cryvex_coins_status()
        current_coins = status_res.get("coins", 0) if status_res.get("success") else 0
        required_coins = 100 * int(duration_hours)

        if current_coins < required_coins:
            return {
                "success": False,
                "current_coins": current_coins,
                "required_coins": required_coins,
                "message": f"Highlight pin karne ke liye {required_coins} Coins chahiye! (Aapke pass abhi {current_coins} Coins hain). Kripya 'Claim Free Coins' button se coins gain karein."
            }

        clean_vid = str(video_id).strip().split("/")[-1].split("?")[0]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            r = requests.post(f"{BIDEO_API_BASE}/boost/create", headers=headers, json={
                "videoId": clean_vid,
                "duration": int(duration_hours)
            }, timeout=8)
            data = r.json()
            if r.ok and data.get("success"):
                return {"success": True, "message": "🎉 Video successfully pinned to Home Feed Top Highlights!", "data": data}
            return {"success": False, "message": data.get("message", "Highlight pin failed on Bideo server")}
        except Exception as e:
            return {"success": False, "message": str(e)}


# =====================================================================
# 24/7 Background Auto Coin Miner (Zero Manual Effort)
# =====================================================================
class AutoCoinMiner:
    """
    Automated background worker that runs continuously as long as server is on.
    It automatically queries Cryvex's boost status:
    - Claims free ad coins whenever available (up to daily limits).
    - Automatically waits through cooldown periods without user intervention.
    - Eliminates the need to manually click claim buttons.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.running = False
        self.thread = None
        self.status = {
            "active": False,
            "state": "idle",
            "message": "Auto-miner ready",
            "coins_mined_today": 0,
            "current_coins": 0,
            "remaining_daily": 16,
            "cooldown_remaining_seconds": 0,
            "last_claim_time": None,
            "last_reward": 0
        }

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start(self):
        with self._lock:
            if self.running:
                return
            self.running = True
            self.status["active"] = True
            self.thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.thread.start()
            print("[AUTO-MINER] 🪙 Automatic Background Coin Miner started! Mining coins in background...")

    def get_status(self):
        return self.status

    def _worker_loop(self):
        time.sleep(2)
        while self.running:
            try:
                # 1. Fetch live Cryvex coins & daily ad status
                status_res = BotEngine.get_cryvex_coins_status()
                if not status_res.get("success"):
                    self.status["state"] = "waiting"
                    self.status["message"] = f"Boost check: {status_res.get('message', 'Waiting...')}"
                    time.sleep(15)
                    continue

                coins = status_res.get("coins", 0)
                daily = status_res.get("dailyAds", {})
                self.status["current_coins"] = coins

                remaining = daily.get("remaining", 0)
                can_watch = daily.get("canWatch", False)
                cooldown_secs = daily.get("cooldownSeconds", 0)
                self.status["remaining_daily"] = remaining
                self.status["cooldown_remaining_seconds"] = cooldown_secs

                # If daily limit reached
                if remaining <= 0:
                    self.status["state"] = "daily_completed"
                    self.status["message"] = f"🎉 Aaj ke sabhi free coin claims complete! (Cryvex Balance: {coins} Coins)"
                    time.sleep(300)
                    continue

                # If in cooldown
                if not can_watch or cooldown_secs > 0:
                    wait_time = max(int(cooldown_secs), 10)
                    mins = math.ceil(wait_time / 60)
                    self.status["state"] = "cooldown"
                    self.status["message"] = f"⏳ Cooldown active (~{mins}m). Cooldown khatam hote hi agla batch auto-claim hoga."

                    # Sleep in small 5s intervals so countdown stays accurate
                    slept = 0
                    while slept < wait_time and self.running:
                        time.sleep(5)
                        slept += 5
                        self.status["cooldown_remaining_seconds"] = max(0, wait_time - slept)
                    continue

                # Ready to claim!
                self.status["state"] = "claiming"
                self.status["message"] = "🪙 Claiming free coins from Bideo API..."
                claim_res = BotEngine.claim_cryvex_ad_coins()

                if claim_res.get("success"):
                    reward = claim_res.get("coinsEarned", 0)
                    new_total = claim_res.get("totalCoins", coins)
                    self.status["coins_mined_today"] += reward
                    self.status["last_reward"] = reward
                    self.status["last_claim_time"] = datetime.utcnow().isoformat()
                    self.status["current_coins"] = new_total
                    self.status["remaining_daily"] = claim_res.get("remainingDaily", max(0, remaining - 1))
                    self.status["cooldown_remaining_seconds"] = claim_res.get("cooldownSeconds", 0)
                    self.status["message"] = f"🎉 Auto-Claimed +{reward} Free Coins! New Balance: {new_total} Coins."
                    print(f"[AUTO-MINER] ✅ +{reward} Coins auto-claimed! Cryvex Total Coins: {new_total}")
                    time.sleep(2)  # Short gap between claims within same session
                else:
                    self.status["message"] = claim_res.get("message", "Ad claim pending...")
                    time.sleep(10)

            except Exception as e:
                self.status["message"] = f"Error in auto-miner: {str(e)}"
                time.sleep(15)

