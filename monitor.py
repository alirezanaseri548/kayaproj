import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone

# -----------------------------
# CONFIGURATION
# -----------------------------

URL = "https://kaya.ir/projects/programming"
BALE_TOKEN = "1230631087:hTpemS-3QOS4mfJNcIR7tcXVkzxJII7Qxhk"
CHAT_ID = "293358612"

STATE_FILE = "project_state.json"
LAST_RUN_FILE = "last_run.json"

# -----------------------------
# SEND MESSAGE TO BALE
# -----------------------------

def send_bale_msg(text):
    """Send message to Bale via bot."""
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print("📡 Bale:", r.status_code)
        if r.status_code != 200:
            print("❌ Bale error:", r.text)
    except Exception as e:
        print("❌ Bale send error:", e)

# -----------------------------
# LOAD STATE
# -----------------------------

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf8") as f:
                return json.load(f)
        except:
            return {}
    else:
        return {}

# -----------------------------
# SAVE STATE
# -----------------------------

def save_state(data):
    with open(STATE_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# MAIN LOGIC
# -----------------------------

def run():
    print("🌐 Fetching projects from Kaya site...")

    seen = load_state()

    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print("❌ Error connecting to Kaya webpage:", e)
        send_bale_msg(f"❌ خطا در اتصال به سایت کایا:\n{e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    projects = soup.select(".project-card, .ProjectCard_projectCard__")

    if not projects:
        print("⚠️ No projects found – site HTML structure may have changed.")
        send_bale_msg("⚠️ خطا در خواندن صفحه پروژه‌های کایا (ساختار سایت تغییر کرده).")
        return

    new_count = 0
    new_state = {}

    for project in projects:
        # Extract project link and title
        link_tag = project.find("a", href=True)
        link = "https://kaya.ir" + link_tag["href"] if link_tag else URL

        title_el = project.find("h3")
        title = title_el.get_text(strip=True) if title_el else "بدون عنوان"

        description_el = project.find("p")
        description = description_el.get_text(strip=True) if description_el else "توضیح ندارد"

        id_slug = link.split("/")[-1]  # unique ID part from URL
        new_state[id_slug] = True

        # skills / tags
        tags = project.select(".tag, .ProjectTag_tag__")
        skill_list = [t.get_text(strip=True) for t in tags]
        skills_lower = [s.lower() for s in skill_list]

        if "node.js" not in skills_lower and "nodejs" not in skills_lower:
            continue  # skip if not related to Node.js

        if id_slug not in seen:
            new_count += 1
            hashtags = " ".join([f"#{s.replace(' ', '')}" for s in skill_list])
            msg = (
                f"✨ پروژه جدید در کایا!\n\n"
                f"📌 عنوان: {title}\n"
                f"📄 توضیحات:\n{description}\n\n"
                f"🔗 لینک: {link}\n\n"
                f"{hashtags}"
            )
            print("🔔 Sending project:", title)
            send_bale_msg(msg)

    if new_count == 0:
        print("😴 No new Node.js projects found.")
    else:
        print(f"✅ {new_count} new Node.js project(s) sent to Bale.")

    save_state(new_state)
    with open(LAST_RUN_FILE, "w") as f:
        json.dump({"last_run": datetime.now(timezone.utc).isoformat()}, f)

    print("🏁 Finished.")

if __name__ == "__main__":
    run()
