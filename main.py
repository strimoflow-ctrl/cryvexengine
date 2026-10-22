import os
import sys
import subprocess

# Determine directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "bideo automation", "backend")

# If requirements.txt is present, ensure dependencies are installed
req_file = os.path.join(BACKEND_DIR, "requirements.txt")
if not os.path.exists(req_file):
    req_file = os.path.join(BASE_DIR, "requirements.txt")

if os.path.exists(req_file):
    try:
        import flask
        import yt_dlp
        import imageio_ffmpeg
        import requests
    except ImportError:
        print(">>> [Botkeep Boot] Installing Python dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r", req_file], check=True)

# Add backend directory to path and switch cwd
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app import app

if __name__ == "__main__":
    # Botkeep or cloud port
    port = int(os.environ.get("PORT", 5000))
    print("==================================================")
    print(">>> BIDEO 24/7 AUTOMATION ENGINE ACTIVE (BOTKEEP)")
    print(f">>> Listening on: 0.0.0.0:{port}")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
