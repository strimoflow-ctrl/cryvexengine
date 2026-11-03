"""
=============================================================================
🏆 BIDEO PODIUM COIN MINER - 24/7 AUTONOMOUS MULTI-STREAM ENGINE
=============================================================================
Dominates Rank 1, Rank 2, and Rank 3 on the Bideo Platform:
- 🥇 Rank 1: cryvex       (Phone: 7052733069)
- 🥈 Rank 2: pankaj_bideo (Phone: 9115233706)
- 🥉 Rank 3: hariom_ai    (Phone: 9648083419)

Earning Streams:
1. Video Watch-Time Mining (1 min = 1 Coin via /api/videos/<id>/watch-time)
2. Daily Ad Rewards Auto-Claim (+2 Coins per ad, up to 16 ads/day)
3. Built-in Auto-Relogin & Token Recovery
4. Strict Podium Hierarchy Guard (Rank 1 > Rank 2 > Rank 3)
=============================================================================
"""

import os
import sys
import time
import json
import random
import threading
from datetime import datetime
from collections import deque
import requests

import functools
print = functools.partial(print, flush=True)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BIDEO_API_BASE = "https://bideo.in/api"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
FIREBASE_PODIUM_URL = "https://secret-gpt-default-rtdb.asia-southeast1.firebasedatabase.app/bideo_automation/podium_miner.json"

# ANSI 256 Cyberpunk Console Colors
CLR_GOLD = "\033[1;38;5;220m"
CLR_GREEN = "\033[1;38;5;82m"
CLR_CYAN = "\033[1;38;5;51m"
CLR_PURPLE = "\033[1;38;5;141m"
CLR_RED = "\033[1;38;5;196m"
CLR_DIM = "\033[38;5;244m"
CLR_BOLD = "\033[1m"
CLR_RESET = "\033[0m"

# ---------------------------------------------------------------------------
# PODIUM ACCOUNTS CONFIGURATION
# ---------------------------------------------------------------------------
PODIUM_CONFIG = [
    {
        "rank": 1,
        "label": "🥇 Rank 1",
        "username": "cryvex",
        "phone": "7052733069",
        "password": "pankaj@5911",
        "user_id": "6ada0b9dfb39968c7c48dd7b",
        "streams_count": 2,      # Concurrent streaming tabs
        "min_buffer_behind": 0   # Apex leader (no cap)
    },
    {
        "rank": 2,
        "label": "🥈 Rank 2",
        "username": "pankaj_bideo",
        "phone": "9115233706",
        "password": "pankaj@5911",
        "user_id": "6ad9f679fb39968c7c37f8b5",
        "streams_count": 2,
        "min_buffer_behind": 200  # Must stay at least 200 coins below Rank 1
    },
    {
        "rank": 3,
        "label": "🥉 Rank 3",
        "username": "hariom_ai",
        "phone": "9648083419",
        "password": "hariom65",
        "user_id": "6ae80c2eff1a527964fd12b8",
        "streams_count": 2,
        "min_buffer_behind": 200  # Must stay at least 200 coins below Rank 2
    }
]

# ---------------------------------------------------------------------------
# 24-HOUR COIN MINING LIMIT & TOGGLE CONTROLLER
# ---------------------------------------------------------------------------
LIMITS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mining_limits.json")


