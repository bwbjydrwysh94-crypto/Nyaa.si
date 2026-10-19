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
    "@All_anime_c"  # ضع هنا معرف قناتك الخاصة بجميع الأنميات
)
URL = "https://witanime.net/"
RECORD_FILE = "sent_witanime_all.txt"


def load_sent():
  if os.path.exists(RECORD_FILE):
    with open(RECORD_FILE, "r", encoding="utf-8") as f:
      return set(f.read().splitlines())
  return set()


def save_sent(title):
  with open(RECORD_FILE, "a", encoding="utf-8") as f:
    f.write(title + "\n")


def send_telegram_photo(photo_url, caption):
  api_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
  payload = {
      "chat_id": CHANNEL_USERNAME,
      "photo": photo_url,
      "caption": caption,
      "parse_mode": "Markdown",
  }
  try:
    response = requests.post(api_url, data=payload)
    if response.status_code != 200:
      send_telegram_text(caption)
  except Exception as e:
    print(f"خطأ في إرسال الصورة: {e}")
    send_telegram_text(caption)


def send_telegram_text(message):
  api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
  payload = {
      "chat_id": CHANNEL_USERNAME,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": False,
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
        items = soup.find_all("div", class_="episodes-card")

        for item in items:
          # استخراج اسم الحلقة بالعربي
          title_tag = item.find("div", class_="episodes-card-title")
          title = title_tag.get_text(strip=True) if title_tag else ""

          # استخراج رابط المشاهدة
          link_tag = item.find("a")
          link = link_tag.get("href") if link_tag else ""

          # استخراج صورة الأنمي (البوستر)
          img_tag = item.find("img")
          img_url = ""
          if img_tag:
            img_url = (
                img_tag.get("data-src")
                or img_tag.get("src")
                or img_tag.get("data-lazy-src")
            )

          if title and title not in sent_items:
            msg = (
                f"🔥 *حلقة جديدة مترجمة*\n\n📌 *{title}*\n\n🔗"
                f" [اضغط هنا للمشاهدة والتحميل]({link})\n\n🌐 المصدر:"
                f" Witanime"
            )

            if img_url:
              send_telegram_photo(img_url, msg)
            else:
              send_telegram_text(msg)

            save_sent(title)
            time.sleep(2)
    except Exception as e:
      print(f"خطأ في فحص موقع Witanime: {e}")

    # فحص الموقع كل 10 دقائق لجلب كل جديد
    time.sleep(600)


@app.route("/")
def home():
  return "Witanime All Episodes Bot is Running 24/7!"


if __name__ == "__main__":
  t = threading.Thread(target=check_loop)
  t.daemon = True
  t.start()

  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
