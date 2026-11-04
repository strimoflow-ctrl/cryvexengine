import os
import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def get_int_env(key: str, default: int = 0) -> int:
    val = os.getenv(key, "").strip()
    return int(val) if val.isdigit() else default

def _decode(b64_str: str) -> str:
    try:
        return base64.b64decode(b64_str.encode()).decode()
    except Exception:
        return ""

# ================= TELEGRAM CONFIG =================
TELEGRAM_API_ID = get_int_env("TELEGRAM_API_ID", 31048519)
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", _decode("YTY2MzkyZGU3Y2U3NjBhMDAyMjdjOGU5Y2RmZTIzYTk=")).strip()
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN", _decode("ODg0MTE5MzQxMTpBQUdIYUpMNkV3RE55ME1kMDdIMlhoM3I5T05pbkJpd2w5MA==")).strip()
TELEGRAM_OWNER_ID = get_int_env("OWNER_ID", 8841106658)
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "Nox_oo1").strip()

# ================= PINTEREST CONFIG =================
PINTEREST_SESSION = os.getenv("PINTEREST_SESSION", "TWc9PSZFeW51S2V6b1lVUDRjYzg1QnQ1Zjl3OTlCMWVXbUJ0R1YxYlBFNE5HQ3hwNzFtMi9OWGZSMHVZM25JeHhEYlVnQzBhM2NuNmZQbWhiczN1eEVhZTZ1S01Lb3crcGxTRFNrcFo5YUxoOXBSWEd0VVFZUXZvbndPWHQ0cTQ3WVVOWWplL3hhMDFrWDJKenVyc2RrWHFneTF1NFNUWHdjemtjaDNZRDBUQ29SR01HYWIyLzB4Q1l0UDBNdXJmRFdxSjFpbWdlUkI0SDlUMS9Vdkx4aW01U1ZaeFBzY3JxRVZ2RmV5ZjV6ZFh5cGtCYlpwZVFlQjRCRXN4NGJMeGxScG01N1VTcU9CY1pGT1ZLZW5EdEI1MTdqOUoxcnhSY1lTTDdYaDJ3djNiVUR3cWJMSjhOZVppSlBqbWN6cUlMdUtxeThheGo5ZnU5MFRvS0hoeWhBUFNvUEF6VGVpOUs1NHYzWEgxZWorZnJCa0FIdEJPK04vQWpjR09ySVVaNVpteVg2ZEVkNGljT0FmajV4Tll4QlY3eVBoUWVXTnRxZG5UYy8vVHdMVDZYTDRLNllYTjZZb1VwcWN5ZjhhRnU5WjlicHhBSnphbTJ5dVF3bVdxTFpsc281RzNoTWNxMk1Fdk84c05PZlBuMUQwditMWksvTk8xMTZ4c05GSEdaTHNrTyswaTNaRnFmbmx0UUNheXZBY3UwQlZTbHNlNlVKOEtDcW8rWmVvU29zYURoRGdKZ1hhT2ZRRzVhOHdCTEtUK2k1aHJRTlVqYVRYNE9iSXpmc29tY2NqNW9Bb0JLdUFJd1RqRzBZdFBtbHlqVGYxNDlQeHJWTVgrd1EvcEFUUXFkVXVLeTJnMmRQRCtqL3U0UXR1a2lSR0srUkZHSzg2aUJ6YURDaVJnb2FTM080aXh0UDVEa1N1LzFQSFFVV0xCbzlhY2FEamtTdFNieGQ2b052UWJ2N1FjcDB4OVFlT0hHbUxPbGM3Tm1pYlEyclY3cCtTRTZwekJzcDhEdHNUTWxGY01mSHBmVlcrWjkrWWViWU4waW5EUGI1Z2ozV1RQWkdQWFJFYzg0WGNEQ3krVEljZmZnV09KSlJwTUM0a0xwN2tnR2lUV3dDSW8za2sxYjE2WmpGRVdrL3paZmFwYzFPU2U1WjlId0ZQcGtmTE83SWw1VnNpQjMzdDBVYmxUaHlndjk2dkZjcGYvaFFrL1V4RXN3YWFKdS9xTnA2aFVIS3BQU1NSaG10M2hnS1VDaTU1Q1JpZ3g3b1FYM2s3UjBaNGk2b3pBempRdklTOHNyOE9rSWZQbm5jMnlsaWluQVFuVWErZ1kvVEtMNS9LNUg2QVUzR3crR3FaWitGM1haZ0VpTmlOU2JPUFNZWkhSTEloMmhUbENBeXY5a1pERFVPdEM2d1B2alV2U1dYTkZXd29BRlJqQVJFNXpGU2VIeHJJNnJXQzJWcjUzK3dqS3FjQ01YckRhWlBOTjhzU2tzbWd4OTlsZEtUWkRKZHhEcTRibkpBaXRhMVU4ZURJQVhYdnpZdUxlSERsNVVvQW0zLzJWTFU2N0l5bVZjTDNuY0tJZGoxS3hzQ2xBTG1uMTFhbFBjSWU3R3JIdUplY1A3dnNITWhOYzRmeUphT0tnMjNqdlF2Z0VNYytjR0Via0ZvdGFJaHFtMEhua1o2eWd2UXQrcFlMZ3JuZVZIS0U3MjhGYmIybzZPY2pMOGtSQ20yN29hQTBqd2RCeWNRTlQrUWRuT09tOFkvYVIvY3ZqckhNcXlxOWtnSTdsd1lxOG8mT2dTQ1FWNW0yL0dWeG9FZ203SFJ2NWdNZVlJPQ==").strip()
PINTEREST_BOARD_ID = os.getenv("PINTEREST_BOARD_ID", "1043357507362929953").strip()
POST_INTERVAL_MINUTES = get_int_env("POST_INTERVAL_MINUTES", 35)

# ================= WEB APP & MONETAG CONFIG =================
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "").strip()
TIMER_SECONDS = get_int_env("TIMER_SECONDS", 9)
MONETAG_DIRECT_LINK = os.getenv("MONETAG_DIRECT_LINK", "https://otieuwai.net/4/your_monetag_direct_link").strip()
MONETAG_SCRIPT_TAG = os.getenv("MONETAG_SCRIPT_TAG", """
<!-- Monetag Ad Placeholder (paste your Monetag tag in environment or here) -->
<script>(function(s,u,z,p){s.src='//'+u+'/p.js?r='+z;s.async=true;(document.body||document.head).appendChild(s);})(document,'groleegni.net',8500000,window);</script>
""").strip()

# ================= STORAGE =================
MEDIA_DIR = BASE_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = BASE_DIR / "pfp_database.db"