class MiningLimitManager:
    _instance = None
    _lock = threading.RLock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self.file_path = LIMITS_FILE
        self.lock = threading.RLock()
        self.data = self._load()

    def _load(self):
        default_data = {
            "cryvex": {"enabled": True, "daily_limit": 100.0, "history": []},
            "pankaj_bideo": {"enabled": True, "daily_limit": 50.0, "history": []},
            "hariom_ai": {"enabled": True, "daily_limit": 50.0, "history": []}
        }
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    for k, v in default_data.items():
                        if k not in saved:
                            saved[k] = v
                        else:
                            saved[k].setdefault("enabled", v["enabled"])
                            saved[k].setdefault("daily_limit", v["daily_limit"])
                            saved[k].setdefault("history", [])
                    return saved
            except Exception as e:
                print(f"⚠️ [Limit Manager] Load error: {e}")
        return default_data

    def _save(self):
        try:
            temp_path = self.file_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            if os.path.exists(self.file_path):
                os.replace(temp_path, self.file_path)
            else:
                os.rename(temp_path, self.file_path)
        except Exception as e:
            print(f"⚠️ [Limit Manager] Save error: {e}")

    def prune_history(self):
        """Removes earnings older than 24 hours (86,400 seconds)."""
        now = time.time()
        cutoff = now - 86400
        changed = False
        for username, user_data in self.data.items():
            hist = user_data.get("history", [])
            new_hist = [h for h in hist if h.get("ts", 0) >= cutoff]
            if len(new_hist) != len(hist):
                user_data["history"] = new_hist
                changed = True
        if changed:
            self._save()

    def get_mined_last_24h(self, username):
        """Calculates total coins mined by this user in the rolling last 24h."""
        now = time.time()
        cutoff = now - 86400
        user_data = self.data.get(username, {})
        hist = user_data.get("history", [])
        return sum(float(h.get("amount", 0)) for h in hist if h.get("ts", 0) >= cutoff)

    def is_mining_allowed(self, username):
        """
        Returns (allowed: bool, status_msg: str, mined_24h: float, limit: float)
        """
        with self.lock:
            self.prune_history()
            user_data = self.data.get(username, {"enabled": True, "daily_limit": 100.0, "history": []})
            enabled = user_data.get("enabled", True)
            limit = float(user_data.get("daily_limit", 100.0))
            mined_24h = self.get_mined_last_24h(username)

            if not enabled:
                return False, "⏸️ Mining Disabled (OFF)", mined_24h, limit

            if limit > 0 and mined_24h >= limit:
                return False, f"⚠️ 24h Limit Reached ({mined_24h:.1f}/{limit:.1f})", mined_24h, limit

            return True, "🟢 Active", mined_24h, limit

    def record_earning(self, username, amount, coin_type="watch"):
        with self.lock:
            user_data = self.data.setdefault(username, {"enabled": True, "daily_limit": 100.0, "history": []})
            user_data.setdefault("history", []).append({
                "ts": time.time(),
                "amount": float(amount),
                "type": coin_type
            })
            self.prune_history()
            self._save()

    def update_config(self, username, enabled=None, daily_limit=None):
        with self.lock:
            user_data = self.data.setdefault(username, {"enabled": True, "daily_limit": 100.0, "history": []})
            if enabled is not None:
                user_data["enabled"] = bool(enabled)
            if daily_limit is not None:
                user_data["daily_limit"] = max(0.0, float(daily_limit))
            self._save()
            mined_24h = self.get_mined_last_24h(username)
            return {
                "username": username,
                "enabled": user_data["enabled"],
                "daily_limit": user_data["daily_limit"],
                "mined_24h": round(mined_24h, 1)
            }

    def get_all_limits(self):
        with self.lock:
            self.prune_history()
            res = {}
            for u in ["cryvex", "pankaj_bideo", "hariom_ai"]:
                user_data = self.data.get(u, {"enabled": True, "daily_limit": 100.0, "history": []})
                enabled = user_data.get("enabled", True)
                limit = float(user_data.get("daily_limit", 100.0))
                mined = round(self.get_mined_last_24h(u), 1)
                allowed, reason, _, _ = self.is_mining_allowed(u)
                res[u] = {
                    "enabled": enabled,
                    "daily_limit": limit,
                    "mined_24h": mined,
                    "remaining": max(0.0, round(limit - mined, 1)) if limit > 0 else 999999,
                    "status_text": reason,
                    "is_allowed": allowed
                }
            return res


