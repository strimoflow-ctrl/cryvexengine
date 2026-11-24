import os
import sys
import threading
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bot_engine import BotEngine, AutoCoinMiner, DEFAULT_CRYVEX_CHANNEL_ID, DEFAULT_CRYVEX_USERNAME, BASE_NODE, DEFAULT_USER_AGENT
from farming_engine import AutonomousFarmEngine
from view_limit_manager import ViewLimitManager
import requests

# Silence noisy HTTP access logs from Werkzeug so the terminal remains 100% clean and clear
logging.getLogger("werkzeug").setLevel(logging.ERROR)

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
@app.route("/api/miner/limits", methods=["GET"])
def get_miner_limits():
    """Returns 24h limits, mined amount, and ON/OFF status for all 3 bots."""
    try:
        from coin_miner import MiningLimitManager
        limits = MiningLimitManager.get_instance().get_all_limits()
        return jsonify({"success": True, "limits": limits})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/miner/limits", methods=["POST"])
def update_miner_limits():
    """Updates 24h limit or ON/OFF toggle for an account."""
    body = request.get_json() or {}
    username = body.get("username", "").strip()
    enabled = body.get("enabled")
    daily_limit = body.get("daily_limit")

    if not username:
        return jsonify({"success": False, "message": "username zaroori hai!"}), 400

    try:
        from coin_miner import MiningLimitManager, PodiumMinerEngine
        res = MiningLimitManager.get_instance().update_config(
            username=username,
            enabled=enabled,
            daily_limit=daily_limit
        )
        try:
            PodiumMinerEngine.get_instance().sync_podium_state()
        except Exception:
            pass
        return jsonify({
            "success": True,
            "message": f"Settings saved for {username}!",
            "data": res
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/podium/status", methods=["GET"])
def get_podium_status():
    """Fetches live podium rankings from Firebase."""
    try:
        r = requests.get(
            f"{BASE_NODE}/podium_miner.json",
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=5
        )
        if r.ok and r.json():
            return jsonify({"success": True, "podium": r.json()})
    except Exception:
        pass
    return jsonify({"success": False, "podium": None})


@app.route("/api/podium/accounts", methods=["GET"])
def get_podium_accounts():
    """Lists all accounts in the coin mining pool."""
    from coin_miner import PodiumMinerEngine
    engine = PodiumMinerEngine.get_instance()
    accounts = []
    limits_map = engine.limit_mgr.get_all_limits()
    for a in engine.accounts:
        accounts.append({
            "rank": a.rank,
            "label": a.label,
            "username": a.username,
            "phone": a.phone,
            "coins": round(a.coins, 1),
            "enabled": limits_map.get(a.username, {}).get("enabled", True),
            "daily_limit": limits_map.get(a.username, {}).get("daily_limit", 50.0),
            "mined_24h": limits_map.get(a.username, {}).get("mined_24h", 0.0),
            "status": a.status
        })
    return jsonify({"success": True, "accounts": accounts})


@app.route("/api/podium/accounts", methods=["POST"])
def add_podium_account():
    """Authenticates and adds a new account to coin mining."""
    body = request.get_json() or {}
    phone = str(body.get("phone", "")).strip()
    password = str(body.get("password", "")).strip()
    daily_limit = float(body.get("daily_limit", 50.0))
    streams_count = int(body.get("streams_count", 2))

    if not phone or not password:
        return jsonify({"success": False, "message": "Phone number aur Password dono zaroori hain!"}), 400

    from coin_miner import PodiumMinerEngine
    engine = PodiumMinerEngine.get_instance()
    ok, msg = engine.add_account(phone, password, daily_limit=daily_limit, streams_count=streams_count)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/podium/accounts/<username>", methods=["DELETE"])
def remove_podium_account(username):
    """Removes an account from coin mining."""
    from coin_miner import PodiumMinerEngine
    engine = PodiumMinerEngine.get_instance()
    ok, msg = engine.remove_account(username)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


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


# -------------------------------------------------------------
# 24H Views & Multi-Channel Limit Management API
# -------------------------------------------------------------
@app.route("/api/views/channels", methods=["GET"])
def get_view_channels():
    """Returns 24h view summary, limits, and status for all managed channels."""
    try:
        summary = ViewLimitManager.get_instance().get_all_channels_summary()
        return jsonify({"success": True, **summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/views/channels", methods=["POST"])
def add_view_channel():
    """Adds a new channel by username or ID with 24h limit."""
    body = request.get_json() or {}
    identifier = body.get("identifier", "").strip()
    daily_limit = body.get("daily_limit", 200)

    if not identifier:
        return jsonify({"success": False, "message": "Channel username ya ID zaroori hai!"}), 400

    try:
        ok, msg = ViewLimitManager.get_instance().add_channel(identifier, daily_limit=daily_limit)
        if not ok:
            return jsonify({"success": False, "message": msg}), 400
        summary = ViewLimitManager.get_instance().get_all_channels_summary()
        return jsonify({"success": True, "message": msg, **summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/views/channels/<channel_id>", methods=["DELETE"])
def delete_view_channel(channel_id):
    """Deletes a channel from 24h views management."""
    try:
        ok, msg = ViewLimitManager.get_instance().remove_channel(channel_id)
        if not ok:
            return jsonify({"success": False, "message": msg}), 400
        summary = ViewLimitManager.get_instance().get_all_channels_summary()
        return jsonify({"success": True, "message": msg, **summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/views/channels/<channel_id>/limit", methods=["POST"])
def update_view_channel_limit(channel_id):
    """Updates 24h daily limit or enabled toggle for a channel."""
    body = request.get_json() or {}
    daily_limit = body.get("daily_limit")
    enabled = body.get("enabled")

    try:
        ok, res = ViewLimitManager.get_instance().update_channel(
            channel_id,
            enabled=enabled,
            daily_limit=daily_limit
        )
        if not ok:
            return jsonify({"success": False, "message": res}), 400
        summary = ViewLimitManager.get_instance().get_all_channels_summary()
        return jsonify({"success": True, "message": "Settings saved!", "data": res, **summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/views/channels/<channel_id>/toggle", methods=["POST"])
def toggle_view_channel(channel_id):
    """Toggles enabled state for a channel."""
    body = request.get_json() or {}
    enabled = body.get("enabled")

    try:
        mgr = ViewLimitManager.get_instance()
        ch_data = mgr.data.get(channel_id)
        if not ch_data:
            return jsonify({"success": False, "message": "Channel nahi mila"}), 404

        new_val = (not ch_data.get("enabled", True)) if enabled is None else bool(enabled)
        ok, res = mgr.update_channel(channel_id, enabled=new_val)
        summary = mgr.get_all_channels_summary()
        return jsonify({"success": True, "message": "Status updated!", "data": res, **summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/views/global", methods=["POST"])
def update_global_views():
    """Updates master 24h view budget and ON/OFF switch."""
    body = request.get_json() or {}
    daily_limit = body.get("daily_limit")
    enabled = body.get("enabled")

    try:
        mgr = ViewLimitManager.get_instance()
        res = mgr.update_global_config(enabled=enabled, daily_limit=daily_limit)
        summary = mgr.get_all_channels_summary()
        return jsonify({"success": True, "message": "Global view settings saved!", "data": res, **summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/views/global/toggle", methods=["POST"])
def toggle_global_views():
    """Toggles master view engine switch ON/OFF."""
    body = request.get_json() or {}
    enabled = body.get("enabled")

    try:
        mgr = ViewLimitManager.get_instance()
        new_val = (not mgr.is_global_enabled()) if enabled is None else bool(enabled)
        res = mgr.update_global_config(enabled=new_val)
        summary = mgr.get_all_channels_summary()
        return jsonify({"success": True, "message": "Global switch updated!", "data": res, **summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/views/global/reset", methods=["POST"])
def reset_global_views():
    """Instantly clears all 24h rolling view history across all channels and stealth views."""
    try:
        mgr = ViewLimitManager.get_instance()
        mgr.reset_history()
        summary = mgr.get_all_channels_summary()
        return jsonify({"success": True, "message": "All 24h view counters reset to 0!", **summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/views/channels/<channel_id>/reset", methods=["POST"])
def reset_channel_views(channel_id):
    """Instantly clears 24h rolling view history for a specific channel."""
    try:
        mgr = ViewLimitManager.get_instance()
        mgr.reset_history(channel_id=channel_id)
        summary = mgr.get_all_channels_summary()
        return jsonify({"success": True, "message": f"Channel 24h view counter reset to 0!", **summary})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    # 1. 24/7 multi-stream podium miner (Rank 1 Cryvex, Rank 2 Pankaj, Rank 3 Hariom) with 24h limits & toggles
    try:
        from coin_miner import PodiumMinerEngine
        PodiumMinerEngine.get_instance().start_in_background()
        print("🏆 [PODIUM MINER] 24/7 Multi-stream engine started in background!")
    except Exception as e:
        print(f"⚠️ [PODIUM MINER] Failed to auto-start: {e}")

    # 2. Start 24/7 autonomous farming engine (anti-rush, hourly spawner, review watchdog)
    AutonomousFarmEngine.get_instance().start()

    port = int(os.environ.get("PORT") or os.environ.get("SERVER_PORT") or os.environ.get("BOTS_PORT", 5050))
    print("==================================================")
    print(">>> BIDEO BOT ARMY & FOLLOWER ENGINE ACTIVE")
    print(f">>> Bots Dashboard: http://localhost:{port}")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)

