import requests
import json
import os
from datetime import datetime, timezone
import logging

# Setup logging to console for GitHub Actions visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
# Using the comprehensive API URL provided by علیرضا
API_URL = "https://ir.api.kaya.ir/api/v2/projects/projects?limit=20&skills%5B%5D=3&skills%5B%5D=1031&skills%5B%5D=335&skills%5B%5D=1013&skills%5B%5D=1023&skills%5B%5D=44&skills%5B%5D=38&skills%5B%5D=9&skills%5B%5D=2701&skills%5B%5D=59&skills%5B%5D=1055&skills%5B%5D=69&skills%5B%5D=116&skills%5B%5D=947&skills%5B%5D=2164&skills%5B%5D=13&skills%5B%5D=58&skills%5B%5D=2292&skills%5B%5D=305&skills%5B%5D=500&skills%5B%5D=1093&skills%5B%5D=2165&skills%5B%5D=1977&skills%5B%5D=1092&skills%5B%5D=7&skills%5B%5D=137&skills%5B%5D=613&skills%5B%5D=1101&skills%5B%5D=1383&skills%5B%5D=2158&skills%5B%5D=1315&skills%5B%5D=1067&skills%5B%5D=502&skills%5B%5D=115&skills%5B%5D=40&skills%5B%5D=1084&skills%5B%5D=1658&skills%5B%5D=2282&skills%5B%5D=1314&skills%5B%5D=1832&skills%5B%5D=1936&skills%5B%5D=668&skills%5B%5D=2393&skills%5B%5D=497&skills%5B%5D=669&skills%5B%5D=60&skills%5B%5D=31&skills%5B%5D=2839&skills%5B%5D=2159&skills%5B%5D=1088&skills%5B%5D=1004&skills%5B%5D=2152&skills%5B%5D=106&skills%5B%5D=298&skills%5B%5D=72&skills%5B%5D=95&skills%5B%5D=2298&skills%5B%5D=2703&skills%5B%5D=102&skills%5B%5D=320&skills%5B%5D=2382&skills%5B%5D=1552&skills%5B%5D=1521&skills%5B%5D=6&skills%5B%5D=89&skills%5B%5D=759&skills%5B%5D=14&skills%5B%5D=607&skills%5B%5D=323&skills%5B%5D=1686&skills%5B%5D=2068&skills%5B%5D=152&skills%5B%5D=120&skills%5B%5D=2305&skills%5B%5D=481&skills%5B%5D=741&skills%5B%5D=113&skills%5B%5D=1087&skills%5B%5D=2991&skills%5B%5D=1716&skills%5B%5D=2376&skills%5B%5D=407&skills%5B%5D=167&skills%5B%5D=454&skills%5B%5D=704&skills%5B%5D=1657&skills%5B%5D=2161&skills%5B%5D=15&skills%5B%5D=564&skills%5B%5D=1002&skills%5B%5D=1423&skills%5B%5D=1019&skills%5B%5D=480&skills%5B%5D=33&skills%5B%5D=1309&skills%5B%5D=2695&skills%5B%5D=2536&skills%5B%5D=68&skills%5B%5D=716&skills%5B%5D=1030&fixed=false&hourly=false&fixed_min=&fixed_max=&hourly_min=&hourly_max="
BALE_TOKEN = "1230631087:hTpemS-3QOS4mfJNcIR7tcXVkzxJII7Qxhk" # Your Bale bot token
CHAT_ID = "293358612" # Your Bale chat ID
STATE_FILE = "project_state.json" # File to store seen project IDs
LAST_RUN_FILE = "last_run.json" # File to store last run timestamp

# Node.js skill ID (as seen in the URL provided: skills%5B%5D=500)
NODEJS_SKILL_ID = 500

# --- Bale Message Sender ---
def send_bale_msg(text):
    """Sends a message to the specified Bale chat."""
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=15)
        logging.info(f"Bale API Response Status: {r.status_code}")
        if r.status_code != 200:
            logging.error(f"Bale API Error: {r.text}")
    except Exception as e:
        logging.error(f"Error sending message to Bale: {e}")

# --- State Management ---
def load_state():
    """Loads the previously seen project IDs from the state file."""
    if not os.path.exists(STATE_FILE):
        logging.info("State file not found, starting with empty state.")
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf8") as f:
            state = json.load(f)
            logging.info(f"Loaded {len(state)} entries from state file.")
            return state
    except json.JSONDecodeError:
        logging.warning("Corrupted state file (JSONDecodeError), starting fresh.")
        return {}
    except Exception as e:
        logging.warning(f"Error loading state file ({e}), starting fresh.")
        return {}

