import requests
from bs4 import BeautifulSoup

URL = "https://kaya.ir/projects/programming/backend-development"

BALE_TOKEN = "1230631087:hTpemS-3QOS4mfJNcIR7tcXVkzxJII7Qxhk"
CHAT_ID = "293358612"


def send_message(text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    })

def run():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a", href=True)

    for a in links:
        href = a["href"]

        if "/projects/" in href:
            title = a.get_text(strip=True)

            if len(title) > 5:
                link = "https://kaya.ir" + href

                msg = f"📌 {title}\n\n{link}"

                send_message(msg)
                break

run()

