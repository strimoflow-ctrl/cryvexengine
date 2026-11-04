import os
import time
import threading
from datetime import datetime
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, send_from_directory, abort, jsonify

from . import config
from . import database
from .pinterest_poster import post_single_item
from .telegram_scraper import scrape_telegram_web

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

pfp_bp = Blueprint(
    "pfp_bp", 
    __name__, 
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR)
)

_worker_thread = None
_worker_lock = threading.Lock()

def pfp_background_worker():
    """
    Background worker thread:
    - Auto-scrapes from t.me/Nox_oo1 when queue is empty
    - Auto-posts 1 pin to Pinterest every POST_INTERVAL_MINUTES (35 min)
    - Sends Telegram Bot notification to owner on each pin
    """
    time.sleep(5) # brief initial delay
    print("🚀 [PFP ENGINE] 24/7 Background Pinterest & Telegram Worker Active!")
    database.init_db()
    
    while True:
        try:
            item = database.get_next_unposted_item()
            if not item:
                print("📥 [PFP ENGINE] Queue empty. Scraping new batch from Telegram Nox_oo1...")
                scrape_telegram_web(max_items=25)
                item = database.get_next_unposted_item()

            if item:
                print(f"📌 [PFP ENGINE] Auto-posting Pin #{item['id']} to Pinterest...")
                post_single_item(item)
            else:
                print("[*] [PFP ENGINE] No items available to post right now.")
        except Exception as e:
            print(f"⚠️ [PFP ENGINE] Error in background worker: {e}")

        sleep_secs = max(config.POST_INTERVAL_MINUTES * 60, 600)
        time.sleep(sleep_secs)

def start_pfp_background_thread():
    global _worker_thread
    with _worker_lock:
        if _worker_thread is None or not _worker_thread.is_alive():
            _worker_thread = threading.Thread(target=pfp_background_worker, daemon=True, name="PFP-Worker")
            _worker_thread.start()
            print("⚡ [PFP ENGINE] Background Worker Thread launched successfully!")
    return _worker_thread

@pfp_bp.record_once
def on_register(state):
    database.init_db()
    start_pfp_background_thread()

@pfp_bp.before_app_request
def check_worker():
    start_pfp_background_thread()

@pfp_bp.route("/pfp-static/<path:filename>")
def pfp_static(filename):
    return send_from_directory(str(STATIC_DIR), filename)

@pfp_bp.route("/pfp")
def pfp_home():
    items = database.get_recent_items(limit=36)
    stats = database.get_stats()
    return render_template(
        "pfp_index.html",
        items=items,
        stats=stats,
        monetag_script_tag=config.MONETAG_SCRIPT_TAG
    )

@pfp_bp.route("/p/<int:item_id>")
def view_pin(item_id):
    item = database.get_item_by_id(item_id)
    if not item:
        abort(404)
        
    database.increment_views(item_id)
    site_url = config.SITE_BASE_URL or request.host_url.rstrip("/")
    
    return render_template(
        "pin_view.html",
        item=item,
        site_url=site_url,
        timer_seconds=config.TIMER_SECONDS,
        monetag_direct_link=config.MONETAG_DIRECT_LINK,
        monetag_script_tag=config.MONETAG_SCRIPT_TAG,
        now_year=datetime.now().year
    )

@pfp_bp.route("/download/<int:item_id>")
def download_item(item_id):
    item = database.get_item_by_id(item_id)
    if not item:
        abort(404)
        
    database.increment_downloads(item_id)
    
    file_path = config.MEDIA_DIR / item["file_path"]
    if file_path.exists():
        return send_from_directory(
            str(config.MEDIA_DIR), 
            item["file_path"], 
            as_attachment=True, 
            download_name=item["original_filename"] or item["file_path"]
        )
    elif item.get("cdn_url"):
        return redirect(item["cdn_url"])
    else:
        abort(404)

@pfp_bp.route("/media/<path:filename>")
def serve_media(filename):
    return send_from_directory(str(config.MEDIA_DIR), filename)

@pfp_bp.route("/api/pfp/stats")
def api_pfp_stats():
    return jsonify(database.get_stats())

@pfp_bp.route("/api/pfp/post-now")
def api_pfp_post_now():
    """Manually trigger 1 pin post and scrape if needed."""
    database.init_db()
    item = database.get_next_unposted_item()
    if not item:
        scrape_telegram_web(max_items=10)
        item = database.get_next_unposted_item()
        
    if not item:
        return jsonify({"success": False, "message": "No unposted items found"})
        
    ok = post_single_item(item)
    return jsonify({
        "success": ok,
        "posted_item": item["id"],
        "title": item["seo_title"],
        "stats": database.get_stats()
    })
