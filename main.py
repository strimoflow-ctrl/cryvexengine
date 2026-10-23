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

if __name__ == "__main__":
    AutoCoinMiner.get_instance().start()
    AutonomousFarmEngine.get_instance().start()

    port = int(os.environ.get("SERVER_PORT") or os.environ.get("PORT") or 5050)
    print("==================================================")
    print(">>> BIDEO 24/7 AUTONOMOUS BOT FARMING ACTIVE")
    print(f">>> Listening on: 0.0.0.0:{port}")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