def save_state(data):
    """Saves the current set of seen project IDs to the state file."""
    try:
        with open(STATE_FILE, "w", encoding="utf8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"State updated successfully with {len(data)} entries.")
    except Exception as e:
        logging.error(f"Error saving state: {e}")
        send_bale_msg(f"❌ خطا در ذخیره وضعیت پروژه: {e}")

def save_last_run_time():
    """Records the current UTC time as the last successful run."""
    try:
        with open(LAST_RUN_FILE, "w") as f:
            json.dump({"last_run": datetime.now(timezone.utc).isoformat()}, f)
        logging.info("Last run time saved.")
    except Exception as e:
        logging.error(f"Error saving last run time: {e}")

# --- Main Monitor Logic ---
def run_monitor():
    logging.info("🚀 Starting Kaya Monitor...")

    seen_projects = load_state()
    current_run_projects_state = {} # Stores all projects fetched in this run

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        logging.info(f"🌐 Attempting to reach Kaya API at: {API_URL}")
        response = requests.get(API_URL, headers=headers, timeout=30) # Increased timeout to 30 seconds
        
        logging.info(f"Kaya API responded with Status: {response.status_code}")
        if response.status_code != 200:
            logging.error(f"Kaya API Error! Status: {response.status_code}")
            logging.error(f"Response Content (first 500 chars): {response.text[:500]}...")
            send_bale_msg(f"❌ خطا در دریافت پروژه‌ها از کایا: {response.status_code}\nمحتوا: {response.text[:100]}...")
            return

        response_json = response.json()
        projects_data = response_json.get('data', []) 
        logging.info(f"✅ Successfully fetched {len(projects_data)} projects from API.")

    except requests.exceptions.Timeout:
        logging.error("Kaya API request timed out after 30 seconds.")
        send_bale_msg("❌ خطای Time out در ارتباط با API کایا (30 ثانیه).")
        return
    except requests.exceptions.ConnectionError as e:
        logging.error(f"ConnectionError: Could not connect to Kaya API. Details: {e}")
        send_bale_msg(f"❌ خطای ConnectionError در ارتباط با کایا API: {e}")
        return
    except requests.exceptions.RequestException as e:
        logging.error(f"General RequestException during API call: {e}")
        send_bale_msg(f"❌ خطای عمومی در درخواست API به کایا: {e}")
        return
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response from Kaya API. Details: {e}. Raw response: {response.text[:500]}...")
        send_bale_msg(f"❌ خطای JSON از کایا: {e}\n(پاسخ نامعتبر API)")
        return
    except Exception as e:
        logging.error(f"An unexpected error occurred during API fetch: {e}", exc_info=True) # exc_info=True for full traceback
        send_bale_msg(f"❌ خطای ناشناخته در دریافت از کایا: {e}")
        return

    new_projects_alerted_count = 0

    for p in projects_data:
        p_id = str(p.get('id'))
        current_run_projects_state[p_id] = True 

        # Verify Node.js skill
        project_skills_ids = [s.get('id') for s in p.get('skills', [])]
        if NODEJS_SKILL_ID not in project_skills_ids:
             logging.debug(f"Skipping project {p_id} (not Node.js): {p.get('title')}")
             continue # Skip if Node.js is not explicitly listed in skills

        if p_id not in seen_projects:
            new_projects_alerted_count += 1
            
            title = p.get('title', 'بدون عنوان')
            description = p.get('description', 'توضیحات ندارد')
            
            budget_min = p.get('budget_min', 0)
            budget_max = p.get('budget_max', 0)
            
            budget_text = "توافقی"
            if budget_min > 0 and budget_max > 0:
                budget_text = f"از {budget_min:,} تا {budget_max:,} تومان"
            elif budget_min > 0:
                budget_text = f"بالای {budget_min:,} تومان"
            elif budget_max > 0:
                budget_text = f"تا {budget_max:,} تومان"

            # Extract skills titles for hashtags
            all_skills_titles = [s.get('title') for s in p.get('skills', []) if s.get('title')]
            hashtags = " ".join([f"#{skill.replace(' ', '')}" for skill in all_skills_titles])

            slug = p.get('slug')
            link = f"https://kaya.ir/projects/{slug}" if slug else "https://kaya.ir/projects"

            msg = (
                f"✨ پروژه Node.js جدید در کایا!\n\n"
                f"📌 عنوان: {title}\n"
                f"💰 بودجه: {budget_text}\n"
                f"📄 توضیحات:\n{description}\n\n" 
                f"🔗 مشاهده پروژه:\n{link}\n\n"
                f"{hashtags}"
            )
            logging.info(f"Sending alert for new Node.js project: {title}")
            send_bale_msg(msg)
    
    if new_projects_alerted_count > 0:
        logging.info(f"🎉 Found {new_projects_alerted_count} new Node.js projects.")
    else:
        logging.info("😴 No new Node.js projects found in this run.")

    # Save the state of all projects fetched in this run
    save_state(current_run_projects_state)
    save_last_run_time()

    logging.info("🏁 Kaya Monitor finished.")

if __name__ == "__main__":
    run_monitor()
