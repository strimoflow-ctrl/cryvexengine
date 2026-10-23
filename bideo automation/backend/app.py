import os
import sys
import json
import subprocess
import tempfile
import threading
from datetime import datetime
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import imageio_ffmpeg

from firebase_client import FirebaseClient
from bideo_client import BideoClient
from youtube_worker import YouTubeWorker
from automation_scheduler import AutomationScheduler

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
# Start Background Automation Scheduler
# -------------------------------------------------------------
try:
    AutomationScheduler.start()
except Exception as e:
    print(f"[Scheduler Startup Notice] {e}")


if __name__ == "__main__":
    port = int(os.environ.get("SERVER_PORT") or os.environ.get("PORT") or 5000)
    print("==================================================")
    print(">>> BIDEO MULTI-CHANNEL & YOUTUBE AUTOMATION ACTIVE")
    print(f">>> Dashboard URL: http://localhost:{port}")
    print(f">>> Firebase DB: {FirebaseClient._url('bideo_automation')}")
    print(f">>> FFmpeg Core: {FFMPEG_EXE}")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