class AccountSession:
    def __init__(self, config):
        self.config = config
        self.rank = config["rank"]
        self.label = config["label"]
        self.username = config["username"]
        self.phone = config["phone"]
        self.password = config["password"]
        self.user_id = config["user_id"]
        self.streams_count = config["streams_count"]
        self.min_buffer_behind = config["min_buffer_behind"]

        self.token = None
        self.coins = 0.0
        self.ads_watched = 0
        self.ads_remaining = 16
        self.ad_cooldown_until = 0

        self.session_coins_mined = 0.0
        self.watch_coins_mined = 0.0
        self.ad_coins_mined = 0.0
        self.status = "Initializing"
        self.lock = threading.Lock()

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT
        }

    def login(self):
        """Authenticates with Bideo API and retrieves fresh JWT token."""
        url = f"{BIDEO_API_BASE}/auth/login"
        payload = {"phone": self.phone, "password": self.password, "login": self.phone}
        headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=12)
            data = r.json()
            if r.ok and data.get("success"):
                with self.lock:
                    self.token = data.get("token")
                    user = data.get("user") or {}
                    self.user_id = user.get("_id") or self.user_id
                    self.username = user.get("name") or self.username
                    self.status = "Logged In"
                return True
            print(f"❌ [{self.label}] Login failed: {data.get('message')}")
            return False
        except Exception as e:
            print(f"❌ [{self.label}] Login exception: {e}")
            return False

    def refresh_coins_status(self):
        """Fetches live coins and ad status from /boost/status."""
        if not self.token:
            if not self.login():
                return
        try:
            r = requests.get(f"{BIDEO_API_BASE}/boost/status", headers=self.get_headers(), timeout=8)
            if r.status_code in (401, 403):
                # Token expired, auto-relogin
                if self.login():
                    r = requests.get(f"{BIDEO_API_BASE}/boost/status", headers=self.get_headers(), timeout=8)

            if r.ok:
                data = r.json().get("data", {})
                daily = data.get("dailyAds", {})
                with self.lock:
                    self.coins = float(data.get("coins", self.coins))
                    self.ads_watched = int(daily.get("watched", 0))
                    self.ads_remaining = int(daily.get("remaining", 16))
                    cd_secs = int(daily.get("cooldownSeconds", 0))
                    self.ad_cooldown_until = time.time() + cd_secs if cd_secs > 0 else 0
        except Exception:
            pass

    def claim_ad_reward(self):
        """Attempts to claim free daily ad reward (+2 coins)."""
        if not self.token:
            return False

        # Check if in cooldown or quota exhausted
        if self.ads_remaining <= 0:
            return False
        if time.time() < self.ad_cooldown_until:
            return False

        try:
            r = requests.post(f"{BIDEO_API_BASE}/boost/claim-ad-reward", headers=self.get_headers(), json={}, timeout=8)
            if r.status_code in (401, 403):
                self.login()
                r = requests.post(f"{BIDEO_API_BASE}/boost/claim-ad-reward", headers=self.get_headers(), json={}, timeout=8)

            if r.ok:
                data = r.json()
                if data.get("success"):
                    d = data.get("data", {})
                    reward = d.get("coinsEarned", 2)
                    new_total = float(d.get("totalCoins", self.coins + reward))
                    with self.lock:
                        self.coins = new_total
                        self.ads_watched = d.get("dailyWatched", self.ads_watched + 1)
                        self.ads_remaining = d.get("remainingDaily", max(0, self.ads_remaining - 1))
                        cd = d.get("cooldownSeconds", 0)
                        self.ad_cooldown_until = time.time() + cd if cd > 0 else 0
                        self.ad_coins_mined += reward
                        self.session_coins_mined += reward
                    return True
                else:
                    msg = data.get("message", "")
                    if "cooldown" in msg.lower() or "limit" in msg.lower():
                        self.ad_cooldown_until = time.time() + 300
            return False
        except Exception:
            return False

    def report_watch_time(self, vid_id, seconds=65):
        """
        Sends view and watch-time to Bideo API.
        If video is not self-owned and watchTime >= 60s, credits +1 Coin!
        """
        if not self.token:
            return False, 0

        headers = self.get_headers()
        try:
            # 1. Send View
            requests.post(f"{BIDEO_API_BASE}/videos/{vid_id}/view", headers=headers, json={}, timeout=6)

            # 2. Send Watch-Time
            r_wt = requests.post(
                f"{BIDEO_API_BASE}/videos/{vid_id}/watch-time",
                headers=headers,
                json={"watchTime": int(seconds)},
                timeout=8
            )
            if r_wt.status_code in (401, 403):
                self.login()
                headers = self.get_headers()
                r_wt = requests.post(
                    f"{BIDEO_API_BASE}/videos/{vid_id}/watch-time",
                    headers=headers,
                    json={"watchTime": int(seconds)},
                    timeout=8
                )

            if r_wt.ok:
                data = r_wt.json()
                earned = int(data.get("coinsEarned", 0))
                new_total = data.get("totalCoins")
                if earned > 0:
                    with self.lock:
                        if new_total is not None:
                            self.coins = float(new_total)
                        else:
                            self.coins += earned
                        self.watch_coins_mined += earned
                        self.session_coins_mined += earned
                    return True, earned
                return False, 0
            return False, 0
        except Exception:
            return False, 0


