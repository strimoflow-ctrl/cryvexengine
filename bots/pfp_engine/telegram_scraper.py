import os
import sys
import re
import time
import requests
from pathlib import Path

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .config import TELEGRAM_CHANNEL, MEDIA_DIR
from . import database
from . import seo_generator

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}

def clean_html_text(raw_html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", raw_html)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()

def scrape_telegram_web(channel: str = TELEGRAM_CHANNEL, max_items: int = 50):
    database.init_db()
    channel = channel.replace("https://t.me/", "").replace("@", "").strip()
    base_url = f"https://t.me/s/{channel}"

    saved_count = 0
    skipped_count = 0
    before_id = None

    while saved_count < max_items:
        fetch_url = f"{base_url}?before={before_id}" if before_id else base_url
        try:
            resp = requests.get(fetch_url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                break
        except Exception:
            break

        html = resp.text
        msg_blocks = re.findall(
            r'(<div class="tgme_widget_message\b[^"]*"[^>]*data-post="([^"]+)"[^>]*>.*?)(?=<div class="tgme_widget_message\b|\Z)',
            html,
            re.DOTALL
        )

        if not msg_blocks:
            break

        first_msg_id = None
        for block_html, data_post in msg_blocks:
            try:
                msg_id = int(data_post.split("/")[-1])
            except (ValueError, IndexError):
                continue

            if first_msg_id is None or msg_id < first_msg_id:
                first_msg_id = msg_id

            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM media_items WHERE telegram_msg_id = ?", (msg_id,))
            exists = cursor.fetchone()
            conn.close()

            if exists:
                skipped_count += 1
                continue

            img_matches = re.findall(r"background-image:url\('([^']+)'\)", block_html)
            valid_imgs = [img for img in img_matches if "telegram.org/img/emoji" not in img]
            vid_matches = re.findall(r'<video[^>]+src="([^"]+)"', block_html)

            text_match = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', block_html, re.DOTALL)
            caption = clean_html_text(text_match.group(1)) if text_match else ""

            media_type = None
            media_url = None
            filename = None

            if valid_imgs:
                media_type = "photo"
                media_url = valid_imgs[0]
                filename = f"photo_{msg_id}.jpg"
            elif vid_matches:
                media_type = "video"
                media_url = vid_matches[0]
                filename = f"video_{msg_id}.mp4"

            if not media_type or not media_url:
                continue

            # Zero-storage mode: don't store full bytes permanently, rely on Telegram global CDN
            seo = seo_generator.generate_seo_metadata(caption=caption, media_type=media_type, msg_id=msg_id)
            
            database.insert_media_item(
                msg_id=msg_id,
                media_type=media_type,
                file_path=filename,
                original_filename=filename,
                file_size=0,
                caption=caption,
                title=seo["title"],
                description=seo["description"],
                tags=seo["tags"],
                cdn_url=media_url
            )
            saved_count += 1

            if saved_count >= max_items:
                break

        if first_msg_id and (before_id is None or first_msg_id < before_id):
            before_id = first_msg_id
        else:
            break

        time.sleep(1)

    return saved_count

