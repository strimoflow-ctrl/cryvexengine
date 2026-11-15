import os
import sys
import time
import math
import random
import threading
import requests
from datetime import datetime
from bot_engine import BotEngine, DEFAULT_CRYVEX_CHANNEL_ID, DEFAULT_CRYVEX_USERNAME, BASE_NODE, DEFAULT_USER_AGENT
from view_limit_manager import ViewLimitManager

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
       - Max Cap: 300 Bots.
       - Newly spawned bot immediately follows Cryvex channel.
       - Once 300 bots reached, creation stops and all 300 bots operate in full rotation.

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
        self.farming_threads = []

        # Configuration
        self.target_channel_id = DEFAULT_CRYVEX_CHANNEL_ID
        self.target_username = DEFAULT_CRYVEX_USERNAME
        self.max_bots_limit = 300
        self.bot_spawn_interval = 3600  # 1 hour
        self.review_check_interval = 1200  # 20 minutes

        # Smart Catalog Rotation & Priority Ratio (80% Cryvex : 20% Stealth)
        self.cryvex_ratio_counter = 0
        self.video_last_viewed = {}  # vid_id -> timestamp
        self.last_cryvex_view_time = 0
        self.next_cryvex_view_delay = 180

        # Engagement probabilities
        self.cryvex_like_chance = 0.50
        self.cryvex_comment_chance = 0.30
        self.stealth_like_chance = 0.20  # 20% organic likes during explore browsing

        # 24H View Limits & Multi-Channel Manager
        self.view_limit_mgr = ViewLimitManager.get_instance()

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
            "current_mode": "Target Views Boosting",
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

        # Colorful ANSI 256 Console Print
        clr = "\033[1;38;5;82m" if category == "success" else ("\033[1;38;5;220m" if category == "coin" or "coin" in message.lower() else ("\033[1;38;5;141m" if category == "stealth" or "stealth" in title.lower() else ("\033[1;38;5;196m" if category == "error" else "\033[1;38;5;51m")))
        clr_rst = "\033[0m"
        print(f"{clr}[FARM ENGINE] [{now_str}] {title}: {message}{clr_rst}")

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

            # Start Worker Threads (2 Balanced Farming Workers to maintain 17k-20k weekly views)
            self.spawner_thread = threading.Thread(target=self._spawner_loop, daemon=True)
            self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
            self.farming_threads = [
                threading.Thread(target=self._farming_loop, args=(wid,), daemon=True)
                for wid in range(1, 3)
            ]

            self.spawner_thread.start()
            self.watchdog_thread.start()
            for t in self.farming_threads:
                t.start()

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
            elapsed_cryvex = now - getattr(self, "last_cryvex_view_time", 0)
            delay = getattr(self, "next_cryvex_view_delay", 180)
            remaining_cryvex = max(0, int(delay - elapsed_cryvex))
            self.state["next_cryvex_view_seconds"] = remaining_cryvex
            res = dict(self.state)
            try:
                res["views_summary"] = self.view_limit_mgr.get_all_channels_summary()
            except Exception:
                pass
            return res

    # -------------------------------------------------------------
    # WORKER 1: Hourly Bot Spawner (1 Bot/Hour, Max 300)
    # -------------------------------------------------------------
    def _spawner_loop(self):
        time.sleep(5)
        while self.running:
            try:
                bots = BotEngine.get_all_bots()
                current_count = len(bots)
                self.state["total_bots"] = current_count

                if current_count >= self.max_bots_limit:
                    self.state["status_text"] = f"Max Cap Reached ({current_count}/{self.max_bots_limit} Bots). Operating in full farming rotation."
                    time.sleep(300)
                    continue

                self._log("Hourly Bot Spawner", f"Current Bots: {current_count}/{self.max_bots_limit}. Spawning 1 new bot...", "info")
                ok, new_bot, err = BotEngine.create_single_bot(import_to_uploader=False)

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
    # WORKER 3: Organic Human Farming & Stealth Rotation (Target: 17k-20k views/week)
    # -------------------------------------------------------------
    def _farming_loop(self, worker_id=1):
        # Stagger worker starts
        time.sleep(worker_id * 6)
        local_ratio_counter = 0
        last_standby_log_time = 0

        while self.running:
            try:
                # 1. Master Global Check: Is view engine allowed to operate?
                g_allowed, g_msg, total_views, g_limit = self.view_limit_mgr.is_viewing_allowed_globally()

                if not g_allowed:
                    # View bot is paused or global 24h budget reached!
                    # "views wala bot band ho jaye apne app okk"
                    self.state["current_mode"] = f"Standby: {g_msg}"
                    now = time.time()
                    if now - last_standby_log_time > 300:  # Log once every 5 minutes at most, keeping terminal 100% clean
                        self._log("Views Standby", f"💤 View bot asleep: {g_msg} (Total 24h: {total_views}/{g_limit})", "info")
                        last_standby_log_time = now
                    time.sleep(25)
                    continue

                # 2. Check if any channels have remaining 24H view budget
                eligible_channels = self.view_limit_mgr.get_eligible_channels()

                if eligible_channels:
                    self.state["current_mode"] = "Target Channel Views"
                    # Periodically perform stealth browsing for human-like profile (if global limit has room)
                    if local_ratio_counter < 5 or random.random() < 0.85:
                        delivered = self._execute_channel_view(eligible_channels, worker_id)
                        if delivered:
                            local_ratio_counter += 1
                            delay = random.randint(25, 38)
                            self.state["next_cryvex_view_seconds"] = delay
                            time.sleep(delay)
                        else:
                            time.sleep(10)
                    else:
                        # Occasional organic stealth browse
                        self._execute_stealth_browsing(is_idle_fallback=False)
                        local_ratio_counter = 0
                        delay = random.randint(20, 32)
                        time.sleep(delay)
                else:
                    # ALL CHANNELS COMPLETED OR PAUSED!
                    # Check if global limit has reached or still has room
                    curr_total = self.view_limit_mgr.get_total_views_24h()
                    if g_limit > 0 and curr_total >= g_limit:
                        # All channels target complete AND global target complete!
                        # "sare channel ka target complite ho gya h ur globel ka bhi to views wala bot band ho jaye apne app"
                        self.state["current_mode"] = f"💤 Standby: All Targets & 24H Global Budget Completed ({curr_total}/{g_limit})"
                        now = time.time()
                        if now - last_standby_log_time > 300:
                            self._log("Views Standby", f"🏁 All channels & global 24h budget completed ({curr_total}/{g_limit}). View bot in standby.", "success")
                            last_standby_log_time = now
                        time.sleep(30)
                    else:
                        # Free bots can browse public explore feed & like videos until global limit is reached
                        self.state["current_mode"] = f"Organic Stealth Browsing ({curr_total}/{g_limit} Global Views)"
                        self._execute_stealth_browsing(is_idle_fallback=True)
                        delay = random.randint(25, 40)
                        time.sleep(delay)

            except Exception as e:
                self._log(f"Farming Loop W{worker_id} Error", str(e), "error")
                time.sleep(15)

    # -------------------------------------------------------------
    # Organic Multi-Channel Interaction & 24H Limit Delivery
    # -------------------------------------------------------------
    def _execute_channel_view(self, eligible_channels, worker_id=1):
        bots = BotEngine.get_all_bots()
        active_bots = [b for b in bots if b.get("token")]
        if not active_bots:
            return False

        # Pick target channel from eligible channels (prioritize ones with lowest completion percentage)
        target_channel = random.choice(eligible_channels[:max(1, len(eligible_channels) // 2 + 1)])
        ch_id = target_channel.get("channel_id")
        ch_name = target_channel.get("name") or "Channel"
        daily_limit = target_channel.get("daily_limit", 200)

        # Fetch channel videos
        v_res = BotEngine.get_channel_videos(ch_id)
        videos = v_res.get("videos", [])
        if not videos:
            return False

        # Smart Catalog Balancing
        now = time.time()
        if random.random() < 0.60:
            sorted_by_views = sorted(videos, key=lambda v: v.get("views", 0))
            lower_pool = sorted_by_views[:max(1, len(sorted_by_views) // 2)]
            lower_pool.sort(key=lambda v: self.video_last_viewed.get(v.get("_id"), 0))
            target_video = lower_pool[0]
        else:
            videos.sort(key=lambda v: self.video_last_viewed.get(v.get("_id"), 0))
            cand_pool = videos[:max(1, len(videos) // 2)]
            target_video = random.choice(cand_pool)

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
            "Content-Type": "application/json",
            "User-Agent": DEFAULT_USER_AGENT
        }

        # Realistic watch-time between 25 and 55 seconds
        watch_seconds = random.randint(25, 55)

        try:
            # 1. Send View
            r_view = requests.post(f"https://bideo.in/api/videos/{vid_id}/view", headers=headers, json={}, timeout=6)
            if r_view.ok:
                if ch_id == DEFAULT_CRYVEX_CHANNEL_ID:
                    self.state["cryvex_views_today"] += 1

            # 2. Record view in 24h limit manager
            self.view_limit_mgr.record_view(ch_id, vid_id, title)
            curr_24h = self.view_limit_mgr.get_views_last_24h(ch_id)

            # 3. Send Watch-Time Retention
            requests.post(f"https://bideo.in/api/videos/{vid_id}/watch-time", headers=headers, json={"watchTime": watch_seconds}, timeout=6)

            action_summary = f"Boosted '{ch_name}' video '{title[:22]}...' ({watch_seconds}s) [{curr_24h}/{daily_limit} 24h Views]"

            # 4. 50% Chance: Like (if not already liked by this bot)
            liked = False
            if (bot_id, vid_id) not in self.liked_pairs and random.random() < self.cryvex_like_chance:
                r_like = requests.post(f"https://bideo.in/api/videos/{vid_id}/like", headers=headers, json={}, timeout=6)
                if r_like.ok:
                    liked = True
                    if ch_id == DEFAULT_CRYVEX_CHANNEL_ID:
                        self.state["cryvex_likes_today"] += 1
                    self._record_like(bot_id, bot_name, vid_id)
                    action_summary += " + Liked ❤️"

            # 5. 30% Chance: Positive Comment (STRICT ANTI-DUPLICATE GUARD)
            commented = False
            if (bot_id, vid_id) not in self.commented_pairs and random.random() < self.cryvex_comment_chance:
                comment_text = random.choice(NATURAL_COMMENTS)
                self._record_comment(bot_id, bot_name, vid_id, title, comment_text)
                if ch_id == DEFAULT_CRYVEX_CHANNEL_ID:
                    self.state["cryvex_comments_today"] += 1
                commented = True
                action_summary += f" + Commented: \"{comment_text[:20]}...\""

            self._log(f"👁️ [VIEW BOOSTER] Bot ({bot_name})", action_summary, "success")
            return True

        except Exception as e:
            self._log(f"View Error ({ch_name})", str(e), "warning")
            return False

    def _execute_organic_cryvex_view(self, worker_id=1):
        """Backward-compatible caller for default channel view."""
        eligible = self.view_limit_mgr.get_eligible_channels()
        if not eligible:
            return False
        return self._execute_channel_view(eligible, worker_id)

    # -------------------------------------------------------------
    # Stealth Browsing (3rd Party Videos - Anti Detection & Free Bots)
    # -------------------------------------------------------------
    def _execute_stealth_browsing(self, is_idle_fallback=False):
        """Bots watch public videos from other creators to maintain natural profile and like videos."""
        bots = BotEngine.get_all_bots()
        active_bots = [b for b in bots if b.get("token")]
        if not active_bots:
            return

        try:
            # Fetch public feed
            r = requests.get("https://bideo.in/api/videos?limit=15", headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=8)
            if not r.ok:
                return
            public_videos = r.json().get("data", [])
            # Exclude all configured target channels
            managed_ids = set(k for k in self.view_limit_mgr.data.keys() if k != "_global")
            others = [v for v in public_videos if (v.get("owner") or {}).get("_id") not in managed_ids]
            if not others:
                others = public_videos
            if not others:
                return

            v = random.choice(others)
            vid_id = v.get("_id")
            creator_name = (v.get("owner") or {}).get("name") or "creator"

            bot = random.choice(active_bots)
            token = bot["token"]
            bot_name = bot.get("name")

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": DEFAULT_USER_AGENT
            }
            watch_seconds = random.randint(18, 38)

            # View & Watch time
            requests.post(f"https://bideo.in/api/videos/{vid_id}/view", headers=headers, json={}, timeout=6)
            requests.post(f"https://bideo.in/api/videos/{vid_id}/watch-time", headers=headers, json={"watchTime": watch_seconds}, timeout=6)
            self.state["stealth_views_today"] += 1

            # Record stealth view in ViewLimitManager
            self.view_limit_mgr.record_stealth_view(video_id=vid_id, creator=creator_name)
            curr_global_views = self.view_limit_mgr.get_total_views_24h()
            curr_global_limit = self.view_limit_mgr.get_global_limit()

            reason_str = "All Channel Targets Met" if is_idle_fallback else "Organic Warming"
            stealth_action = f"Browsed public feed ({reason_str}) -> Watched '{creator_name}' ({watch_seconds}s) [{curr_global_views}/{curr_global_limit} Global Views]"

            # Higher like probability when bots are free/idle (35%), normal (20%)
            like_prob = 0.35 if is_idle_fallback else self.stealth_like_chance
            if random.random() < like_prob:
                requests.post(f"https://bideo.in/api/videos/{vid_id}/like", headers=headers, json={}, timeout=6)
                stealth_action += " [Organic Like 👍]"

            self._log(f"🌐 Stealth Browse ({bot_name})", stealth_action, "stealth")

        except Exception as e:
            pass
