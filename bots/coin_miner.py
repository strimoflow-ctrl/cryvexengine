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
import random
import threading
from datetime import datetime
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
    def __init__(self):
        self.accounts = [AccountSession(cfg) for cfg in PODIUM_CONFIG]
        self.running = False
        self.video_catalog = []
        self.catalog_lock = threading.Lock()
        self.last_catalog_refresh = 0

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
                acc.refresh_coins_status()
                if acc.ads_remaining > 0 and time.time() >= acc.ad_cooldown_until:
                    claimed = acc.claim_ad_reward()
                    if claimed:
                        now_str = datetime.now().strftime("%H:%M:%S")
                        print(f"[{now_str}] 🎁 {acc.label} ({acc.username}): Claimed Ad (+2 Coins) -> Total: {acc.coins:.1f}")
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

                acc.status = f"Streaming #{stream_id}"

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
                    now_str = datetime.now().strftime("%H:%M:%S")
                    print(f"[{now_str}] 🪙 {acc.label} [S{stream_id}] ({acc.username}): Watched '{target['title'][:22]}...' ({watch_duration}s) -> +{earned} Coin (Total: {acc.coins:.1f})")

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

        # 4. Main monitoring dashboard loop
        try:
            while self.running:
                time.sleep(30)
                now_str = datetime.now().strftime("%H:%M:%S")
                print("\n" + "-" * 75)
                print(f"📊 [PODIUM LIVE STATUS @ {now_str}]")
                for acc in self.accounts:
                    print(f"   {acc.label} ({acc.username}): Balance = {acc.coins:.1f} Coins | Mined This Run = +{acc.session_coins_mined:.1f} (Watch: {acc.watch_coins_mined:.0f}, Ads: {acc.ad_coins_mined:.0f}) | Ads Left: {acc.ads_remaining}/16")
                print("-" * 75 + "\n")
        except KeyboardInterrupt:
            print("\n🛑 Stopping Podium Coin Miner cleanly...")
            self.running = False


if __name__ == "__main__":
    engine = PodiumMinerEngine()
    engine.start()
