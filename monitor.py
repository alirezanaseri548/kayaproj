import json
import requests
import os
import sys

# تنظیمات اصلی
BALE_TOKEN = "1230631087:hTpemS-3QOS4mfJNcIR7tcXVkzxJII7Qxhk"
BALE_CHAT_ID = "293358612" # 👈 مطمئن شو این آیدی خودته
API_URL = "https://ir.api.kaya.ir/api/v2/projects/projects?limit=20&skills%5B%5D=500&fixed=false&hourly=false"
SEEN_FILE = "seen_projects.json"

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    try:
        with open(SEEN_FILE, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
            if not content: return set()
            return set(map(str, json.loads(content)))
    except Exception as e:
        print(f"⚠️ Warning loading JSON: {e}")
        return set()

def save_seen(seen):
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen), f)
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")

def send_bale(text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": BALE_CHAT_ID, "text": text}, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Bale API Error: {e}")

def main():
    print("🚀 Starting Scan...")
    seen = load_seen()
    
    # اضافه کردن هدر برای شبیه‌سازی مرورگر (بسیار مهم)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        print(f"📡 Requesting Kaya API...")
        r = requests.get(API_URL, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"❌ Kaya API Request Failed: {e}")
        sys.exit(1) # اینجا باعث میشه اکشن گیت‌هاب متوجه خطا بشه

    projects = data.get("data", [])
    if not projects:
        print("ℹ️ No projects found in API response.")
        return

    new_count = 0
    for p in projects:
        pid = str(p.get("id"))
        if pid in seen:
            continue

        title = p.get("title", "بدون عنوان")
        slug = p.get("slug", "")
        link = f"https://kaya.ir/project/{slug}"
        
        print(f"✨ New Project Found: {title}")
        msg = f"🔔 پروژه جدید کایا\n\n📌 {title}\n\n🔗 {link}"
        
        send_bale(msg)
        seen.add(pid)
        new_count += 1

    if new_count > 0:
        save_seen(seen)
        print(f"✅ Finished. {new_count} new projects notified.")
    else:
        print("😴 No new projects since last check.")

if __name__ == "__main__":
    main()
