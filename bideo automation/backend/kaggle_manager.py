import os
import re
import json
import time
import base64
import threading
import requests
from datetime import datetime

FIREBASE_DB_URL = os.environ.get(
    "FIREBASE_DB_URL",
    "https://secret-gpt-default-rtdb.asia-southeast1.firebasedatabase.app"
).rstrip("/")
FIREBASE_ROOT = "bideo_automation"


class KaggleManager:
    """
    Manages 24/7 Autonomous Kaggle Cloud Worker Sessions for Bideo Automation.
    Automates 11.5-hour cancellation, renewal, and notebook compilation.
    """

    _supervisor_thread = None
    _supervisor_running = False

    @classmethod
    def get_config(cls):
        """Fetches Kaggle credentials and auto-renew settings from Firebase."""
        try:
            url = f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/kaggle_config.json"
            r = requests.get(url, timeout=5)
            return r.json() or {}
        except Exception:
            return {}

    @classmethod
    def save_config(cls, data):
        """Saves Kaggle credentials and settings to Firebase."""
        try:
            url = f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/kaggle_config.json"
            r = requests.put(url, json=data, timeout=5)
            return r.ok
        except Exception:
            return False

    @classmethod
    def get_status(cls):
        """Fetches live Kaggle engine status from Firebase."""
        try:
            url = f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/kaggle_status.json"
            r = requests.get(url, timeout=5)
            return r.json() or {}
        except Exception:
            return {}

    @classmethod
    def compile_notebook_json(cls):
        """
        Reads kaggle_cells (cell1_setup.py, cell2_engine.py)
        Injects cookies and Firebase configuration.
        Returns Jupyter Notebook JSON string ready for Kaggle API push.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cells_dir = os.path.join(base_dir, "kaggle_cells")

        cell1_path = os.path.join(cells_dir, "cell1_setup.py")
        cell2_path = os.path.join(cells_dir, "cell2_engine.py")

        cells = []

        # Read Cell 1 (Dependencies & Deno)
        if os.path.exists(cell1_path):
            with open(cell1_path, "r", encoding="utf-8") as f:
                c1_content = f.read()
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": c1_content.splitlines(keepends=True)
            })

        # Inject cookies if available
        cookie_path = os.path.join(base_dir, "cookies.txt")
        if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 10:
            with open(cookie_path, "rb") as f:
                c_b64 = base64.b64encode(f.read()).decode("utf-8")
            cookie_injection = (
                "import base64\n"
                f"with open('cookies.txt', 'wb') as f:\n"
                f"    f.write(base64.b64decode('{c_b64}'))\n"
                "print('🍪 [Kaggle Bideo Engine] Loaded YouTube Cookies!')\n"
            )
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": cookie_injection.splitlines(keepends=True)
            })

        # Read Cell 2 (Autonomous Mega Engine)
        if os.path.exists(cell2_path):
            with open(cell2_path, "r", encoding="utf-8") as f:
                c2_content = f.read()

            # Ensure Firebase URL is dynamically injected
            inject_header = (
                f"FIREBASE_DB_URL = \"{FIREBASE_DB_URL}\"\n"
                f"FIREBASE_ROOT = \"{FIREBASE_ROOT}\"\n"
            )
            c2_content = re.sub(
                r'FIREBASE_DB_URL\s*=\s*".*?"',
                f'FIREBASE_DB_URL = "{FIREBASE_DB_URL}"',
                c2_content
            )

            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": c2_content.splitlines(keepends=True)
            })

        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 2
        }
        return json.dumps(notebook)

    @classmethod
    def push_kernel(cls, kaggle_user, kaggle_key, kaggle_slug="bideo-automation-engine"):
        """Pushes compiled notebook to Kaggle API to launch execution."""
        notebook_code = cls.compile_notebook_json()
        credentials = base64.b64encode(f"{kaggle_user}:{kaggle_key}".encode()).decode("utf-8")
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }

        full_slug = f"{kaggle_user}/{kaggle_slug}"
        payload = {
            "id": None,
            "slug": full_slug,
            "title": kaggle_slug.replace("-", " ").title(),
            "text": notebook_code,
            "language": "python",
            "kernelType": "notebook",
            "isPrivate": True,
            "enableGpu": False,
            "enableInternet": True,
            "datasetSources": [],
            "competitionSources": [],
            "kernelSources": []
        }

        url = "https://www.kaggle.com/api/v1/kernels/push"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=35)
            if resp.status_code == 200:
                print(f"[Kaggle Manager] Kernel '{full_slug}' launched successfully!")
                return True, "Kaggle Job Launched Successfully!"
            else:
                err = resp.text
                print(f"[Kaggle Manager] Push failed ({resp.status_code}): {err}")
                return False, err
        except Exception as e:
            return False, str(e)

    @classmethod
    def cancel_kernel(cls, kaggle_user, kaggle_key, kaggle_slug="bideo-automation-engine"):
        """Stops/cancels a running Kaggle kernel."""
        credentials = base64.b64encode(f"{kaggle_user}:{kaggle_key}".encode()).decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        url = f"https://www.kaggle.com/api/v1/kernels/cancel?userName={kaggle_user}&kernelSlug={kaggle_slug}"
        try:
            r = requests.post(url, headers=headers, timeout=20)
            return r.status_code in [200, 204]
        except Exception:
            return False

    @classmethod
    def start_supervisor(cls):
        """Starts background 24/7 Kaggle session renew supervisor thread."""
        if cls._supervisor_running:
            return

        cls._supervisor_running = True

        def _supervisor_loop():
            print("🛡️ [Kaggle Supervisor] 24/7 Autonomous Renewal Monitor Started.")
            while cls._supervisor_running:
                try:
                    config = cls.get_config()
                    kaggle_user = config.get("kaggle_user")
                    kaggle_key = config.get("kaggle_key")
                    kaggle_slug = config.get("kaggle_slug", "bideo-automation-engine")
                    auto_renew = config.get("auto_renew", True)

                    if kaggle_user and kaggle_key and auto_renew:
                        status = cls.get_status()
                        is_running = status.get("is_running", False)
                        last_hb = status.get("last_heartbeat", 0)
                        state = status.get("state", "")
                        now = time.time()

                        # Conditions for renewal:
                        # 1. State marked "renew_ready" (11.5 hours completed gracefully)
                        # 2. Kernel stopped running or heartbeat dead for > 150 seconds
                        hb_dead = (now - last_hb > 150) if last_hb > 0 else True
                        should_renew = (not is_running) or (state == "renew_ready") or hb_dead

                        if should_renew:
                            print("[Kaggle Supervisor] Session renewal triggered! Cancelling old session...")
                            cls.cancel_kernel(kaggle_user, kaggle_key, kaggle_slug)
                            time.sleep(8)
                            print("[Kaggle Supervisor] Launching fresh 11.5-hour Kaggle session...")
                            ok, msg = cls.push_kernel(kaggle_user, kaggle_key, kaggle_slug)
                            if ok:
                                # Update status in Firebase
                                try:
                                    requests.put(
                                        f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/kaggle_status.json",
                                        json={
                                            "is_running": True,
                                            "state": "launching",
                                            "launched_at": datetime.now().isoformat(),
                                            "last_heartbeat": time.time(),
                                            "current_task": "Booting fresh 11.5h Kaggle worker..."
                                        },
                                        timeout=5
                                    )
                                except Exception:
                                    pass
                except Exception as ex:
                    print(f"[Kaggle Supervisor Notice] {ex}")

                # Check every 45 seconds
                time.sleep(45)

        cls._supervisor_thread = threading.Thread(target=_supervisor_loop, daemon=True)
        cls._supervisor_thread.start()
