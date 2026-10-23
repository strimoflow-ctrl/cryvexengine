import os
import sys
import json
import time
import uuid
import subprocess
import tempfile
import threading
from datetime import datetime
import requests
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import imageio_ffmpeg

from firebase_client import FirebaseClient
from bideo_client import BideoClient
from youtube_worker import YouTubeWorker
from automation_scheduler import AutomationScheduler
from kaggle_manager import KaggleManager, FIREBASE_DB_URL, FIREBASE_ROOT

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

BIDEO_API_BASE = "https://bideo.in/api"
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


# -------------------------------------------------------------
# Utility: Video Metadata Extraction
# -------------------------------------------------------------
def extract_video_info(video_path):
    duration = 10.0
    width = 1080
    height = 1920

    try:
        cmd = [FFMPEG_EXE, "-i", video_path]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
        output = result.stderr

        import re
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", output)
        if dur_match:
            h, m, s = dur_match.groups()
            duration = int(h) * 3600 + int(m) * 60 + float(s)

        res_match = re.search(r"Video:.*,\s*(\d{3,4})x(\d{3,4})", output)
        if res_match:
            width = int(res_match.group(1))
            height = int(res_match.group(2))

    except Exception as e:
        print(f"[FFmpeg Warning] Could not parse video metadata: {e}")

    is_short = (height >= width)

    return {
        "duration": round(duration, 2),
        "width": width,
        "height": height,
        "is_short": is_short,
        "aspect_ratio": round(width / height, 4) if height else 1.0
    }