class PodiumMinerEngine:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self.accounts = [AccountSession(cfg) for cfg in PODIUM_CONFIG]
        self.limit_mgr = MiningLimitManager.get_instance()
        self.running = False
        self.video_catalog = []
        self.catalog_lock = threading.Lock()
        self.last_catalog_refresh = 0
        self.logs = deque(maxlen=40)
        self.log_lock = threading.Lock()

    def add_log(self, title, message, category="info"):
        now_str = datetime.now().strftime("%H:%M:%S")
        entry = {"time": now_str, "title": title, "message": message, "category": category}
        with self.log_lock:
            self.logs.appendleft(entry)

    def sync_podium_state(self):
        """Pushes current coin balances and recent logs to Firebase."""
        try:
            limits_map = self.limit_mgr.get_all_limits()
            payload = {
                "last_updated": datetime.now().isoformat(),
                "total_coins_podium": sum(a.coins for a in self.accounts),
                "recent_logs": list(self.logs),
                "limits": limits_map,
                "accounts": [
                    {
                        "rank": a.rank,
                        "label": a.label,
                        "username": a.username,
                        "phone": a.phone,
                        "coins": round(a.coins, 1),
                        "mined_this_run": round(a.session_coins_mined, 1),
                        "watch_coins": round(a.watch_coins_mined, 1),
                        "ad_coins": round(a.ad_coins_mined, 1),
                        "ads_watched": a.ads_watched,
                        "ads_remaining": a.ads_remaining,
                        "status": a.status,
                        "enabled": limits_map.get(a.username, {}).get("enabled", True),
                        "daily_limit": limits_map.get(a.username, {}).get("daily_limit", 100.0),
                        "mined_24h": limits_map.get(a.username, {}).get("mined_24h", 0.0),
                        "remaining_24h": limits_map.get(a.username, {}).get("remaining", 100.0),
                        "limit_status": limits_map.get(a.username, {}).get("status_text", "🟢 Active"),
                        "is_allowed": limits_map.get(a.username, {}).get("is_allowed", True)
                    }
                    for a in self.accounts
                ]
            }
            requests.put(FIREBASE_PODIUM_URL, json=payload, timeout=6)
        except Exception:
            pass

    def start_in_background(self):
        """Starts engine asynchronously in background thread."""
        t = threading.Thread(target=self.start, daemon=True)
        t.start()
        return t

    def refresh_public_videos(self):
        """Fetches fresh list of public non-self videos from feed."""
        now = time.time()
        if now - self.last_catalog_refresh < 180 and self.video_catalog:
            return

        try:
            url = f"{BIDEO_API_BASE}/videos?limit=40"
            headers = {"User-Agent": USER_AGENT}
            r = requests.get(url, headers=headers, timeout=8)
            if r.ok:
                data = r.json().get("data", [])
                clean_list = []
                for v in data:
                    vid_id = v.get("_id")
                    owner_id = (v.get("owner") or {}).get("_id")
                    title = v.get("title", "Video")
                    if vid_id and owner_id:
                        clean_list.append({"id": vid_id, "owner_id": owner_id, "title": title})

                if clean_list:
                    with self.catalog_lock:
                        self.video_catalog = clean_list
                        self.last_catalog_refresh = now
        except Exception:
            pass

    def get_target_video(self, account_user_id):
        """Picks a random video not owned by this account."""
        self.refresh_public_videos()
        with self.catalog_lock:
            candidates = [v for v in self.video_catalog if v["owner_id"] != account_user_id]
            if candidates:
                return random.choice(candidates)
        return None

    def _ad_claim_worker(self, acc: AccountSession):
        """Periodically checks and claims daily ad rewards for this account."""
        # Initial status fetch
        acc.refresh_coins_status()
        time.sleep(random.randint(2, 6))

        while self.running:
            try:
                # 24h Coin Mining Limit & Toggle Check
                allowed, reason, _, _ = self.limit_mgr.is_mining_allowed(acc.username)
                if not allowed:
                    time.sleep(15)
                    continue

                acc.refresh_coins_status()
                if acc.ads_remaining > 0 and time.time() >= acc.ad_cooldown_until:
                    claimed = acc.claim_ad_reward()
                    if claimed:
                        self.limit_mgr.record_earning(acc.username, 2.0, "ad")
                        now_str = datetime.now().strftime("%H:%M:%S")
                        print(f"{CLR_GOLD}[{now_str}] 🎁 [AD REWARD] {acc.label} ({acc.username}) Claimed +2.0 Coins ──► Balance: {acc.coins:.1f} Coins (Ads Left: {acc.ads_remaining}/16){CLR_RESET}")
                        self.add_log(f"🎁 AD REWARD [{acc.label}]", f"Claimed +2.0 Coins (Balance: {acc.coins:.1f} | Ads Left: {acc.ads_remaining}/16)", "coin-reward")
                        self.sync_podium_state()
                        time.sleep(random.randint(8, 15))
                        continue

                # Sleep check interval
                time.sleep(25)
            except Exception:
                time.sleep(15)

    def _streaming_watch_worker(self, acc: AccountSession, stream_id: int):
        """Simulates 1 continuous video stream for this account."""
        # Stagger initial stream starts
        time.sleep((acc.rank * 4) + (stream_id * 8))

        while self.running:
            try:
                # 24h Coin Mining Limit & Toggle Check
                allowed, reason, mined_24h, limit = self.limit_mgr.is_mining_allowed(acc.username)
                if not allowed:
                    acc.status = reason
                    time.sleep(10)
                    continue

                # Hierarchy Safety Check:
                # Rank 2 must never overtake Rank 1 (Cryvex stays apex)
                # Rank 3 must never overtake Rank 2 (Pankaj stays #2)
                if acc.rank == 2:
                    rank1_acc = self.accounts[0]
                    if acc.coins >= (rank1_acc.coins - 50):
                        acc.status = "Pacing (Holding #2 behind Rank 1)"
                        time.sleep(15)
                        continue
                elif acc.rank == 3:
                    rank2_acc = self.accounts[1]
                    if acc.coins >= rank2_acc.coins:
                        acc.status = "Pacing (Holding #3 behind Rank 2)"
                        time.sleep(15)
                        continue

                acc.status = f"Streaming #{stream_id} ({mined_24h:.0f}/{limit:.0f} 24h)"

                target = self.get_target_video(acc.user_id)
                if not target:
                    time.sleep(10)
                    continue

                # Watch time between 62 and 68 seconds to guarantee +1 Coin credit
                watch_duration = random.randint(62, 68)

                # Simulate real-time watching
                slept = 0
                while slept < watch_duration and self.running:
                    time.sleep(2)
                    slept += 2

                if not self.running:
                    break

                # Submit watch time
                success, earned = acc.report_watch_time(target["id"], watch_duration)
                if success and earned > 0:
                    self.limit_mgr.record_earning(acc.username, earned, "watch")
                    now_str = datetime.now().strftime("%H:%M:%S")
                    print(f"{CLR_GREEN}[{now_str}] 🪙 [COIN MINED] {acc.label} [S{stream_id}] ({acc.username}) Watched '{target['title'][:22]}...' ({watch_duration}s) ──► +{earned}.0 Coin | Total: {acc.coins:.1f}{CLR_RESET}")
                    self.add_log(f"🪙 COIN MINED [{acc.label}]", f"[Stream #{stream_id}] Watched '{target['title'][:22]}...' ({watch_duration}s) ──► +{earned}.0 Coin | Vault: {acc.coins:.1f}", "coin-reward")
                    self.sync_podium_state()

                # Short realistic human gap between videos (3 to 7 seconds)
                time.sleep(random.randint(3, 7))

            except Exception as e:
                time.sleep(10)

    def start(self):
        """Starts multi-stream mining engine for all 3 podium accounts."""
        self.running = True
        print("\n" + "=" * 75)
        print("🚀 BIDEO PODIUM COIN MINER - STARTING MULTI-STREAM ENGINE")
        print("=" * 75)

        # 1. Login all accounts
        for acc in self.accounts:
            print(f"Logging in {acc.label} ({acc.phone})...")
            if acc.login():
                acc.refresh_coins_status()
                print(f"✅ Logged In: {acc.username} | Coins: {acc.coins} | Ads Remaining: {acc.ads_remaining}/16")
            else:
                print(f"❌ Failed to login {acc.label} ({acc.phone})")

        self.sync_podium_state()
        print("=" * 75)

        # 2. Launch Ad Claim workers (1 per account)
        for acc in self.accounts:
            t_ad = threading.Thread(target=self._ad_claim_worker, args=(acc,), daemon=True)
            t_ad.start()

        # 3. Launch Video Streaming workers (multi-stream per account)
        for acc in self.accounts:
            for s_id in range(1, acc.streams_count + 1):
                t_stream = threading.Thread(target=self._streaming_watch_worker, args=(acc, s_id), daemon=True)
                t_stream.start()

        print("⚡ ALL MINING STREAMS ACTIVE & RUNNING 24/7!")
        print("=" * 75 + "\n")

        # 4. Main monitoring dashboard loop & Firebase live state sync
        try:
            while self.running:
                self.sync_podium_state()

                time.sleep(25)
                now_str = datetime.now().strftime("%H:%M:%S")
                print("\n" + CLR_CYAN + "═" * 75 + CLR_RESET)
                print(f"{CLR_BOLD}📊 [PODIUM LIVE STATUS @ {now_str}]{CLR_RESET}")
                for acc in self.accounts:
                    color = CLR_GOLD if acc.rank == 1 else (CLR_CYAN if acc.rank == 2 else CLR_PURPLE)
                    print(f"   {color}{acc.label} ({acc.username}){CLR_RESET}: Balance = {CLR_BOLD}{acc.coins:.1f} Coins{CLR_RESET} | Mined = {CLR_GREEN}+{acc.session_coins_mined:.1f}{CLR_RESET} (Watch: {acc.watch_coins_mined:.0f}, Ads: {acc.ad_coins_mined:.0f}) | Ads Left: {acc.ads_remaining}/16")
                print(CLR_CYAN + "═" * 75 + CLR_RESET + "\n")
        except KeyboardInterrupt:
            print("\n🛑 Stopping Podium Coin Miner cleanly...")
            self.running = False


if __name__ == "__main__":
    engine = PodiumMinerEngine()
    engine.start()
