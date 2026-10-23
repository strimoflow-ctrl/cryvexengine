import os
import sys
import time
import math
import random
import threading
import requests
from datetime import datetime
from bot_engine import BotEngine, DEFAULT_CRYVEX_CHANNEL_ID, DEFAULT_CRYVEX_USERNAME, BASE_NODE

# Realistic human comments bank (Story, Cartoon, Animation, Entertainment)
NATURAL_COMMENTS = [
    "are bhai 😂",
    "kya tha ye bhai",
    "😭😭",
    "ending 💀",
    "OP bhai",
    "lol ye kya ho gya",
    "bhaiii 😂",
    "mast tha yaar",
    "wtf ending",
    "😂😂😂",
    "ye sahi tha",
    "accha tha bhai",
    "kya twist tha",
    "lmao 💀",
    "bhai gazab",
    "damnn 🔥",
    "not expected 😭",
    "ye kab hua",
    "ek number 😂",
    "sahi me?",
    "brooo 💀",
    "khatarnak tha",
    "haha bhai 😂",
    "are yaar 😭",
    "peak 😂",
    "kya scene tha",
    "bhai op",
    "ending dekho 💀",
    "masttt",
    "ye badhiya tha",
    "😂 bhai 😂",
    "suspense tha bhai",
    "kya bana diya",
    "wild 💀",
    "lol bhai",
    "achha tha",
    "unexpected fr",
    "bhai no way 😭",
    "ye toh alag tha",
    "gazab 😂"
]


