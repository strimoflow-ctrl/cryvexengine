import requests
import json
import sys
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json'
})

payload = {'phone': '7052733069', 'password': 'pankaj@5911'}
print("Logging in to Bideo API...")
resp = session.post('https://bideo.in/api/auth/login', json=payload, timeout=30)
print(f"Bideo Login status: {resp.status_code}")
data = resp.json()

if not data.get('success'):
    print(f"Login failed: {data}")
    sys.exit(1)

token = data.get('token')
user = data.get('user', {})
uid = user.get('_id', '6ada0b9dfb39968c7c48dd7b')
name = user.get('name', 'cryvex')
phone = user.get('phone', '7052733069')

print(f"Login SUCCESSFUL! User ID: {uid}, Name: {name}, Phone: {phone}")

# Test auth with /api/auth/me
auth_resp = session.get('https://bideo.in/api/auth/me', headers={'Authorization': f'Bearer {token}'}, timeout=30)
print(f"Test /api/auth/me status: {auth_resp.status_code}")
if auth_resp.status_code != 200:
    print(f"Token validation failed: {auth_resp.text}")
    sys.exit(1)

print(f"Token verified! AdRewards/Balance active.")

# Write token to Firebase accounts
fb_url = 'https://secret-gpt-default-rtdb.asia-southeast1.firebasedatabase.app/bideo_automation'
acc_data = {
    'name': name,
    'phone': phone,
    'password': 'pankaj@5911',
    'token': token,
    'user_id': uid,
    'status': 'active',
    'updated_at': datetime.now().isoformat()
}
put_resp = requests.put(f"{fb_url}/accounts/{uid}.json", json=acc_data, timeout=30)
print(f"Firebase accounts/{uid} update status: {put_resp.status_code}")

# Also update active_batch if exists
active_batch = requests.get(f"{fb_url}/active_batch.json", timeout=30).json()
if active_batch and isinstance(active_batch, dict):
    print(f"Found active_batch: {active_batch.get('batch_id')}, current status: {active_batch.get('status')}")
    # If it was stuck or in pacing sleep, we can check its status
    
# Check Firebase accounts to confirm
fb_check = requests.get(f"{fb_url}/accounts/{uid}.json", timeout=30).json()
print(f"Firebase verified token: {fb_check.get('token')[:35]}... Status: {fb_check.get('status')}")

print("\n--- SUCCESS: CRYVEX TOKEN SUCCESSFULLY SAVED TO FIREBASE! ---")
