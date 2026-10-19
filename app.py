import os
import threading
import time
from bs4 import BeautifulSoup
import cloudscraper
from flask import Flask
import requests

app = Flask(__name__)

# === بيانات التوكن وقناتك ===
TOKEN = "8820447124:AAGX1xh2RXRG2NLD4XXBQ6ajVmyVtFm9e-A"
CHANNEL_USERNAME = (
    "@All_anime_c"  # ضع معرف قناتك هنا بدقة وتأكد أن البوت مشرف
)
URL = "https://witanime.net/"
RECORD_FILE = "sent_witanime_all.txt"

# إنشاء كاشف قوي يتجاوز حماية المواقع (مثل Cloudflare)
scraper = cloudscraper.create_scraper()


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
    response = requests.post(api_url, data=payload, timeout=10)
    if response.status_code != 200:
      send_telegram_text(caption)
  except Exception:
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
    requests.post(api_url, data=payload, timeout=10)
  except Exception as e:
    print(f"خطأ في إرسال التيليجرام: {e}")


def check_loop():
  while True:
    try:
      sent_items = load_sent()
      # استخدام الكاشف القوي لسحب الموقع حتى لو كان محميأ
      response = scraper.get(URL, timeout=15)

      if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("div", class_="episodes-card")

        for item in items:
          title_tag = item.find("div", class_="episodes-card-title")
          title = title_tag.get_text(strip=True) if title_tag else ""

          link_tag = item.find("a")
          link = link_tag.get("href") if link_tag else ""

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
      print(f"خطأ في الاتصال بالموقع: {e}")

    # فحص الموقع كل 10 دقائق لجلب الجديد فوراً
    time.sleep(600)


@app.route("/")
def home():
  return "Ultimate Witanime Bot is Running 24/7!"


if __name__ == "__main__":
  t = threading.Thread(target=check_loop)
  t.daemon = True
  t.start()

  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
if __name__ == "__main__":
  # تشغيل حلقة فحص الأنمي في خلفية منفصلة
  bot_thread = threading.Thread(target=check_loop)
  bot_thread.daemon = True
  bot_thread.start()

  # تشغيل سيرفر الويب ليبقى السيرفر مستيقظاً على Render
  app.run(host="0.0.0.0", port=10000)