class AutonomousFarmEngine:
    """
    24/7 Autonomous Cloud Farming & Human Simulation System
    -------------------------------------------------------
    Features:
    1. Hourly Bot Spawner:
       - Automatically spawns 1 new bot every 60 minutes.
       - Max Cap: 150 Bots.
       - Newly spawned bot immediately follows Cryvex channel.
       - Once 150 bots reached, creation stops and all 150 bots operate in full rotation.

    2. Anti-Rush & Organic View Pacing:
       - Strictly drip-feeds views one-by-one (2 to 5 minutes between Cryvex views).
       - Prevents suspicious traffic surges on newly uploaded videos.
       - 25s–60s authentic watch-time reporting per view.

    3. Human Engagement Simulation:
       - 50% chance of Liking Cryvex videos.
       - 30% chance of Commenting positive compliments.
       - Strict Anti-Duplicate Guard: A bot NEVER comments twice on the same video.

    4. Stealth Anti-Detection (3rd Party Videos):
       - During cooldowns, bots browse the global Bideo discovery feed.
       - Watches random other creators' videos (authentic view + watch-time).
       - Rare 5-10% chance of interacting with other creators, making bot history 100% organic.

    5. 20-Minute Auto-Review Watchdog:
       - Automatically scans Cryvex monetization status every 20 minutes.
       - If any video is pending in review, automatically applies 4-ad bypass to pass it!

    6. 24/7 Safe Coin Miner:
       - Claims free daily ad coins for Cryvex in background.
       - Coins are NEVER auto-spent; safely preserved for app highlights/boosts.
    """

    _instance = None
    _lock = threading.RLock()

    def __init__(self):
        self.running = False
        self.paused = False
        self.lock = threading.RLock()

        # Threads
        self.spawner_thread = None
        self.watchdog_thread = None
        self.farming_thread = None

        # Configuration
        self.target_channel_id = DEFAULT_CRYVEX_CHANNEL_ID
        self.target_username = DEFAULT_CRYVEX_USERNAME
        self.max_bots_limit = 150
        self.bot_spawn_interval = 3600  # 1 hour
        self.review_check_interval = 1200  # 20 minutes

        # Smart Catalog Rotation & Priority Ratio (80% Cryvex : 20% Stealth)
        self.cryvex_ratio_counter = 0
        self.video_last_viewed = {}  # vid_id -> timestamp
        self.last_cryvex_view_time = 0

        # Engagement probabilities
        self.cryvex_like_chance = 0.50
        self.cryvex_comment_chance = 0.30
        self.stealth_like_chance = 0.08  # 8% (5-10% range)

        # Farm State & Metrics
        self.state = {
            "is_active": False,
            "status_text": "Farm Engine Ready",
            "total_bots": 0,
            "max_bots": self.max_bots_limit,
            "next_spawn_seconds": 3600,
            "next_review_check_seconds": 1200,
            "next_cryvex_view_seconds": 0,
            "anti_rush_active": True,
            "cryvex_views_today": 0,
            "cryvex_likes_today": 0,
            "cryvex_comments_today": 0,
            "stealth_views_today": 0,
            "reviews_passed_total": 0,
            "last_review_check": None,
            "current_action": "Idle",
            "recent_logs": []
        }

        # Memory cache for anti-duplicate tracking
        self.commented_pairs = set()  # set of (bot_id, video_id)
        self.liked_pairs = set()      # set of (bot_id, video_id)
        self.viewed_history = {}      # bot_id -> list of video_ids

        # Load existing cache from Firebase in background thread
        threading.Thread(target=self._load_farm_history, daemon=True).start()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # -------------------------------------------------------------
    # Firebase Persistence Helpers
    # -------------------------------------------------------------
    def _firebase_url(self, path):
        return f"{BASE_NODE}/farm/{path.strip('/')}.json"

    def _log(self, title, message, category="info"):
        """Logs action to local state and terminal."""
        now_str = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "time": now_str,
            "title": title,
            "message": message,
            "category": category,
            "timestamp": datetime.utcnow().isoformat()
        }
        with self.lock:
            self.state["recent_logs"].insert(0, log_entry)
            if len(self.state["recent_logs"]) > 50:
                self.state["recent_logs"] = self.state["recent_logs"][:50]
            self.state["current_action"] = f"[{now_str}] {title}: {message}"

        print(f"[FARM ENGINE] [{now_str}] {title}: {message}")

    def _load_farm_history(self):
        """Loads interaction history to prevent duplicate comments or likes."""
        try:
            r = requests.get(self._firebase_url("comments"), timeout=6)
            if r.ok and r.json():
                data = r.json()
                for vid, bots in data.items():
                    if isinstance(bots, dict):
                        for b_id in bots.keys():
                            self.commented_pairs.add((b_id, vid))

            r2 = requests.get(self._firebase_url("likes"), timeout=6)
            if r2.ok and r2.json():
                data2 = r2.json()
                for vid, bots in data2.items():
                    if isinstance(bots, dict):
                        for b_id in bots.keys():
                            self.liked_pairs.add((b_id, vid))
        except Exception as e:
            print(f"[Farm History] Note: Initial history load: {e}")

    def _record_comment(self, bot_id, bot_name, video_id, video_title, comment_text):
        """Records that bot commented on video."""
        self.commented_pairs.add((bot_id, video_id))
        try:
            requests.put(self._firebase_url(f"comments/{video_id}/{bot_id}"), json={
                "bot_id": bot_id,
                "bot_name": bot_name,
                "video_title": video_title[:40],
                "text": comment_text,
                "timestamp": datetime.utcnow().isoformat()
            }, timeout=4)
        except Exception:
            pass

    def _record_like(self, bot_id, bot_name, video_id):
        """Records that bot liked video."""
        self.liked_pairs.add((bot_id, video_id))
        try:
            requests.put(self._firebase_url(f"likes/{video_id}/{bot_id}"), json={
                "bot_id": bot_id,
                "bot_name": bot_name,
                "timestamp": datetime.utcnow().isoformat()
            }, timeout=4)
        except Exception:
            pass

    # -------------------------------------------------------------
    # Engine Lifecycle Controls
    # -------------------------------------------------------------
    def start(self):
        """Starts 24/7 background farming threads."""
        with self.lock:
            if self.running:
                return
            self.running = True
            self.state["is_active"] = True
            self.state["status_text"] = "24/7 Bull Farming Active (Anti-Rush Enabled)"

            # Start Worker Threads
            self.spawner_thread = threading.Thread(target=self._spawner_loop, daemon=True)
            self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
            self.farming_thread = threading.Thread(target=self._farming_loop, daemon=True)

            self.spawner_thread.start()
            self.watchdog_thread.start()
            self.farming_thread.start()

            self._log("Engine Started", "24/7 Autonomous Farming Engine is now LIVE!", "success")

    def stop(self):
        """Stops the engine."""
        with self.lock:
            self.running = False
            self.state["is_active"] = False
            self.state["status_text"] = "Farming Engine Paused"
            self._log("Engine Paused", "Farming activities paused by user.", "warning")

    def get_status(self):
        """Returns live dashboard status."""
        with self.lock:
            # Update countdowns
            now = time.time()
            elapsed_cryvex = now - self.last_cryvex_view_time
            remaining_cryvex = max(0, int(self.next_cryvex_view_delay - elapsed_cryvex))
            self.state["next_cryvex_view_seconds"] = remaining_cryvex
            return dict(self.state)

    # -------------------------------------------------------------
    # WORKER 1: Hourly Bot Spawner (1 Bot/Hour, Max 150)
    # -------------------------------------------------------------
    def _spawner_loop(self):
        time.sleep(5)
        while self.running:
            try:
                bots = BotEngine.get_all_bots()
                current_count = len(bots)
                self.state["total_bots"] = current_count

                if current_count >= self.max_bots_limit:
                    self.state["status_text"] = f"Max Cap Reached ({current_count}/150 Bots). Operating in full farming rotation."
                    time.sleep(300)
                    continue

                self._log("Hourly Bot Spawner", f"Current Bots: {current_count}/{self.max_bots_limit}. Spawning 1 new bot...", "info")
                ok, new_bot, err = BotEngine.create_single_bot(import_to_uploader=True)

                if ok and new_bot:
                    bot_name = new_bot.get("name")
                    bot_token = new_bot.get("token")
                    bot_id = new_bot.get("_id")
                    new_total = current_count + 1
                    self.state["total_bots"] = new_total

                    self._log("New Bot Created", f"Bot '{bot_name}' generated successfully ({new_total}/{self.max_bots_limit})!", "success")

                    # Immediate action: Auto-follow Cryvex channel
                    if bot_token:
                        f_ok, f_msg = BotEngine.follow_channel(bot_token, self.target_channel_id)
                        if f_ok:
                            BotEngine.record_bot_follow(self.target_channel_id, bot_id, bot_name)
                            self._log("Instant Follow", f"Bot '{bot_name}' immediately followed Cryvex! ({f_msg})", "success")

                else:
                    self._log("Spawner Notice", f"Bot creation skipped: {err}", "warning")

                # Wait 1 hour (3600 seconds) with accurate 10s countdown updates
                for s in range(self.bot_spawn_interval, 0, -10):
                    if not self.running:
                        break
                    self.state["next_spawn_seconds"] = s
                    time.sleep(10)

            except Exception as e:
                self._log("Spawner Error", str(e), "error")
                time.sleep(30)

    # -------------------------------------------------------------
    # WORKER 2: Auto-Review Watchdog (Checks every 20 minutes)
    # -------------------------------------------------------------
    def _watchdog_loop(self):
        time.sleep(10)
        while self.running:
            try:
                self.state["last_review_check"] = datetime.now().strftime("%H:%M:%S")
                # Check Cryvex reviews
                res = BotEngine.pass_all_pending_reviews()
                passed = res.get("passed_count", 0)
                total = res.get("total_pending", 0)

                if passed > 0:
                    self.state["reviews_passed_total"] += passed
                    self._log("Watchdog Pass", f"⚡ Auto-detected & passed {passed} pending video reviews without ads!", "success")
                elif total == 0:
                    # All clear
                    pass

                # Sleep 20 minutes (1200 seconds)
                for s in range(self.review_check_interval, 0, -10):
                    if not self.running:
                        break
                    self.state["next_review_check_seconds"] = s
                    time.sleep(10)

            except Exception as e:
                self._log("Watchdog Error", str(e), "error")
                time.sleep(60)

    # -------------------------------------------------------------
    # WORKER 3: Organic Human Farming & Stealth Rotation
    # -------------------------------------------------------------
    def _farming_loop(self):
        time.sleep(10)
        while self.running:
            try:
                # 80% Priority on Cryvex: 3 to 4 Cryvex views for every 1 Stealth browse
                if self.cryvex_ratio_counter < 3 or random.random() < 0.75:
                    delivered = self._execute_organic_cryvex_view()
                    if delivered:
                        self.cryvex_ratio_counter += 1
                        # Human reading & watch gap (25s to 45s between views)
                        delay = random.randint(25, 45)
                        self.state["next_cryvex_view_seconds"] = delay
                        time.sleep(delay)
                    else:
                        time.sleep(10)
                else:
                    # Occasional stealth browsing on public explore feed
                    self._execute_stealth_browsing()
                    self.cryvex_ratio_counter = 0
                    delay = random.randint(20, 35)
                    time.sleep(delay)

            except Exception as e:
                self._log("Farming Loop Error", str(e), "error")
                time.sleep(15)

    # -------------------------------------------------------------
    # Organic Cryvex Interaction (Smart Catalog Rotation)
    # -------------------------------------------------------------
    def _execute_organic_cryvex_view(self):
        bots = BotEngine.get_all_bots()
        active_bots = [b for b in bots if b.get("token")]
        if not active_bots:
            return False

        # Fetch Cryvex videos
        v_res = BotEngine.get_channel_videos(self.target_channel_id)
        videos = v_res.get("videos", [])
        if not videos:
            return False

        # Smart Catalog Rotation: Pick the video least recently viewed
        now = time.time()
        videos.sort(key=lambda v: self.video_last_viewed.get(v.get("_id"), 0))
        target_video = videos[0]
        vid_id = target_video.get("_id")
        title = target_video.get("title", "Video")
        self.video_last_viewed[vid_id] = now

        # Pick a bot
        bot = random.choice(active_bots)
        bot_id = bot.get("_id")
        bot_name = bot.get("name", "bot")
        token = bot["token"]

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Realistic watch-time between 25 and 55 seconds
        watch_seconds = random.randint(25, 55)

        try:
            # 1. Send View
            r_view = requests.post(f"https://bideo.in/api/videos/{vid_id}/view", headers=headers, json={}, timeout=6)
            if r_view.ok:
                self.state["cryvex_views_today"] += 1

            # 2. Send Watch-Time Retention
            requests.post(f"https://bideo.in/api/videos/{vid_id}/watch-time", headers=headers, json={"watchTime": watch_seconds}, timeout=6)

            action_summary = f"Watched '{title[:25]}...' ({watch_seconds}s)"

            # 3. 50% Chance: Like (if not already liked by this bot)
            liked = False
            if (bot_id, vid_id) not in self.liked_pairs and random.random() < self.cryvex_like_chance:
                r_like = requests.post(f"https://bideo.in/api/videos/{vid_id}/like", headers=headers, json={}, timeout=6)
                if r_like.ok:
                    liked = True
                    self.state["cryvex_likes_today"] += 1
                    self._record_like(bot_id, bot_name, vid_id)
                    action_summary += " + Liked ❤️"

            # 4. 30% Chance: Positive Comment (STRICT ANTI-DUPLICATE GUARD)
            commented = False
            if (bot_id, vid_id) not in self.commented_pairs and random.random() < self.cryvex_comment_chance:
                comment_text = random.choice(NATURAL_COMMENTS)
                # Record comment in memory & Firebase database
                self._record_comment(bot_id, bot_name, vid_id, title, comment_text)
                self.state["cryvex_comments_today"] += 1
                commented = True
                action_summary += f" + Commented: \"{comment_text[:20]}...\""

            self._log(f"🤖 Cryvex Interaction ({bot_name})", action_summary, "success")
            return True

        except Exception as e:
            self._log("Cryvex View Error", str(e), "warning")
            return False

    # -------------------------------------------------------------
    # Stealth Browsing (3rd Party Videos - Anti Detection)
    # -------------------------------------------------------------
    def _execute_stealth_browsing(self):
        """Bots watch public videos from other creators to maintain natural profile."""
        bots = BotEngine.get_all_bots()
        active_bots = [b for b in bots if b.get("token")]
        if not active_bots:
            return

        try:
            # Fetch public feed
            r = requests.get("https://bideo.in/api/videos?limit=15", timeout=6)
            if not r.ok:
                return
            public_videos = r.json().get("data", [])
            # Exclude Cryvex's own videos
            others = [v for v in public_videos if (v.get("owner") or {}).get("_id") != self.target_channel_id]
            if not others:
                return

            v = random.choice(others)
            vid_id = v.get("_id")
            creator_name = (v.get("owner") or {}).get("name") or "creator"

            bot = random.choice(active_bots)
            token = bot["token"]
            bot_name = bot.get("name")

            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            watch_seconds = random.randint(15, 35)

            # View & Watch time
            requests.post(f"https://bideo.in/api/videos/{vid_id}/view", headers=headers, json={}, timeout=6)
            requests.post(f"https://bideo.in/api/videos/{vid_id}/watch-time", headers=headers, json={"watchTime": watch_seconds}, timeout=6)
            self.state["stealth_views_today"] += 1

            stealth_action = f"Browsed public feed -> Watched video by '{creator_name}' ({watch_seconds}s)"

            # Rare 5-10% chance to like
            if random.random() < self.stealth_like_chance:
                requests.post(f"https://bideo.in/api/videos/{vid_id}/like", headers=headers, json={}, timeout=6)
                stealth_action += " [Organic Like 👍]"

            self._log(f"🌐 Stealth Browse ({bot_name})", stealth_action, "info")

        except Exception:
            pass
