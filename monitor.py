import json
import requests
import os

BALE_TOKEN = "1230631087:hTpemS-3QOS4mfJNcIR7tcXVkzxJII7Qxhk"
BALE_681141315 = "681141315"

API_URL = "https://ir.api.kaya.ir/api/v2/projects/projects?limit=20&skills%5B%5D=500&fixed=false&hourly=false"

SEEN_FILE = "seen_projects.json"


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()

    with open(SEEN_FILE, "r") as f:
        return set(json.load(f))


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def send_bale(text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"

    payload = {
        "chat_id": BALE_681141315,
        "text": text
    }

    requests.post(url, json=payload)


def main():

    seen = load_seen()

    r = requests.get(API_URL)
    data = r.json()

    projects = data.get("data", [])

    for p in projects:

        pid = str(p.get("id"))

        if pid in seen:
            continue

        title = p.get("title")
        slug = p.get("slug")

        link = f"https://kaya.ir/project/{slug}"

        msg = f"پروژه جدید در کایا\n\n{title}\n\n{link}"

        send_bale(msg)

        seen.add(pid)

    save_seen(seen)


if __name__ == "__main__":
    main()
