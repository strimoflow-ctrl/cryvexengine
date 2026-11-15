import requests
import json
import sys
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json'
}

FB_URL = 'https://secret-gpt-default-rtdb.asia-southeast1.firebasedatabase.app/bideo_automation'

ACCOUNTS_CONFIG = [
    {'name': 'cryvex', 'phone': '7052733069', 'password': 'pankaj@5911', 'user_id': '6ada0b9dfb39968c7c48dd7b'},
    {'name': 'pankaj_bideo', 'phone': '9115233706', 'password': 'pankaj@5911', 'user_id': '6ad9f679fb39968c7c37f8b5'},
    {'name': 'hariom_ai', 'phone': '9648083419', 'password': 'hariom65', 'user_id': '6ae80c2eff1a527964fd12b8'}
]

fresh_accounts = {}

for acc in ACCOUNTS_CONFIG:
    phone = acc['phone']
    pwd = acc['password']
    acc_name = acc['name']
    print(f"Logging in {acc_name} ({phone})...")
    r = requests.post('https://bideo.in/api/auth/login', json={'phone': phone, 'login': phone, 'password': pwd}, headers=headers, timeout=15)
    data = r.json()
    if not data.get('success'):
        print(f"Failed to login {acc_name}: {data}")
        continue
    token = data['token']
    user = data['user']
    
    # Get full profile via /api/auth/me
    r_me = requests.get('https://bideo.in/api/auth/me', headers={**headers, 'Authorization': f'Bearer {token}'}, timeout=15)
    me_data = r_me.json().get('data', {}) if r_me.ok else {}
    
    uid = user.get('_id') or acc['user_id']
    clean_record = {
        '_id': uid,
        'id': uid,
        'user_id': uid,
        'name': user.get('name') or acc_name,
        'channelName': me_data.get('channelName') or user.get('channelName') or acc_name,
        'phone': phone,
        'password': pwd,
        'token': token,
        'avatar': me_data.get('avatar') or user.get('avatar') or '',
        'followersCount': me_data.get('followersCount', 0),
        'coins': me_data.get('coins', 0),
        'walletBalance': me_data.get('walletBalance', 0),
        'status': 'active',
        'is_primary': (acc_name == 'cryvex'),
        'updated_at': datetime.now().isoformat()
    }
    fresh_accounts[uid] = clean_record
    print(f"✅ Prepared account {clean_record['name']} (@{clean_record['channelName']}) | Token length: {len(token)}")

# Update Firebase accounts directly
print(f"\nReplacing Firebase accounts with {len(fresh_accounts)} clean accounts...")
put_r = requests.put(f"{FB_URL}/accounts.json", json=fresh_accounts, timeout=20)
print(f"Firebase accounts replacement status: {put_r.status_code}")

# Verify
check_r = requests.get(f"{FB_URL}/accounts.json", timeout=10)
check_data = check_r.json()
print(f"Verified accounts in Firebase count: {len(check_data)}")
for k, v in check_data.items():
    print(f"  -> {v.get('name')} (@{v.get('channelName')}) | Phone: {v.get('phone')} | Coins: {v.get('coins')}")

print("\n--- ALL 200+ BOTS REMOVED AND ONLY 3 MAIN ACCOUNTS SAVED! ---")

