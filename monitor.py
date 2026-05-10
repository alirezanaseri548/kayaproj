import requests
import json
import os
from datetime import datetime, timezone

# =========================================================
# CONFIG
# =========================================================

# فقط پروژه‌های Node.js
API_URL = (
    "https://ir.api.kaya.ir/api/v2/projects/projects"
    "?limit=20&offset=0&skills=500&fixed=false&hourly=false"
)

# Bale Bot
BALE_TOKEN = "1230631087:hTpemS-3QOS4mfJNcIR7tcXVkzxJII7Qxhk"
CHAT_ID = "293358612"

# Files
STATE_FILE = "project_state.json"
LAST_RUN_FILE = "last_run.json"

# =========================================================
# SEND MESSAGE TO BALE
# =========================================================

def send_bale_msg(text):

    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        print(f"📡 Bale status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Bale API error: {response.text}")

    except Exception as e:
        print(f"❌ Error sending Bale message: {e}")

# =========================================================
# LOAD STATE
# =========================================================

def load_state():

    if not os.path.exists(STATE_FILE):
        return {}

    try:

        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:

        print(f"⚠️ Could not load state file: {e}")

        return {}

# =========================================================
# SAVE STATE
# =========================================================

def save_state(data):

    try:

        with open(STATE_FILE, "w", encoding="utf-8") as f:

            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )

        print("💾 State saved")

    except Exception as e:

        print(f"❌ Error saving state: {e}")

# =========================================================
# SAVE LAST RUN
# =========================================================

def save_last_run():

    try:

        with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:

            json.dump(
                {
                    "last_run": datetime.now(
                        timezone.utc
                    ).isoformat()
                },
                f,
                indent=2
            )

        print("⏱ Last run saved")

    except Exception as e:

        print(f"❌ Error saving last run: {e}")

# =========================================================
# FORMAT BUDGET
# =========================================================

def format_budget(min_budget, max_budget):

    if min_budget and max_budget:
        return f"{min_budget:,} تا {max_budget:,} تومان"

    if min_budget:
        return f"از {min_budget:,} تومان"

    if max_budget:
        return f"تا {max_budget:,} تومان"

    return "توافقی"

# =========================================================
# FORMAT SKILLS
# =========================================================

def format_skills(skills):

    skill_names = []

    for skill in skills:

        title = skill.get("title")

        if title:
            skill_names.append(title)

    if not skill_names:
        return "نامشخص"

    return ", ".join(skill_names)

# =========================================================
# BUILD MESSAGE
# =========================================================

def build_message(project):

    title = project.get("title", "بدون عنوان")

    description = project.get("description", "")

    if len(description) > 300:
        description = description[:300] + "..."

    budget = format_budget(
        project.get("budget_min"),
        project.get("budget_max")
    )

    skills = format_skills(
        project.get("skills", [])
    )

    slug = project.get("slug")

    if slug:
        link = f"https://kaya.ir/projects/{slug}"
    else:
        link = "https://kaya.ir/projects"

    message = (
        f"🚀 پروژه جدید Node.js در کایا\n\n"
        f"📌 عنوان:\n{title}\n\n"
        f"💰 بودجه:\n{budget}\n\n"
        f"🛠 مهارت‌ها:\n{skills}\n\n"
        f"📄 توضیحات:\n{description}\n\n"
        f"🔗 لینک پروژه:\n{link}"
    )

    return message

# =========================================================
# FETCH PROJECTS
# =========================================================

def fetch_projects():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json"
    }

    try:

        response = requests.get(
            API_URL,
            headers=headers,
            timeout=20
        )

    except Exception as e:

        print(f"❌ API request failed: {e}")

        send_bale_msg(
            f"❌ خطا در اتصال به API کایا\n{e}"
        )

        return []

    print(f"🌐 Kaya status: {response.status_code}")

    if response.status_code != 200:

        print(response.text)

        send_bale_msg(
            f"❌ خطا در دریافت پروژه‌ها از کایا\n"
            f"Status: {response.status_code}"
        )

        return []

    try:

        data = response.json()

    except Exception as e:

        print(f"❌ JSON error: {e}")

        send_bale_msg(
            "❌ خطا در پردازش JSON کایا"
        )

        return []

    # بعضی وقت‌ها data است بعضی results
    projects = (
        data.get("data")
        or data.get("results")
        or []
    )

    return projects

# =========================================================
# MAIN
# =========================================================

def run():

    print("🚀 Kaya monitor started")

    seen_projects = load_state()

    projects = fetch_projects()

    print(f"📦 Projects fetched: {len(projects)}")

    if not projects:
        print("⚠️ No projects returned from API")
        return

    new_state = {}

    new_count = 0

    for project in projects:

        project_id = str(
            project.get("id")
        )

        if not project_id:
            continue

        new_state[project_id] = True

        if project_id in seen_projects:
            continue

        new_count += 1

        title = project.get(
            "title",
            "بدون عنوان"
        )

        print(f"🔔 New project: {title}")

        message = build_message(project)

        send_bale_msg(message)

    if new_count == 0:

        print("😴 No new projects found")

    else:

        print(f"✅ {new_count} new projects sent")

    save_state(new_state)

    save_last_run()

    print("🏁 Monitor finished")

# =========================================================

if __name__ == "__main__":
    run()
