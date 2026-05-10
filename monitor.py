import requests
import json
import os

API_URL = "https://ir.api.kaya.ir/api/v2/projects/projects?limit=20&offset=0&skills=500&fixed=false&hourly=false"
BALE_TOKEN = "2115160012:v8oT43oUfR3Y3N5Xv6p8K4G3j8Z9Q2L1S6D5F4G3"
CHAT_ID = "293358612"
STATE_FILE = "seen_projects.json"

def send_bale_msg(text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"📡 Bale: {res.status_code}")
    except Exception as e:
        print(f"❌ Bale Error: {e}")

def run():
    print("🚀 Checking Kaya API for Node.js projects...")
    seen_ids = []
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                seen_ids = json.load(f)
        except:
            pass

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }

    try:
        r = requests.get(API_URL, headers=headers, timeout=15)
        print(f"HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"❌ Kaya API Error: {r.text[:200]}")
            return
        data = r.json().get("results", [])
        print(f"✅ {len(data)} projects fetched.")
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return

    new_ids = []
    found_new = False
    for p in data:
        pid = str(p["id"])
        new_ids.append(pid)
        if pid not in seen_ids:
            found_new = True
            title = p.get("title", "بدون عنوان")
            budget_min = p.get("budget_min", 0)
            budget_max = p.get("budget_max", 0)
            link = f"https://kaya.ir/projects/{p.get('slug')}"
            msg = f"✨ پروژه جدید Node.js در سایت کایا!\n\n📌 {title}\n💰 بودجه: {budget_min:,} - {budget_max:,} تومان\n🔗 {link}"
            print(f"🔔 Sending Bale alert: {title}")
            send_bale_msg(msg)

    if found_new:
        with open(STATE_FILE, "w") as f:
            json.dump(new_ids, f)
        print("💾 State updated.")
    else:
        print("😴 No new Node.js projects found.")

if __name__ == "__main__":
    run()
    print("🏁 Monitor finished.")
