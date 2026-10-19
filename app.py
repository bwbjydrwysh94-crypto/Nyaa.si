import os
import threading
import time
from bs4 import BeautifulSoup
from flask import Flask
import requests

app = Flask(__name__)

# === بيانات التوكن وقناتك الجديدة ===
TOKEN = "8820447124:AAGX1xh2RXRG2NLD4XXBQ6ajVmyVtFm9e-A"
CHANNEL_USERNAME = (
    "@All_anime_c"  # ضع هنا معرف قناتك الثانية الخاصة بجميع الأنميات
)
URL = "https://nyaa.si/"
RECORD_FILE = "sent_nyaa.txt"


def load_sent():
  if os.path.exists(RECORD_FILE):
    with open(RECORD_FILE, "r", encoding="utf-8") as f:
      return set(f.read().splitlines())
  return set()


def save_sent(title):
  with open(RECORD_FILE, "a", encoding="utf-8") as f:
    f.write(title + "\n")


def send_telegram(message):
  api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
  payload = {
      "chat_id": CHANNEL_USERNAME,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": True,
  }
  try:
    requests.post(api_url, data=payload)
  except Exception as e:
    print(f"خطأ في إرسال التليجرام: {e}")


def check_loop():
  while True:
    try:
      sent_items = load_sent()
      headers = {
          "User-Agent": (
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          )
      }
      response = requests.get(URL, headers=headers, timeout=15)
      if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.torrent-list tbody tr")

        for row in rows:
          # استخراج عنوان الحلقة
          links = row.select("td:nth-child(2) a")
          title_link = None
          for l in links:
            href_val = l.get("href", "")
            if "view" in href_val:
              title_link = l
              break

          if title_link:
            title = title_link.get_text(strip=True)

            # استخراج رابط الماجنت (Magnet Link) المباشر
            magnet_tag = row.select_one('a[href^="magnet:?"]')
            magnet_link = magnet_tag.get("href") if magnet_tag else ""

            if title and title not in sent_items:
              if magnet_link:
                msg = (
                    f"🔥 *حلقة جديدة (جميع الأنميات)*\n\n📌 *{title}*\n\n🔗"
                    f" [اضغط هنا لتحميل الماجنت (Magnet)]({magnet_link})\n\n🌐"
                    f" المصدر: Nyaa.si"
                )
                send_telegram(msg)
                save_sent(title)
                time.sleep(2)
    except Exception as e:
      print(f"خطأ في فحص موقع Nyaa: {e}")

    # يفحص الموقع كل 10 دقائق لجلب الجديد فوراً
    time.sleep(600)


@app.route("/")
def home():
  return "Nyaa Anime Bot is Running 24/7!"


if __name__ == "__main__":
  t = threading.Thread(target=check_loop)
  t.daemon = True
  t.start()

  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
