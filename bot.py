import os
import instaloader
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")   # Your Telegram ID (get from @userinfobot)
USERNAME = os.getenv("USERNAME") # Instagram target username

L = instaloader.Instaloader()

def check_status(username):
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        return "Active ✅"
    except Exception:
        return "Deactivated ❌"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def main():
    status = check_status(USERNAME)
    send_message(f"🔍 {USERNAME} → {status}")

if __name__ == "__main__":
    main()
