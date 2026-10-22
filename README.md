# 🚀 Bideo Video Automation Pipeline

High-performance automated video pipeline connecting **YouTube channels** to **Bideo Creator Studio** with 1080p downloading, metadata synchronization, 30-minute recurring backfill, duplicate prevention via Firebase Realtime Database, and full 24/7 Railway cloud deployment readiness.

---

## 🌟 Key Features

1. **YouTube to Bideo Auto-Pipeline**:
   - Downloads videos in crisp **1080p MP4** via `yt-dlp` and `imageio-ffmpeg`.
   - Extracts and syncs the exact original YouTube **Title** and **Description**.
   - Extracts HD thumbnail at 1-second mark via FFmpeg.
   - Posts directly to the designated Bideo channel via official multipart upload API (`POST /api/videos/upload`).

2. **30-Minute Automation Cycle**:
   - Background daemon thread checks active channel pairings every 30 minutes.
   - Automatically detects new releases as well as unposted older backlog videos.

3. **Zero Duplicate Prevention (Firebase Synced)**:
   - Tracks all posted YouTube video IDs in Firebase Realtime Database (`/bideo_automation/posted_videos/{yt_id}`).
   - Survives server restarts and Railway redeployments without duplicate uploads.

4. **Instant Disk Cleanup**:
   - Temporary 1080p video files are purged from disk immediately after uploading, preventing Railway ephemeral disk overflow.

5. **Multi-Channel & Multi-Account Support**:
   - Log into multiple Bideo accounts and switch between them in 1-click.
   - Pair different YouTube channels to different Bideo accounts.

---

## 📁 Repository Structure

```text
├── bideo automation/
│   ├── backend/
│   │   ├── app.py                     # Main Flask Server & REST API
│   │   ├── automation_scheduler.py    # 30-Minute Recurring Worker Thread
│   │   ├── bideo_client.py            # Official Bideo API Client (Auth, Upload)
│   │   ├── firebase_client.py         # Firebase Realtime DB REST Client
│   │   ├── youtube_worker.py          # 1080p yt-dlp Video Downloader
│   │   └── requirements.txt           # Python Dependencies
│   └── frontend/
│       ├── index.html                 # Studio & Automation Hub Dashboard
│       ├── style.css                  # Modern Glassmorphic Dark UI
│       └── app.js                     # Interactive State & Real-time Logs
├── Dockerfile                         # Railway Production Container (Python 3.12 + FFmpeg)
├── Procfile                           # Web Process Config
├── railway.json                       # Railway Builder & Restart Policy
├── .dockerignore
└── .gitignore
```

---

## 🚂 Railway Deployment (1-Click)

1. Connect this GitHub repository (`cryvexengine`) in [Railway](https://railway.app/).
2. Railway will automatically detect `railway.json` and build the container using `Dockerfile` (which installs Python 3.12 and system `ffmpeg`).
3. Set the environment variable:
   - `PORT`: `5000` (or Railway default)
   - `FIREBASE_DB_URL`: `https://secret-gpt-default-rtdb.asia-southeast1.firebasedatabase.app`
4. Under **Settings**, click **Generate Domain** to get your public live URL (e.g., `https://cryvexengine-production.up.railway.app`).
5. Open your public domain, log in to your Bideo account, connect your YouTube channel, and let automation run 24/7!
