import os
import sys
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bot_engine import BotEngine, AutoCoinMiner, DEFAULT_CRYVEX_CHANNEL_ID, DEFAULT_CRYVEX_USERNAME
from farming_engine import AutonomousFarmEngine

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)


# -------------------------------------------------------------
# Frontend Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


# -------------------------------------------------------------
# Bot Accounts API
# -------------------------------------------------------------
@app.route("/api/bots", methods=["GET"])
def get_bots():
    bots = BotEngine.get_all_bots()
    return jsonify({"success": True, "bots": bots, "count": len(bots)})


@app.route("/api/bots/generate", methods=["POST"])
def generate_bots():
    body = request.get_json() or {}
    count = int(body.get("count", 1))
    count = max(1, min(count, 50))  # Safeguard between 1 and 50
    custom_name = body.get("custom_name")

    if count == 1:
        ok, bot, err = BotEngine.create_single_bot(custom_name=custom_name)
        if not ok:
            return jsonify({"success": False, "message": err or "Failed to create account"}), 400
        return jsonify({"success": True, "bot": bot, "message": f"Account '{bot['name']}' created successfully!"})

    # Bulk create
    created = BotEngine.bulk_create_bots(count=count)
    return jsonify({
        "success": True,
        "bots": created,
        "count": len(created),
        "message": f"Batch of {len(created)} accounts created successfully!"
    })


@app.route("/api/bots/<bot_id>", methods=["DELETE"])
def delete_bot(bot_id):
    ok = BotEngine.delete_bot(bot_id)
    return jsonify({"success": ok})


# -------------------------------------------------------------
# Cryvex Specific & Channel Video Pipeline API
# -------------------------------------------------------------
@app.route("/api/cryvex/videos", methods=["GET"])
def get_cryvex_videos():
    channel_id = request.args.get("channel_id") or DEFAULT_CRYVEX_CHANNEL_ID
    result = BotEngine.get_channel_videos(channel_id)
    return jsonify(result)


@app.route("/api/cryvex/stats", methods=["GET"])
def get_cryvex_stats():
    channel_id = request.args.get("channel_id") or DEFAULT_CRYVEX_CHANNEL_ID
    stats = BotEngine.get_follow_stats(channel_id)
    return jsonify({"success": True, "stats": stats})


@app.route("/api/cryvex/coins", methods=["GET"])
def get_cryvex_coins():
    result = BotEngine.get_cryvex_coins_status()
    return jsonify(result)


@app.route("/api/cryvex/claim-coins", methods=["POST"])
def claim_cryvex_coins():
    result = BotEngine.claim_cryvex_ad_coins()
    return jsonify(result)


@app.route("/api/cryvex/auto-miner-status", methods=["GET"])
def get_auto_miner_status():
    status = AutoCoinMiner.get_instance().get_status()
    return jsonify({"success": True, "status": status})


@app.route("/api/cryvex/pass-review", methods=["POST"])
def pass_video_review():
    body = request.get_json() or {}
    review_id = body.get("review_id")
    video_id = body.get("video_id")
    result = BotEngine.pass_video_review(review_id=review_id, video_id=video_id)
    return jsonify(result)


@app.route("/api/cryvex/pass-all-reviews", methods=["POST"])
def pass_all_pending_reviews():
    result = BotEngine.pass_all_pending_reviews()
    return jsonify(result)



# -------------------------------------------------------------
# Controllable Growth & Engagement API
# -------------------------------------------------------------
@app.route("/api/bots/follow", methods=["POST"])
def boost_followers():
    body = request.get_json() or {}
    target_channel_id = body.get("target_channel_id", "").strip() or DEFAULT_CRYVEX_CHANNEL_ID
    count = body.get("count")  # Controlled quantity (e.g. 5, 10, None for all)

    result = BotEngine.boost_followers(target_channel_id, count=count)
    return jsonify(result)


@app.route("/api/bots/boost-video", methods=["POST"])
def boost_video():
    body = request.get_json() or {}
    video_id = body.get("video_id", "").strip()
    views_count = int(body.get("views_count", 10))
    likes_count = int(body.get("likes_count", 5))
    watch_time = int(body.get("watch_time", 30))

    if not video_id:
        return jsonify({"success": False, "message": "Video ID zaroori hai!"}), 400

    result = BotEngine.boost_video(
        video_id,
        views_count=views_count,
        likes_count=likes_count,
        watch_time=watch_time
    )
    return jsonify(result)


@app.route("/api/bots/batch-boost", methods=["POST"])
def batch_boost_videos():
    body = request.get_json() or {}
    channel_id = body.get("channel_id") or DEFAULT_CRYVEX_CHANNEL_ID
    views_per_video = int(body.get("views_per_video", 5))
    likes_per_video = int(body.get("likes_per_video", 3))
    watch_time = int(body.get("watch_time", 30))

    result = BotEngine.batch_boost_channel_videos(
        channel_id=channel_id,
        views_per_video=views_per_video,
        likes_per_video=likes_per_video,
        watch_time=watch_time
    )
    return jsonify(result)


@app.route("/api/bots/farm-coins", methods=["POST"])
def farm_coins():
    result = BotEngine.claim_cryvex_ad_coins()
    return jsonify(result)


@app.route("/api/bots/pin-highlight", methods=["POST"])
def pin_highlight():
    body = request.get_json() or {}
    video_id = body.get("video_id", "").strip()
    duration_hours = int(body.get("duration", 1))

    if not video_id:
        return jsonify({"success": False, "message": "Video ID zaroori hai!"}), 400

    result = BotEngine.pin_video_to_highlight(video_id, duration_hours=duration_hours)
    return jsonify(result)


@app.route("/api/bots/search", methods=["GET"])
def search_channels():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"success": True, "channels": []})
    channels = BotEngine.search_channels(q)
    return jsonify({"success": True, "channels": channels})


# -------------------------------------------------------------
# 24/7 Autonomous Farming System API
# -------------------------------------------------------------
@app.route("/api/farm/status", methods=["GET"])
def get_farm_status():
    status = AutonomousFarmEngine.get_instance().get_status()
    return jsonify({"success": True, "status": status})


@app.route("/api/farm/toggle", methods=["POST"])
def toggle_farm():
    body = request.get_json() or {}
    farm = AutonomousFarmEngine.get_instance()
    action = body.get("action")  # "start", "stop", or toggle
    if action == "start":
        farm.start()
    elif action == "stop":
        farm.stop()
    else:
        if farm.running:
            farm.stop()
        else:
            farm.start()
    return jsonify({"success": True, "is_active": farm.running, "status": farm.get_status()})


if __name__ == "__main__":
    # 1. Start 24/7 background automatic coin claimer
    AutoCoinMiner.get_instance().start()

    # 2. Start 24/7 autonomous farming engine (anti-rush, hourly spawner, review watchdog)
    AutonomousFarmEngine.get_instance().start()

    port = int(os.environ.get("PORT") or os.environ.get("SERVER_PORT") or os.environ.get("BOTS_PORT", 5050))
    print("==================================================")
    print(">>> BIDEO BOT ARMY & FOLLOWER ENGINE ACTIVE")
    print(f">>> Bots Dashboard: http://localhost:{port}")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)

