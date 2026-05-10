import requests
import json
import os
from datetime import datetime, timezone

# -----------------------------
# CONFIG
# -----------------------------

API_URL = "https://ir.api.kaya.ir/api/v2/projects/projects?limit=20"

BALE_TOKEN = "1230631087:hTpemS-3QOS4mfJNcIR7tcXVkzxJII7Qxhk"
CHAT_ID = "293358612"

STATE_FILE = "project_state.json"
LAST_RUN_FILE = "last_run.json"

# -----------------------------
# SEND MESSAGE TO BALE
# -----------------------------

def send_bale_msg(text):

    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    try:

        r = requests.post(
            url,
            json=payload,
            timeout=15
        )

        print("📡 Bale status:", r.status_code)

        if r.status_code != 200:
            print("❌ Bale error:", r.text)

    except Exception as e:
        print("❌ Bale send error:", e)

# -----------------------------
# LOAD STATE
# -----------------------------

def load_state():

    if not os.path.exists(STATE_FILE):
        return {}

    try:

        with open(STATE_FILE, "r", encoding="utf8") as f:
            return json.load(f)

    except:
        return {}

# -----------------------------
# SAVE STATE
# -----------------------------

def save_state(data):

    with open(STATE_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# SAVE LAST RUN
# -----------------------------

def save_last_run():

    with open(LAST_RUN_FILE, "w") as f:

        json.dump(
            {"last_run": datetime.now(timezone.utc).isoformat()},
            f
        )

# -----------------------------
# MAIN
# -----------------------------

def run():

    print("🚀 Kaya monitor started")

    seen = load_state()

    headers = {

        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"

    }

    try:

        r = requests.get(
            API_URL,
            headers=headers,
            timeout=20
        )

    except Exception as e:

        print("❌ API connection error:", e)

        send_bale_msg(f"❌ خطای اتصال به کایا\n{e}")

        return

    if r.status_code != 200:

        print("❌ Kaya API error:", r.text)

        send_bale_msg("❌ خطا در دریافت پروژه‌ها از کایا")

        return

    try:

        data = r.json()

    except:

        print("❌ JSON decode error")

        return

    projects = data.get("data", [])

    print("📦 projects found:", len(projects))

    new_count = 0

    new_state = {}

    for p in projects:

        pid = str(p.get("id"))

        new_state[pid] = True

        if pid in seen:
            continue

        new_count += 1

        title = p.get("title", "بدون عنوان")

        desc = p.get("description", "")

        if len(desc) > 150:
            desc = desc[:150] + "..."

        budget_min = p.get("budget_min")
        budget_max = p.get("budget_max")

        budget = "توافقی"

        if budget_min and budget_max:
            budget = f"{budget_min:,} - {budget_max:,} تومان"

        slug = p.get("slug")

        if slug:
            link = f"https://kaya.ir/projects/{slug}"
        else:
            link = "https://kaya.ir/projects"

        skills = []

        for s in p.get("skills", []):
            name = s.get("title")
            if name:
                skills.append(name)

        skills_text = ", ".join(skills) if skills else "نامشخص"

        message = (
            f"🚀 پروژه جدید در کایا\n\n"
            f"📌 {title}\n"
            f"💰 بودجه: {budget}\n"
            f"🛠 مهارت‌ها: {skills_text}\n\n"
            f"📄 توضیحات:\n{desc}\n\n"
            f"🔗 {link}"
        )

        print("🔔 new project:", title)

        send_bale_msg(message)

    if new_count == 0:
        print("😴 no new projects")

    else:
        print("✅ new projects:", new_count)

    save_state(new_state)

    save_last_run()

    print("🏁 monitor finished")

# -----------------------------

if __name__ == "__main__":
    run()
