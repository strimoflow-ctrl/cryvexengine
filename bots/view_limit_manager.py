import os
import sys
import json
import time
import threading
from datetime import datetime

LIMITS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "view_limits.json")
DEFAULT_CRYVEX_CHANNEL_ID = "6ada0b9dfb39968c7c48dd7b"
DEFAULT_CRYVEX_USERNAME = "cryvex"
DEFAULT_CRYVEX_AVATAR = "https://pub-39d197c890b64644a9a1869b8f6740b1.r2.dev/images/1792711625547-612508265.jpg"


class ViewLimitManager:
    """
    Thread-Safe 24-Hour Rolling Limit & Multi-Channel View Automation Manager
    ------------------------------------------------------------------------
    - Master Global 24H View Budget & Global ON/OFF Switch.
    - Manages per-channel daily view targets and ON/OFF switches.
    - Rolling 24-hour window (86,400s) with automatic timestamp pruning.
    - Dynamically balances views across all registered channels.
    - When 24h limit is reached, signals farming engine to execute stealth browsing or sleep in standby.
    """
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

    def _get_default_data(self):
        return {
            "_global": {
                "enabled": True,
                "daily_limit": 100,
                "stealth_history": []
            },
            DEFAULT_CRYVEX_CHANNEL_ID: {
                "channel_id": DEFAULT_CRYVEX_CHANNEL_ID,
                "name": "cryvex",
                "username": DEFAULT_CRYVEX_USERNAME,
                "avatar": DEFAULT_CRYVEX_AVATAR,
                "enabled": True,
                "daily_limit": 200,
                "history": []
            }
        }

    def _load(self):
        defaults = self._get_default_data()
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        # Ensure _global is present
                        if "_global" not in saved:
                            saved["_global"] = defaults["_global"]
                        else:
                            saved["_global"].setdefault("enabled", True)
                            saved["_global"].setdefault("daily_limit", 100)
                            saved["_global"].setdefault("stealth_history", [])

                        # Ensure default cryvex channel is present
                        if DEFAULT_CRYVEX_CHANNEL_ID not in saved:
                            saved[DEFAULT_CRYVEX_CHANNEL_ID] = defaults[DEFAULT_CRYVEX_CHANNEL_ID]
                        else:
                            c = saved[DEFAULT_CRYVEX_CHANNEL_ID]
                            c.setdefault("channel_id", DEFAULT_CRYVEX_CHANNEL_ID)
                            c.setdefault("name", "cryvex")
                            c.setdefault("username", DEFAULT_CRYVEX_USERNAME)
                            c.setdefault("avatar", DEFAULT_CRYVEX_AVATAR)
                            c.setdefault("enabled", True)
                            c.setdefault("daily_limit", 200)
                            c.setdefault("history", [])

                        # Ensure other channels have required keys
                        for k, v in saved.items():
                            if k == "_global":
                                continue
                            if isinstance(v, dict):
                                v.setdefault("channel_id", k)
                                v.setdefault("enabled", True)
                                v.setdefault("daily_limit", 200)
                                v.setdefault("history", [])
                        return saved
            except Exception as e:
                print(f"⚠️ [ViewLimitManager] Load error: {e}")
        return defaults

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
            print(f"⚠️ [ViewLimitManager] Save error: {e}")

    def prune_history(self):
        """Removes view events older than rolling 24 hours (86,400 seconds)."""
        now = time.time()
        cutoff = now - 86400
        changed = False

        # Prune global stealth views
        g = self.data.setdefault("_global", {"enabled": True, "daily_limit": 100, "stealth_history": []})
        st_hist = g.get("stealth_history", [])
        new_st_hist = [h for h in st_hist if h.get("ts", 0) >= cutoff]
        if len(new_st_hist) != len(st_hist):
            g["stealth_history"] = new_st_hist
            changed = True

        # Prune channel views
        for channel_id, ch_data in self.data.items():
            if channel_id == "_global" or not isinstance(ch_data, dict):
                continue
            hist = ch_data.get("history", [])
            new_hist = [h for h in hist if h.get("ts", 0) >= cutoff]
            if len(new_hist) != len(hist):
                ch_data["history"] = new_hist
                changed = True

        if changed:
            self._save()

    # -------------------------------------------------------------
    # Global Limit & Master Switch Methods
    # -------------------------------------------------------------
    def is_global_enabled(self):
        """Returns True if the master view engine is switched ON."""
        with self.lock:
            g = self.data.get("_global", {})
            return g.get("enabled", True)

    def get_global_limit(self):
        """Returns master 24h view budget."""
        with self.lock:
            g = self.data.get("_global", {})
            return int(g.get("daily_limit", 100))

    def get_stealth_views_24h(self):
        """Returns stealth views delivered in the last 24h."""
        now = time.time()
        cutoff = now - 86400
        g = self.data.get("_global", {})
        st_hist = g.get("stealth_history", [])
        return sum(1 for h in st_hist if h.get("ts", 0) >= cutoff)

    def get_total_channel_views_24h(self):
        """Returns sum of all views delivered across all target channels in last 24h."""
        now = time.time()
        cutoff = now - 86400
        total = 0
        for k, v in self.data.items():
            if k == "_global" or not isinstance(v, dict):
                continue
            hist = v.get("history", [])
            total += sum(1 for h in hist if h.get("ts", 0) >= cutoff)
        return total

    def get_total_views_24h(self):
        """Total views delivered across all channels AND stealth in rolling 24h."""
        return self.get_total_channel_views_24h() + self.get_stealth_views_24h()

    def is_viewing_allowed_globally(self):
        """
        Master check: Can the view engine perform ANY views (target or stealth)?
        Returns: (allowed: bool, status_msg: str, total_views: int, global_limit: int)
        """
        with self.lock:
            self.data = self._load()
            self.prune_history()

            g = self.data.setdefault("_global", {"enabled": True, "daily_limit": 100, "stealth_history": []})
            enabled = g.get("enabled", True)
            limit = int(g.get("daily_limit", 100))
            total_views = self.get_total_views_24h()

            if not enabled:
                return False, "⏸️ Master View Engine Paused (OFF)", total_views, limit

            if limit > 0 and total_views >= limit:
                return False, f"⚠️ 24H Global Budget Completed ({total_views}/{limit})", total_views, limit

            return True, f"🟢 Global Engine Active ({total_views}/{limit})", total_views, limit

    def update_global_config(self, enabled=None, daily_limit=None):
        """Updates master view switch and/or global 24h budget."""
        with self.lock:
            self.data = self._load()
            g = self.data.setdefault("_global", {"enabled": True, "daily_limit": 100, "stealth_history": []})

            if enabled is not None:
                g["enabled"] = bool(enabled)
            if daily_limit is not None:
                g["daily_limit"] = max(0, int(daily_limit))

            self._save()
            total_views = self.get_total_views_24h()
            limit = g["daily_limit"]
            pct = min(100, int((total_views / limit) * 100)) if limit > 0 else 100

            return {
                "enabled": g["enabled"],
                "daily_limit": g["daily_limit"],
                "total_views_24h": total_views,
                "progress_pct": pct
            }

    def record_stealth_view(self, video_id="", creator=""):
        """Records an organic stealth view under _global history."""
        with self.lock:
            self.data = self._load()
            g = self.data.setdefault("_global", {"enabled": True, "daily_limit": 100, "stealth_history": []})
            g.setdefault("stealth_history", []).append({
                "ts": time.time(),
                "video_id": video_id,
                "creator": creator[:40] if creator else ""
            })
            self.prune_history()
            self._save()

    # -------------------------------------------------------------
    # Per-Channel View Management Methods
    # -------------------------------------------------------------
    def get_views_last_24h(self, channel_id):
        """Calculates views delivered to this specific channel in the rolling last 24h."""
        now = time.time()
        cutoff = now - 86400
        ch_data = self.data.get(channel_id, {})
        hist = ch_data.get("history", [])
        return sum(1 for h in hist if h.get("ts", 0) >= cutoff)

    def is_viewing_allowed(self, channel_id):
        """
        Checks if views can be delivered to this specific channel.
        Returns: (allowed: bool, status_msg: str, views_24h: int, limit: int)
        """
        with self.lock:
            self.data = self._load()
            self.prune_history()

            # First check global master switch
            if not self.is_global_enabled():
                return False, "⏸️ Global View Engine Paused", self.get_views_last_24h(channel_id), 0

            # Check global limit
            g_limit = self.get_global_limit()
            total_views = self.get_total_views_24h()
            if g_limit > 0 and total_views >= g_limit:
                return False, f"⚠️ Global 24H Limit Reached ({total_views}/{g_limit})", self.get_views_last_24h(channel_id), 0

            ch_data = self.data.get(channel_id)
            if not ch_data or channel_id == "_global":
                return False, "Channel not found", 0, 0

            enabled = ch_data.get("enabled", True)
            limit = int(ch_data.get("daily_limit", 200))
            views_24h = self.get_views_last_24h(channel_id)

            if not enabled:
                return False, "⏸️ Views Paused (OFF)", views_24h, limit

            if limit > 0 and views_24h >= limit:
                return False, f"⚠️ 24h Target Completed ({views_24h}/{limit})", views_24h, limit

            return True, f"🟢 Active ({views_24h}/{limit})", views_24h, limit

    def record_view(self, channel_id, video_id, title=""):
        """Records a successful view delivered to a video under this channel."""
        with self.lock:
            self.data = self._load()
            if channel_id not in self.data or channel_id == "_global":
                channel_id = DEFAULT_CRYVEX_CHANNEL_ID

            ch_data = self.data.setdefault(channel_id, {
                "channel_id": channel_id,
                "name": channel_id,
                "username": channel_id,
                "avatar": "",
                "enabled": True,
                "daily_limit": 200,
                "history": []
            })
            ch_data.setdefault("history", []).append({
                "ts": time.time(),
                "video_id": video_id,
                "title": title[:60] if title else ""
            })
            self.prune_history()
            self._save()

    def get_eligible_channels(self):
        """
        Returns list of channel dicts that are currently ENABLED and have NOT reached their 24h limit.
        Returns empty list if global master switch is OFF or global limit is reached.
        """
        with self.lock:
            self.data = self._load()
            self.prune_history()

            # If global switch is OFF or global limit reached, no channels are eligible
            g_allowed, _, _, _ = self.is_viewing_allowed_globally()
            if not g_allowed:
                return []

            eligible = []
            for ch_id, ch_data in self.data.items():
                if ch_id == "_global" or not isinstance(ch_data, dict):
                    continue
                if not ch_data.get("enabled", True):
                    continue

                limit = int(ch_data.get("daily_limit", 200))
                views_24h = self.get_views_last_24h(ch_id)

                if limit > 0 and views_24h >= limit:
                    continue  # Target met!

                pct = (views_24h / limit) if limit > 0 else 0.0
                eligible.append({
                    "channel_id": ch_id,
                    "name": ch_data.get("name") or ch_data.get("username") or ch_id,
                    "username": ch_data.get("username") or ch_id,
                    "avatar": ch_data.get("avatar", ""),
                    "daily_limit": limit,
                    "views_24h": views_24h,
                    "completion_pct": pct
                })

            # Sort by lowest completion percentage so all channels get balanced views
            eligible.sort(key=lambda x: x["completion_pct"])
            return eligible

    def add_channel(self, identifier, daily_limit=200):
        """Adds a channel to the views manager using identifier (Channel ID or Username/Handle)."""
        with self.lock:
            self.data = self._load()

            from bot_engine import BotEngine
            resolved_id, resolved_name = BotEngine.resolve_channel_id(identifier)
            if not resolved_id or resolved_id == "_global":
                return False, "Channel resolution failed"

            daily_limit = max(0, int(daily_limit))

            avatar_url = ""
            try:
                results = BotEngine.search_channels(resolved_name)
                for r in results:
                    if r.get("_id") == resolved_id:
                        avatar_url = r.get("avatar") or r.get("photo") or ""
                        break
            except Exception:
                pass

            if not avatar_url and resolved_id == DEFAULT_CRYVEX_CHANNEL_ID:
                avatar_url = DEFAULT_CRYVEX_AVATAR

            if resolved_id in self.data:
                self.data[resolved_id]["daily_limit"] = daily_limit
                self.data[resolved_id]["enabled"] = True
                if avatar_url:
                    self.data[resolved_id]["avatar"] = avatar_url
                self._save()
                return True, f"Channel '{resolved_name}' updated with 24h limit of {daily_limit} views!"

            self.data[resolved_id] = {
                "channel_id": resolved_id,
                "name": resolved_name,
                "username": resolved_name,
                "avatar": avatar_url,
                "enabled": True,
                "daily_limit": daily_limit,
                "history": []
            }
            self._save()
            return True, f"Channel '{resolved_name}' added with 24h limit of {daily_limit} views!"

    def remove_channel(self, channel_id):
        """Removes a channel from views management."""
        with self.lock:
            self.data = self._load()
            if channel_id in (DEFAULT_CRYVEX_CHANNEL_ID, "_global"):
                return False, "Cannot delete master channel (you can pause it instead)!"

            if channel_id in self.data:
                removed_name = self.data[channel_id].get("name", channel_id)
                del self.data[channel_id]
                self._save()
                return True, f"Channel '{removed_name}' removed from automation!"
            return False, "Channel not found in active list"

    def update_channel(self, channel_id, enabled=None, daily_limit=None):
        """Updates channel limit or enabled status."""
        with self.lock:
            self.data = self._load()
            if channel_id == "_global":
                return True, self.update_global_config(enabled=enabled, daily_limit=daily_limit)

            if channel_id not in self.data:
                return False, "Channel not found"

            ch = self.data[channel_id]
            if enabled is not None:
                ch["enabled"] = bool(enabled)
            if daily_limit is not None:
                ch["daily_limit"] = max(0, int(daily_limit))

            self._save()
            views_24h = self.get_views_last_24h(channel_id)
            return True, {
                "channel_id": channel_id,
                "name": ch.get("name"),
                "enabled": ch["enabled"],
                "daily_limit": ch["daily_limit"],
                "views_24h": views_24h
            }

    def get_all_channels_summary(self):
        """Returns comprehensive summary of global settings and all managed channels."""
        with self.lock:
            self.data = self._load()
            self.prune_history()

            summary_list = []
            active_count = 0

            for ch_id, ch_data in self.data.items():
                if ch_id == "_global" or not isinstance(ch_data, dict):
                    continue

                views_24h = self.get_views_last_24h(ch_id)
                limit = int(ch_data.get("daily_limit", 200))
                enabled = ch_data.get("enabled", True)

                if enabled:
                    active_count += 1

                allowed, status_msg, _, _ = self.is_viewing_allowed(ch_id)
                pct = min(100, int((views_24h / limit) * 100)) if limit > 0 else 100

                summary_list.append({
                    "channel_id": ch_id,
                    "name": ch_data.get("name") or ch_data.get("username") or ch_id,
                    "username": ch_data.get("username") or ch_id,
                    "avatar": ch_data.get("avatar") or "",
                    "enabled": enabled,
                    "daily_limit": limit,
                    "views_24h": views_24h,
                    "progress_pct": pct,
                    "is_allowed": allowed,
                    "status_text": status_msg
                })

            summary_list.sort(key=lambda x: (0 if x["channel_id"] == DEFAULT_CRYVEX_CHANNEL_ID else 1, x["name"].lower()))

            # Global metrics
            g = self.data.setdefault("_global", {"enabled": True, "daily_limit": 100, "stealth_history": []})
            g_enabled = g.get("enabled", True)
            g_limit = int(g.get("daily_limit", 100))
            ch_views = self.get_total_channel_views_24h()
            st_views = self.get_stealth_views_24h()
            total_views = ch_views + st_views
            g_pct = min(100, int((total_views / g_limit) * 100)) if g_limit > 0 else 100
            g_allowed, g_status_msg, _, _ = self.is_viewing_allowed_globally()

            return {
                "channels": summary_list,
                "total_channels": len(summary_list),
                "active_channels": active_count,
                "total_views_24h": total_views,
                "channel_views_24h": ch_views,
                "stealth_views_24h": st_views,
                "global_enabled": g_enabled,
                "global_daily_limit": g_limit,
                "global_progress_pct": g_pct,
                "global_is_allowed": g_allowed,
                "global_status_text": g_status_msg
            }
