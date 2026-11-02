import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOTS_DIR = os.path.join(BASE_DIR, "bots")

req_file = os.path.join(BASE_DIR, "requirements.txt")
if os.path.exists(req_file):
    try:
        import flask
        import flask_cors
        import requests
    except ImportError:
        print(">>> [Cloud Boot] Installing Python dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r", req_file], check=True)

sys.path.insert(0, BOTS_DIR)
os.chdir(BOTS_DIR)

from server import app, AutoCoinMiner, AutonomousFarmEngine
from coin_miner import PodiumMinerEngine

if __name__ == "__main__":
    # 1. Start Cryvex Auto Coin Miner (Ad claimer)
    AutoCoinMiner.get_instance().start()

    # 2. Start 24/7 Multi-Stream Podium Miner (🥇 Cryvex | 🥈 Pankaj | 🥉 Hariom)
    try:
        PodiumMinerEngine.get_instance().start_in_background()
        print("🏆 [PODIUM MINER] 24/7 Multi-Stream Coin Mining Engine started for Rank 1, 2, 3!")
    except Exception as e:
        print(f"⚠️ [PODIUM MINER] Failed to start: {e}")

    # 3. Start 24/7 Autonomous Farm Engine (anti-rush organic views/likes)
    AutonomousFarmEngine.get_instance().start()

    port = int(os.environ.get("SERVER_PORT") or os.environ.get("PORT") or 5050)
    print("==================================================")
    print(">>> BIDEO 24/7 AUTONOMOUS COIN & PODIUM ENGINE ACTIVE")
    print(f">>> Listening on: 0.0.0.0:{port}")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
