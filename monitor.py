import requests
import json
import os
from datetime import datetime, timezone

# تنظیمات اصلی - علیرضا: اگر نیاز بود اینها را تغییر بده
API_URL = "https://ir.api.kaya.ir/api/v2/projects/projects?limit=20&offset=0&skills=500&fixed=false&hourly=false" # مهارت Node.js (ID 500)
BALE_TOKEN = "2115160012:v8oT43oUfR3Y3N5Xv6p8K4G3j8Z9Q2L1S6D5F4G3"
CHAT_ID = "293358612"
STATE_FILE = "seen_projects.json" # تغییر نام دادم به project_state.json برای وضوح بیشتر
LAST_RUN_FILE = "last_run.json" # برای ذخیره آخرین زمان اجرا

def send_bale_msg(text):
    """Sends a message to the specified Bale chat."""
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"📡 Bale API Response Status: {res.status_code}")
        if res.status_code != 200:
            print(f"❌ Bale API Error: {res.text}")
    except Exception as e:
        print(f"❌ Error sending message to Bale: {e}")

def run():
    print("🚀 Starting Kaya Monitor for Node.js Projects...")

    # 1. Load previous state and last run time
    current_seen_projects = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                current_seen_projects = json.load(f)
            print(f"📦 Loaded {len(current_seen_projects)} previous project entries.")
        except json.JSONDecodeError:
            print("⚠️ Could not decode previous project state, starting fresh.")
        except Exception as e:
            print(f"⚠️ Error loading previous project state: {e}, starting fresh.")

    # 2. Fetch projects from Kaya API
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        print(f"🌐 Requesting Kaya API: {API_URL}")
        response = requests.get(API_URL, headers=headers, timeout=20) # Increased timeout
        
        if response.status_code != 200:
            print(f"❌ Kaya API Error! Status: {response.status_code}")
            print(f"📄 Response Content: {response.text[:500]}...") # Log more of the response for debugging
            send_bale_msg(f"❌ خطا در دریافت پروژه‌ها از کایا: {response.status_code}\nمحتوا: {response.text[:100]}...")
            return

        projects_data = response.json().get('results', []) # Changed from 'data' to 'results'
        print(f"✅ Found {len(projects_data)} projects from API.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network or API connection error: {e}")
        send_bale_msg(f"❌ خطای شبکه/ارتباط با کایا: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON response from Kaya API: {e}")
        send_bale_msg(f"❌ خطای JSON از کایا: {e}")
        return
    except Exception as e:
        print(f"❌ An unexpected error occurred during API fetch: {e}")
        send_bale_msg(f"❌ خطای ناشناخته در دریافت از کایا: {e}")
        return

    # 3. Process new projects
    new_projects_found_count = 0
    updated_seen_projects = {} # To store all projects for the new state file

    for p in projects_data:
        p_id = str(p.get('id'))
        
        # Store all project details, keyed by ID for easy lookup
        # This allows us to detect changes in existing projects too, if needed
        updated_seen_projects[p_id] = p 

        if p_id not in current_seen_projects:
            new_projects_found_count += 1
            title = p.get('title', 'بدون عنوان')
            description_snippet = p.get('description', 'توضیحات ندارد')
            if len(description_snippet) > 150:
                description_snippet = description_snippet[:150] + "..."
            
            budget_min = p.get('budget_min', 0)
            budget_max = p.get('budget_max', 0)
            
            # Format budget
            budget_text = "توافقی"
            if budget_min > 0 and budget_max > 0:
                budget_text = f"از {budget_min:,} تا {budget_max:,} تومان"
            elif budget_min > 0:
                budget_text = f"بالای {budget_min:,} تومان"
            elif budget_max > 0:
                budget_text = f"تا {budget_max:,} تومان"

            # Extract skills
            skills = [s.get('title') for s in p.get('skills', []) if s.get('title')]
            skills_text = ", ".join(skills) if skills else "نامشخص"

            link = f"https://kaya.ir/projects/{p.get('slug', '')}" # Ensure slug exists

            msg = (
                f"✨ پروژه جدید در کایا (Node.js)!\n\n"
                f"📌 عنوان: {title}\n"
                f"💰 بودجه: {budget_text}\n"
                f"🛠 مهارت‌ها: {skills_text}\n"
                f"📄 توضیحات: {description_snippet}\n\n"
                f"🔗 مشاهده پروژه:\n{link}"
            )
            print(f"🔔 Sending alert for new project: {title}")
            send_bale_msg(msg)
    
    if new_projects_found_count > 0:
        print(f"🎉 Found {new_projects_found_count} new projects.")
    else:
        print("😴 No new projects found in this run.")

    # 4. Save updated state (all projects fetched in this run)
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(updated_seen_projects, f, indent=4, ensure_ascii=False)
        print("💾 Project state updated successfully.")
    except Exception as e:
        print(f"❌ Error saving project state: {e}")
        send_bale_msg(f"❌ خطا در ذخیره وضعیت پروژه: {e}")

    # 5. Save last successful run time
    try:
        with open(LAST_RUN_FILE, 'w') as f:
            json.dump({"last_run": datetime.now(timezone.utc).isoformat()}, f)
        print("⏱ Last run time saved.")
    except Exception as e:
        print(f"❌ Error saving last run time: {e}")

    print("🏁 Kaya Monitor finished.")

if __name__ == "__main__":
    run()
