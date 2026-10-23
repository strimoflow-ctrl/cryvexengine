# Cell 1: Setup & Dependencies
import os
import subprocess

print("🚀 [Kaggle Bideo Engine] Installing Deno JS runtime, FFmpeg, and yt-dlp dependencies...")

# 1. Install FFmpeg, fonts, curl, and unzip
os.system("apt-get update -y -qq && apt-get install -y -qq ffmpeg curl unzip fonts-dejavu-core fontconfig")

# 2. Install Deno JS runtime (YouTube signature decipher requirement)
os.system("curl -fsSL https://deno.land/install.sh | sh")
os.system("if [ -f \"$HOME/.deno/bin/deno\" ]; then cp $HOME/.deno/bin/deno /usr/local/bin/; fi")

# 3. Upgrade yt-dlp, requests, pillow, ffmpeg-python
os.system("pip install -q --upgrade \"yt-dlp[default]\" requests pillow ffmpeg-python")

print("✅ [Kaggle Bideo Engine] Environment ready for 24/7 autonomous video sync!")
