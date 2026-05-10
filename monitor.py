import requests
from bs4 import BeautifulSoup
import json
import os
import logging

URL = "https://kaya.ir/projects/programming/backend-development"

# ==========================
# DIRECT TOKENS (YOUR REQUEST)
# ==========================
BALE_TOKEN = "1230631087:hTpemS-3QOS4mfJNcIR7tcXVkzxJII7Qxhk"
CHAT_ID = "293358612"

STATE_FILE = "project_state.json"

logging.basicConfig(level=logging.INFO)

def send_message(text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            json={"chat_id": CHAT_ID, "text": text},
            timeout=15
        )
    except Exception as e:
        logging.error(f"Bale error: {e}")

def load_state():
    if not os.path.exists(STATE_FILE):
        return []

    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def fetch_projects():

    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(URL, headers=headers, timeout=30)

    soup = BeautifulSoup(r.text, "html.parser")

    projects = []

    cards = soup.find_all("a", href=True)

    for card in cards:

        href = card["href"]

        if "/projects/" not in href:
            continue

        title = card.get_text(strip=True)
        if len(title) < 5:
            continue

        link = "https://kaya.ir" + href

        projects.append({"title": title, "link": link})

    return projects

def run():

    seen = load_state()
    projects = fetch_projects()

    new_seen = []

    for p in projects:

        pid = p["link"]
        new_seen.append(pid)

        if pid not in seen:

            msg = f"""
🚀 پروژه جدید بک‌اند در کایا

📌 {p['title']}

🔗 {p['link']}
"""

            send_message(msg)
            logging.info("NEW PROJECT SENT")

    save_state(new_seen)

if __name__ == "__main__":
    run()