def generate_thumbnail(video_path, output_thumb_path, timestamp="00:00:01"):
    cmd = [
        FFMPEG_EXE,
        "-y",
        "-ss", timestamp,
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        output_thumb_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.exists(output_thumb_path) and os.path.getsize(output_thumb_path) > 0


# -------------------------------------------------------------
# Frontend Static Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("../frontend", path)


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# -------------------------------------------------------------
# API: Categories
# -------------------------------------------------------------
@app.route("/api/categories", methods=["GET"])
def get_categories():
    try:
        categories = BideoClient.get_categories()
        return jsonify({"success": True, "categories": categories})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# API: Login with Phone / Username & Password (Saves to Firebase)
# -------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def login():
    try:
        body = request.get_json() or {}
        login_val = body.get("login") or body.get("phone") or body.get("username")
        password = body.get("password")

        if not login_val or not password:
            return jsonify({"success": False, "message": "Phone number/username aur password dono zaroori hain!"}), 400

        success, token, user_data, err_msg = BideoClient.login(login_val, password)
        if not success:
            return jsonify({"success": False, "message": err_msg or "Login fail ho gaya"}), 400

        # Save to Firebase Realtime Database for Multi-Account & Automation
        FirebaseClient.save_account(user_data, token, login_val.strip())

        return jsonify({
            "success": True,
            "token": token,
            "user": user_data
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Server connection error: {str(e)}"}), 500


# -------------------------------------------------------------
# API: Multi-Account Management
# -------------------------------------------------------------
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    accounts = FirebaseClient.get_accounts()
    # Mask full tokens slightly for safety in listing
    safe_accounts = []
    for acc in accounts:
        safe_acc = dict(acc)
        tok = safe_acc.get("token", "")
        safe_acc["has_token"] = bool(tok)
        safe_accounts.append(safe_acc)
    return jsonify({"success": True, "accounts": safe_accounts})


@app.route("/api/accounts/<user_id>", methods=["DELETE"])
def delete_account(user_id):
    try:
        # Delete from Firebase accounts
        r = requests.delete(FirebaseClient._url(f"accounts/{user_id}"), timeout=8)
        return jsonify({"success": r.ok})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# API: YouTube <---> Bideo Channel Pairings
# -------------------------------------------------------------
@app.route("/api/pairings", methods=["GET"])
def list_pairings():
    pairings = FirebaseClient.get_pairings()
    return jsonify({"success": True, "pairings": pairings})


@app.route("/api/pairings", methods=["POST"])
def create_pairing():
    body = request.get_json() or {}
    yt_input = body.get("yt_channel", "").strip()
    bideo_user_id = body.get("bideo_user_id", "").strip()
    category_id = body.get("category_id", "").strip()
    category_name = body.get("category_name", "").strip()

    if not yt_input or not bideo_user_id:
        return jsonify({"success": False, "message": "YouTube Channel aur Bideo Account dono zaroori hain!"}), 400

    # Verify Bideo account exists
    bideo_acc = FirebaseClient.get_account_by_id(bideo_user_id)
    if not bideo_acc:
        return jsonify({"success": False, "message": "Select kiya gaya Bideo account nahi mila!"}), 404

    # Scrape YouTube channel meta & test connectivity
    try:
        channel_meta, videos = YouTubeWorker.get_channel_info_and_videos(yt_input, max_results=10)
    except Exception as e:
        return jsonify({"success": False, "message": f"YouTube channel connect karne me error: {str(e)}"}), 400

    pairing_id = f"pair_{int(datetime.utcnow().timestamp())}"
    pairing_data = {
        "id": pairing_id,
        "yt_channel_url": channel_meta.get("channel_url", yt_input),
        "yt_channel_name": channel_meta.get("channel_name", yt_input),
        "bideo_user_id": bideo_user_id,
        "bideo_channel_name": bideo_acc.get("name") or bideo_acc.get("channelName", "Bideo Channel"),
        "category_id": category_id,
        "category_name": category_name,
        "is_active": True,
        "total_posted": 0,
        "created_at": datetime.utcnow().isoformat(),
        "last_polled_at": None,
        "last_posted_at": None
    }

    saved = FirebaseClient.save_pairing(pairing_id, pairing_data)
    if not saved:
        return jsonify({"success": False, "message": "Firebase database me pairing save nahi ho saki."}), 500

    FirebaseClient.add_log(
        "Automation Pairing Created",
        f"YouTube '{pairing_data['yt_channel_name']}' linked to Bideo '{pairing_data['bideo_channel_name']}'",
        "success",
        pairing_data
    )

    return jsonify({"success": True, "pairing": pairing_data})


# -------------------------------------------------------------
# CHANNEL VIDEO LIBRARY & ON-DEMAND BATCH QUEUE
# -------------------------------------------------------------
@app.route("/api/channels/fetch", methods=["POST"])
def fetch_channel_videos():
    """
    Fetches videos from a YouTube channel via yt-dlp, saves all video records
    into Firebase library under channels/<id>/videos, and returns the video list.
    Preserves existing upload flags so already uploaded videos stay marked!
    """
    body = request.get_json() or {}
    ch_input = body.get("channel_input", "").strip()
    max_results = int(body.get("max_results") or 60)

    if not ch_input:
        return jsonify({"success": False, "message": "YouTube Channel URL ya @handle zaroori hai!"}), 400

    try:
        channel_meta, videos = YouTubeWorker.get_channel_info_and_videos(ch_input, max_results=max_results)
        if not videos:
            return jsonify({"success": False, "message": f"'{ch_input}' se koi video nahi mili! URL ya name check karein."}), 404

        # Save to Firebase catalog
        saved_channel = FirebaseClient.save_channel_and_videos(channel_meta, videos)

        FirebaseClient.add_log(
            "Channel Videos Fetched",
            f"Fetched {len(videos)} videos from '{channel_meta.get('channel_name')}' into library",
            "success",
            {"channel": channel_meta.get("channel_name"), "count": len(videos)}
        )

        return jsonify({
            "success": True,
            "channel": saved_channel,
            "videos": saved_channel.get("videos", [])
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Channel fetch error: {str(e)}"}), 500


@app.route("/api/channels", methods=["GET"])
def list_saved_channels():
    """Lists all saved YouTube channels and their video counts."""
    channels = FirebaseClient.get_all_channels()
    return jsonify({"success": True, "channels": channels})


@app.route("/api/channels/<channel_id>/videos", methods=["GET"])
def get_channel_videos_route(channel_id):
    """Returns all stored videos for a given channel, synced with uploaded state."""
    videos = FirebaseClient.get_channel_videos(channel_id)
    return jsonify({"success": True, "videos": videos})


@app.route("/api/batch/start", methods=["POST"])
def batch_start():
    """
    Pushes selected videos to Firebase as an active batch and launches
    the Kaggle Bot ONCE for this specific task.
    """
    data = request.get_json() or {}
    selected_videos = data.get("selected_videos") or []
    bideo_user_id = data.get("bideo_user_id")
    category_id = data.get("category_id", "")
    category_name = data.get("category_name", "General")
    pacing_hours = float(data.get("pacing_hours") or 9.0)

    if not selected_videos:
        return jsonify({"success": False, "message": "Kam se kam ek video select karein!"}), 400
    if not bideo_user_id:
        return jsonify({"success": False, "message": "Target Bideo Account select karein!"}), 400

    # Verify Bideo account
    bideo_acc = FirebaseClient.get_account_by_id(bideo_user_id)
    if not bideo_acc:
        return jsonify({"success": False, "message": "Select kiya gaya Bideo account nahi mila!"}), 404

    # Build batch record
    batch_id = f"batch_{int(time.time())}"
    batch_data = {
        "batch_id": batch_id,
        "created_at": datetime.utcnow().isoformat(),
        "bideo_user_id": bideo_user_id,
        "bideo_channel_name": bideo_acc.get("name") or bideo_acc.get("channelName", "Bideo Channel"),
        "category_id": category_id,
        "category_name": category_name,
        "pacing_hours": pacing_hours,
        "status": "queued",
        "total_count": len(selected_videos),
        "completed_count": 0,
        "videos": selected_videos
    }

    # Save batch in Firebase
    FirebaseClient.save_active_batch(batch_data)

    # Launch Kaggle on-demand bot
    config = KaggleManager.get_config()
    user = config.get("kaggle_user")
    key = config.get("kaggle_key")
    slug = config.get("kaggle_slug", "bideo-automation-engine")

    if not user or not key:
        return jsonify({
            "success": False,
            "message": "Kaggle API Key configured nahi hai! Pehle Kaggle Settings me setup karein."
        }), 400

    ok, msg = KaggleManager.push_kernel(user, key, slug)
    if ok:
        try:
            requests.put(
                f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/kaggle_status.json",
                json={
                    "is_running": False,
                    "state": "waiting_boot",
                    "launched_at": datetime.now().isoformat(),
                    "last_heartbeat": 0,
                    "batch_id": batch_id,
                    "total_videos": len(selected_videos),
                    "current_task": f"Kaggle Bot launched! Pre-downloading {len(selected_videos)} videos...",
                    "kaggle_url": f"https://www.kaggle.com/code/{user}/{slug}"
                },
                timeout=5
            )
        except Exception:
            pass

        FirebaseClient.add_log(
            "Kaggle Batch Started",
            f"Queued {len(selected_videos)} videos for '{bideo_acc.get('name')}', scheduled over ~{pacing_hours}h",
            "success",
            {"batch_id": batch_id, "count": len(selected_videos)}
        )

        return jsonify({
            "success": True,
            "message": f"Kaggle Bot launched! {len(selected_videos)} videos pre-download karke ~{pacing_hours} ghante me upload honge.",
            "batch": batch_data,
            "kaggle_url": f"https://www.kaggle.com/code/{user}/{slug}"
        })
    else:
        return jsonify({"success": False, "message": f"Kaggle launch error: {msg}"}), 500


@app.route("/api/batch/status", methods=["GET"])
def batch_status():
    """Returns active batch details & Kaggle live progress."""
    batch = FirebaseClient.get_active_batch()
    status = KaggleManager.get_status()
    return jsonify({
        "success": True,
        "batch": batch,
        "kaggle_status": status
    })


@app.route("/api/batch/cancel", methods=["POST"])
def batch_cancel():
    """Cancels active batch and stops running Kaggle session."""
    FirebaseClient.clear_active_batch()
    config = KaggleManager.get_config()
    user = config.get("kaggle_user")
    key = config.get("kaggle_key")
    slug = config.get("kaggle_slug", "bideo-automation-engine")
    if user and key:
        KaggleManager.cancel_kernel(user, key, slug)

    try:
        requests.put(
            f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/kaggle_status.json",
            json={
                "is_running": False,
                "state": "stopped",
                "current_task": "Batch cancelled by user",
                "last_heartbeat": time.time()
            },
            timeout=5
        )
    except Exception:
        pass

    return jsonify({"success": True, "message": "Batch cancelled and Kaggle Bot stopped."})


@app.route("/api/pairings/<pairing_id>", methods=["DELETE"])
def delete_pairing(pairing_id):
    deleted = FirebaseClient.delete_pairing(pairing_id)
    return jsonify({"success": deleted})


@app.route("/api/pairings/<pairing_id>/toggle", methods=["PATCH"])
def toggle_pairing(pairing_id):
    pairings = FirebaseClient.get_pairings()
    target = next((p for p in pairings if p.get("id") == pairing_id), None)
    if not target:
        return jsonify({"success": False, "message": "Pairing not found"}), 404

    new_status = not target.get("is_active", True)
    updated = FirebaseClient.update_pairing(pairing_id, {"is_active": new_status})
    return jsonify({"success": updated, "is_active": new_status})


@app.route("/api/pairings/<pairing_id>/sync", methods=["POST"])
def manual_sync_pairing(pairing_id):
    """
    Manually triggers an immediate sync check for a single pairing in background thread.
    """
    pairings = FirebaseClient.get_pairings()
    target = next((p for p in pairings if p.get("id") == pairing_id), None)
    if not target:
        return jsonify({"success": False, "message": "Pairing not found"}), 404

    # Run in thread so the request returns quickly without blocking UI
    def _run():
        print(f"[Manual Sync] Triggered for pairing {pairing_id}")
        AutomationScheduler.sync_pairing(target)

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return jsonify({
        "success": True,
        "message": f"Sync started for '{target.get('yt_channel_name')}'! Video download aur upload progress me hai."
    })


@app.route("/api/sync_all", methods=["POST"])
def sync_all():
    """Manually triggers sync across all active pairings."""
    def _run():
        AutomationScheduler.run_all_pairings()

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return jsonify({"success": True, "message": "Automation cycle triggered across all pairings!"})


# -------------------------------------------------------------
# API: Channel Video Catalog Explorer (Live Check & Upload Status)
# -------------------------------------------------------------
@app.route("/api/channel/videos", methods=["GET"])
def get_channel_videos():
    channel_url = request.args.get("channel_url", "").strip()
    if not channel_url:
        return jsonify({"success": False, "message": "channel_url query parameter is required"}), 400

    try:
        channel_meta, raw_videos = YouTubeWorker.get_channel_info_and_videos(channel_url, max_results=50)
        posted_videos = FirebaseClient.get_posted_videos()

        enriched = []
        for v in raw_videos:
            vid_id = v.get("id")
            is_uploaded = vid_id in posted_videos
            post_info = posted_videos.get(vid_id) or {}
            
            entry = dict(v)
            entry["is_uploaded"] = is_uploaded
            entry["posted_at"] = post_info.get("posted_at") or post_info.get("postedAt")
            entry["bideo_user_id"] = post_info.get("bideo_user_id")
            entry["pairing_id"] = post_info.get("pairing_id")
            enriched.append(entry)

        uploaded_count = sum(1 for v in enriched if v.get("is_uploaded"))
        pending_count = len(enriched) - uploaded_count

        return jsonify({
            "success": True,
            "channel_name": channel_meta.get("channel_name", channel_url),
            "channel_url": channel_meta.get("channel_url", channel_url),
            "total_videos": len(enriched),
            "uploaded_count": uploaded_count,
            "pending_count": pending_count,
            "videos": enriched
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Channel videos fetch failed: {str(e)}"}), 500


@app.route("/api/pairings/<pairing_id>/videos", methods=["GET"])
def get_pairing_videos(pairing_id):
    pairings = FirebaseClient.get_pairings()
    target = next((p for p in pairings if p.get("id") == pairing_id), None)
    if not target:
        return jsonify({"success": False, "message": "Pairing not found"}), 404

    target_url = target.get("yt_channel_url") or target.get("yt_channel_name")
    try:
        channel_meta, raw_videos = YouTubeWorker.get_channel_info_and_videos(target_url, max_results=50)
        posted_videos = FirebaseClient.get_posted_videos()

        enriched = []
        for v in raw_videos:
            vid_id = v.get("id")
            is_uploaded = vid_id in posted_videos
            post_info = posted_videos.get(vid_id) or {}

            entry = dict(v)
            entry["is_uploaded"] = is_uploaded
            entry["posted_at"] = post_info.get("posted_at") or post_info.get("postedAt")
            entry["bideo_user_id"] = post_info.get("bideo_user_id")
            entry["pairing_id"] = post_info.get("pairing_id")
            enriched.append(entry)

        uploaded_count = sum(1 for v in enriched if v.get("is_uploaded"))
        pending_count = len(enriched) - uploaded_count

        return jsonify({
            "success": True,
            "pairing_id": pairing_id,
            "bideo_user_id": target.get("bideo_user_id"),
            "bideo_channel_name": target.get("bideo_channel_name"),
            "category_id": target.get("category_id"),
            "channel_name": target.get("yt_channel_name") or channel_meta.get("channel_name"),
            "channel_url": target.get("yt_channel_url") or channel_meta.get("channel_url"),
            "total_videos": len(enriched),
            "uploaded_count": uploaded_count,
            "pending_count": pending_count,
            "videos": enriched
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Pairing videos fetch failed: {str(e)}"}), 500



# -------------------------------------------------------------
# API: Save YouTube Cookies (For Cloud / Botkeep Bypass)
# -------------------------------------------------------------
@app.route("/api/save_cookies", methods=["POST"])
def save_cookies():
    try:
        data = request.get_json() or {}
        cookies_text = data.get("cookies_text", "").strip()
        if not cookies_text:
            return jsonify({"success": False, "message": "Cookies text cannot be empty"}), 400

        cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(cookies_text)

        return jsonify({
            "success": True,
            "message": "YouTube Cookies successfully save ho gayi hain! Ab Botkeep server pe zero bot error ke sath download hoga."
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/cookies_status", methods=["GET"])
def cookies_status():
    cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
    has_cookies = os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 10
    return jsonify({
        "success": True,
        "has_cookies": has_cookies,
        "size_bytes": os.path.getsize(cookie_path) if has_cookies else 0
    })


# -------------------------------------------------------------
# API: Automation Activity Logs
# -------------------------------------------------------------
@app.route("/api/logs", methods=["GET"])
def get_logs():
    limit = int(request.args.get("limit", 30))
    logs = FirebaseClient.get_logs(limit=limit)
    return jsonify({"success": True, "logs": logs})


# -------------------------------------------------------------
# API: Single YouTube Video / Shorts Link Upload (Under 500MB)
# -------------------------------------------------------------
@app.route("/api/upload_single_url", methods=["POST"])
def upload_single_url():
    data = request.get_json() or {}
    video_url = data.get("video_url", "").strip()
    bideo_user_id = data.get("bideo_user_id", "").strip()
    category_id = data.get("category_id", "").strip()
    custom_title = data.get("title", "").strip()
    custom_desc = data.get("description", "").strip()

    if not video_url:
        return jsonify({"success": False, "message": "YouTube Video URL zaroori hai!"}), 400
    if not bideo_user_id:
        return jsonify({"success": False, "message": "Target Bideo Account select karein!"}), 400

    account = FirebaseClient.get_account_by_id(bideo_user_id)
    if not account or not account.get("token"):
        return jsonify({"success": False, "message": "Bideo account not found ya logged out hai!"}), 404

    token = account["token"]
    bideo_channel_name = account.get("name", "Bideo Channel")

    # If Kaggle 24/7 Super-Engine is running, queue task for instant Google Cloud execution!
    k_status = KaggleManager.get_status()
    if k_status.get("is_running") and (time.time() - k_status.get("last_heartbeat", 0) < 180):
        task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        task_payload = {
            "id": task_id,
            "video_url": video_url,
            "bideo_user_id": bideo_user_id,
            "bideo_channel_name": bideo_channel_name,
            "category_id": category_id,
            "title": custom_title,
            "description": custom_desc,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        try:
            requests.put(f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/single_upload_queue/{task_id}.json", json=task_payload, timeout=5)
            return jsonify({
                "success": True,
                "message": "Task Kaggle 24/7 Cloud Super-Engine ko bhej diya gaya hai! Google Cloud network se superfast download & Bideo upload ho raha hai.",
                "task_id": task_id,
                "via": "kaggle_cloud"
            })
        except Exception as q_err:
            print(f"[Queue Error] {q_err}. Falling back to local execution...")

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            print(f"[Single Link Upload] Downloading {video_url} with <500MB safeguard...")
            dl_result = YouTubeWorker.download_video_1080p(video_url, tmp_dir)

            vid_id = dl_result["video_id"]
            final_title = custom_title or dl_result["title"] or "YouTube Video"
            description = custom_desc or dl_result["description"] or ""
            video_path = dl_result["video_path"]
            thumb_path = dl_result["thumb_path"]
            is_short = dl_result["is_short"]
            duration = dl_result["duration"]

            meta = {
                "duration": duration,
                "width": dl_result["width"],
                "height": dl_result["height"]
            }

            file_size_mb = round(os.path.getsize(video_path) / (1024 * 1024), 1)
            print(f"[Single Link Upload] Publishing '{final_title}' ({file_size_mb} MB) to '{bideo_channel_name}'...")

            success, bideo_data, err_msg = BideoClient.upload_video(
                token=token,
                video_path=video_path,
                thumb_path=thumb_path,
                title=final_title,
                description=description,
                category_id=category_id,
                is_short=is_short,
                meta=meta
            )

            if not success:
                FirebaseClient.add_log(
                    "Single Link Upload Failed",
                    f"Failed to publish '{final_title}': {err_msg}",
                    "error",
                    {"video_url": video_url, "bideo_user_id": bideo_user_id}
                )
                return jsonify({"success": False, "message": err_msg or "Upload fail ho gaya"}), 500

            # Record in Firebase to prevent future automated duplicates
            bideo_vid_id = bideo_data.get("_id") or bideo_data.get("id", "unknown")
            record = {
                "yt_video_id": vid_id,
                "title": final_title,
                "bideo_video_id": bideo_vid_id,
                "bideo_user_id": bideo_user_id,
                "bideo_channel_name": bideo_channel_name,
                "is_short": is_short,
                "duration": duration,
                "file_size_mb": file_size_mb,
                "uploaded_via": "single_link_uploader"
            }
            FirebaseClient.mark_video_posted(vid_id, record)

            log_msg = f"Single Link Video '{final_title}' ({file_size_mb} MB) successfully published to '{bideo_channel_name}'!"
            print(f"✅ {log_msg}")
            FirebaseClient.add_log("Single Video Published", log_msg, "success", record)

            return jsonify({
                "success": True,
                "message": log_msg,
                "video": bideo_data,
                "file_size_mb": file_size_mb,
                "title": final_title,
                "channel_name": bideo_channel_name
            })

    except Exception as e:
        err = f"Single link upload error: {str(e)}"
        print(f"❌ {err}")
        FirebaseClient.add_log("Single Link Upload Error", err, "error", {"video_url": video_url})
        return jsonify({"success": False, "message": err}), 500


# -------------------------------------------------------------
# API: Direct Manual Video Upload from PC
# -------------------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def upload_to_channel():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"success": False, "message": "Aap logged in nahi hain! Kripya login karein."}), 401

    if "video" not in request.files:
        return jsonify({"success": False, "message": "Video file missing hai!"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"success": False, "message": "Koi video select nahi ki gayi!"}), 400

    title = request.form.get("title", "").strip()
    if not title:
        title = os.path.splitext(video_file.filename)[0].replace("-", " ").replace("_", " ")

    description = request.form.get("description", "").strip()
    category_id = request.form.get("category", "")
    explicit_short = request.form.get("isShort")

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_video_path = os.path.join(tmp_dir, video_file.filename)
        video_file.save(temp_video_path)

        meta = extract_video_info(temp_video_path)
        if explicit_short is not None:
            is_short = explicit_short.lower() in ["true", "1", "yes"]
        else:
            is_short = meta["is_short"]

        temp_thumb_path = os.path.join(tmp_dir, "thumbnail.jpg")
        if "thumbnail" in request.files and request.files["thumbnail"].filename != "":
            request.files["thumbnail"].save(temp_thumb_path)
        else:
            generate_thumbnail(temp_video_path, temp_thumb_path, timestamp="00:00:01")

        if not os.path.exists(temp_thumb_path):
            generate_thumbnail(temp_video_path, temp_thumb_path, timestamp="00:00:00")

        # Clean token
        token_str = auth_header.replace("Bearer ", "").strip()

        success, video_data, err_msg = BideoClient.upload_video(
            token=token_str,
            video_path=temp_video_path,
            thumb_path=temp_thumb_path,
            title=title,
            description=description,
            category_id=category_id,
            is_short=is_short,
            meta=meta
        )

        if not success:
            return jsonify({"success": False, "message": err_msg or "Upload fail ho gaya"}), 500

        return jsonify({
            "success": True,
            "message": "Video successfully aapke channel me upload ho gayi!",
            "video": video_data
        })


# -------------------------------------------------------------
# API: Kaggle 24/7 Cloud Super-Engine Management
# -------------------------------------------------------------
@app.route("/api/kaggle/config", methods=["GET", "POST"])
def kaggle_config():
    if request.method == "POST":
        data = request.get_json() or {}
        KaggleManager.save_config(data)
        return jsonify({"success": True, "message": "Kaggle configuration saved!"})
    config = KaggleManager.get_config()
    return jsonify({"success": True, "config": config})


@app.route("/api/kaggle/status", methods=["GET"])
def kaggle_status():
    status = KaggleManager.get_status()
    config = KaggleManager.get_config()
    return jsonify({
        "success": True,
        "status": status,
        "config": config
    })


@app.route("/api/kaggle/start", methods=["POST"])
def kaggle_start():
    data = request.get_json() or {}
    config = KaggleManager.get_config()

    user = data.get("kaggle_user") or config.get("kaggle_user")
    key = data.get("kaggle_key") or config.get("kaggle_key")
    slug = data.get("kaggle_slug") or config.get("kaggle_slug", "bideo-automation-engine")

    if not user or not key:
        return jsonify({"success": False, "message": "Kaggle Username aur API Key zaroori hai!"}), 400

    config.update({"kaggle_user": user, "kaggle_key": key, "kaggle_slug": slug, "auto_renew": True})
    KaggleManager.save_config(config)

    ok, msg = KaggleManager.push_kernel(user, key, slug)
    if ok:
        try:
            requests.put(
                f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/kaggle_status.json",
                json={
                    "is_running": False,
                    "state": "waiting_heartbeat",
                    "launched_at": datetime.now().isoformat(),
                    "last_heartbeat": 0,
                    "current_task": "Kaggle notebook deployed! Waiting for Google Cloud boot...",
                    "kaggle_url": f"https://www.kaggle.com/code/{user}/{slug}"
                },
                timeout=5
            )
        except Exception:
            pass
        return jsonify({
            "success": True,
            "message": f"Kaggle Job Deployed! Notebook: https://www.kaggle.com/code/{user}/{slug}",
            "kaggle_url": f"https://www.kaggle.com/code/{user}/{slug}"
        })
    else:
        return jsonify({"success": False, "message": f"Kaggle API Error: {msg}"}), 500


@app.route("/api/kaggle/stop", methods=["POST"])
def kaggle_stop():
    config = KaggleManager.get_config()
    user = config.get("kaggle_user")
    key = config.get("kaggle_key")
    slug = config.get("kaggle_slug", "bideo-automation-engine")

    config["auto_renew"] = False
    KaggleManager.save_config(config)

    if user and key:
        KaggleManager.cancel_kernel(user, key, slug)

    try:
        requests.put(
            f"{FIREBASE_DB_URL}/{FIREBASE_ROOT}/kaggle_status.json",
            json={
                "is_running": False,
                "state": "stopped",
                "current_task": "Engine Stopped by User",
                "last_heartbeat": time.time()
            },
            timeout=5
        )
    except Exception:
        pass

    return jsonify({"success": True, "message": "Kaggle Engine stopped and 24/7 auto-renew paused."})


@app.route("/api/kaggle/download_notebook", methods=["GET"])
def kaggle_download_notebook():
    nb = KaggleManager.compile_notebook_json()
    return Response(
        nb,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=bideo_automation_kaggle.ipynb"}
    )


# -------------------------------------------------------------
# On-Demand Localhost Studio Mode (Zero Background Runaways)
# -------------------------------------------------------------
print("[Local Server] Pure Localhost Studio Active. Automation runs on-demand per user selected batch.")


if __name__ == "__main__":
    port = int(os.environ.get("SERVER_PORT") or os.environ.get("PORT") or 5000)
    print("==================================================")
    print(">>> BIDEO MULTI-CHANNEL & YOUTUBE AUTOMATION ACTIVE")
    print(f">>> Dashboard URL: http://localhost:{port}")
    print(f">>> Firebase DB: {FirebaseClient._url('bideo_automation')}")
    print(f">>> FFmpeg Core: {FFMPEG_EXE}")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
