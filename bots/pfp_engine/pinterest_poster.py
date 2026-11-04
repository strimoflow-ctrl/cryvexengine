import os
import sys
import time
import json
import requests
from pathlib import Path

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .config import (
    PINTEREST_SESSION, PINTEREST_BOARD_ID, 
    SITE_BASE_URL, MEDIA_DIR, POST_INTERVAL_MINUTES
)
from . import database
from .notifier import send_telegram_notification

DEFAULT_BOARD_ID = PINTEREST_BOARD_ID or "1043357507362929953"

class PinterestSessionPoster:
    def __init__(self, session_cookie: str):
        self.session_cookie = session_cookie
        self.http = requests.Session()
        self.http.cookies.set('_pinterest_sess', session_cookie, domain='.pinterest.com')
        self.app_version = '4fc27a6'
        self.csrf_token = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.pinterest.com/pin-builder/',
            'X-Pinterest-AppState': 'active',
            'X-Pinterest-PWS-Handler': 'www/pin-builder/index.js',
            'X-APP-VERSION': self.app_version
        }

    def refresh_csrf(self):
        try:
            resp = self.http.get('https://www.pinterest.com/pin-builder/', headers=self.headers, timeout=15)
            self.csrf_token = self.http.cookies.get('csrftoken', '')
            self.headers['X-CSRFToken'] = self.csrf_token
            return bool(self.csrf_token)
        except Exception as e:
            print(f"[-] Failed to get CSRF token: {e}")
            return False

    def create_pin(self, board_id: str, title: str, description: str, link: str, image_url: str):
        if not self.csrf_token:
            self.refresh_csrf()

        data = {
            "options": {
                "board_id": str(board_id),
                "field_set_key": "create_success",
                "title": title[:100],
                "description": description[:500],
                "link": link,
                "image_url": image_url
            },
            "context": {}
        }
        
        post_payload = {
            "source_url": "/pin-builder/",
            "data": json.dumps(data)
        }

        url = 'https://www.pinterest.com/resource/PinResource/create/'
        resp = self.http.post(url, headers=self.headers, data=post_payload, timeout=20)
        
        if resp.status_code == 200:
            res_data = resp.json()
            pin_data = res_data.get('resource_response', {}).get('data', {})
            pin_id = pin_data.get('id')
            if pin_id:
                return {"success": True, "pin_id": pin_id, "url": f"https://www.pinterest.com/pin/{pin_id}/"}
                
        return {"success": False, "error": f"Status {resp.status_code}: {resp.text[:200]}"}

def post_single_item(item: dict, host_url: str = "", board_id: str = DEFAULT_BOARD_ID) -> bool:
    item_id = item["id"]
    base = host_url or SITE_BASE_URL
    
    if not base or "localhost" in base or "127.0.0.1" in base or not base.startswith("http"):
        landing_url = f"https://nainofuture.blogspot.com/p/download.html?pfp={item_id}"
    else:
        landing_url = f"{base}/p/{item_id}"

    # Use direct CDN url so Pinterest crawlers fetch high-res image directly
    image_url = item.get("cdn_url") or f"https://picsum.photos/seed/{item_id}/800/1200"

    poster = PinterestSessionPoster(PINTEREST_SESSION)
    result = poster.create_pin(
        board_id=board_id,
        title=item["seo_title"],
        description=item["seo_description"],
        link=landing_url,
        image_url=image_url
    )

    if result.get("success"):
        pin_id = result["pin_id"]
        pin_url = result["url"]
        database.mark_item_posted(item_id, pin_id)
        print(f"[✓] Pin #{item_id} successfully created on Pinterest! URL: {pin_url}")

        notif_msg = (
            f"📌 <b>New Pin Posted to Pinterest!</b>\n\n"
            f"🏷️ <b>Title:</b> {item['seo_title']}\n"
            f"🔗 <b>Pinterest Pin:</b> <a href=\"{pin_url}\">{pin_url}</a>\n"
            f"🌐 <b>Landing Page:</b> <a href=\"{landing_url}\">{landing_url}</a>\n\n"
            f"⚡ <i>Auto-posted via NOX Automation</i>"
        )
        send_telegram_notification(notif_msg)
        return True
    else:
        err = result.get("error", "Unknown error")
        print(f"[-] Failed to post Pin #{item_id}: {err}")
        database.mark_item_error(item_id, err)
        
        err_msg = f"⚠️ <b>Pinterest Post Failed for #{item_id}</b>\n\n<code>{err}</code>"
        send_telegram_notification(err_msg)
        return False

