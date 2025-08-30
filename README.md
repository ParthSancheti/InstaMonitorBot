# **InstaMonitorBot** 📱

**Small Description:**  
A Telegram bot that monitors Instagram accounts and notifies you when their status changes ✅❌⚠️.  
Works for public & private accounts. Built with **Python** + **python-telegram-bot**.

<p align="center">
  <img src="https://github.com/user-attachments/assets/c6945438-e273-4953-b32b-db0fdecf46b2" width="80%" alt="InstaMonitorBot Banner" />
</p>

---

## **Features** ✨

* 🎯 Each user can set their own Instagram account to monitor  
* ⏱ Auto-check every 15 minutes (customizable per user with `/delay`)  
* 🔔 Notifications **only when status changes**  
* 🔍 Force check anytime with `/check`  
* ♻️ Reset your account with `/reset`  
* 📊 View last known status with `/current`  
* Emoji-rich, simple, and user-friendly messages  

---

## *Try It Out*

<div align="center">
  <a href="https://t.me/InstaAccReactivation_bot">
    <img src="https://github.com/user-attachments/assets/ae45c8a9-38b1-4802-b98c-0140e57cc50b" width="220" style="border-radius:50px;"/>
  </a>
</div>

---

## **How It Works** ⚙️

* Built using **Python 3.11+**
* Libraries:
  * [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)  
  * [httpx](https://www.python-httpx.org/)  
  * [APScheduler](https://apscheduler.readthedocs.io/en/stable/)  
* Uses Instagram **public web JSON API** (with HTML fallback for reliability)  
* Stores per-user settings in a **SQLite DB**  
* Scheduler runs every X minutes (default 15) and notifies only if the status changes  

---

## 🎬 Preview

<p align="center">
  <img src="https://github.com/user-attachments/assets/70bf2dc7-0b43-47e6-89c5-59e9d5e5d213" width="40%" alt="InstaMonitorBot Demo 1" />
  <br />
</p>

---

## **Getting Started** 🚀

### **1. Create Your Telegram Bot**
1. Open Telegram → search for **@BotFather**.  
2. Send `/newbot` and follow the steps.  
3. Copy the **bot token** provided.

---

### **2. Clone and Setup Locally**
```bash
git clone https://github.com/<your-username>/InstaMonitorBot.git
cd InstaMonitorBot
python3 -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
````

*Or install manually:*

```bash
pip install "python-telegram-bot==21.10" "httpx==0.28.1" "apscheduler==3.10.4"
```

---

### **3. Configure**

Open `main.py` and paste your **bot token** at the top:

```python
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
```

---

### **4. Run Locally**

```bash
python main.py
```

Start chatting with your bot on Telegram 🎉

---

### **5. Commands**

| Command              | Description                       |
| -------------------- | --------------------------------- |
| `/start`             | Welcome + list of commands        |
| `/target <username>` | Set Instagram username to monitor |
| `/check`             | Force immediate status check      |
| `/current`           | Show last known status            |
| `/reset`             | Reset stored target and data      |
| `/delay <minutes>`   | Set auto-check interval           |

---

## **Deploy for 24×7 Hosting** ☁️

You have multiple options:

### 🔹 PythonAnywhere (quickest)

* Free tier has CPU limits → bot slows down after \~100 seconds/day.
* Works best if you upgrade.

**Steps:**

```bash
python3 -m venv .venv
pip install -r requirements.txt
python3 main.py
```

Run in **Always-on tasks** (paid plan).

---

### 🔹 Render (recommended free option)

* Free tier gives 750h/month (\~24×7).
* Bots should be set up in **webhook mode** to save CPU.
* Add **cron-job.org** to hit `/cron` endpoint every 15 minutes for checks.

---

### 🔹 Railway

* Free tier: 500h/month.
* Similar to Render, better for webhook mode.

---

### 🔹 Replit

* Run with `keep_alive` (Flask) + [UptimeRobot](https://uptimerobot.com) pings.
* Can sleep or reset sometimes.

---

## **Troubleshooting** 🔧

* **Bot not replying?**

  * Double-check your token.
  * Ensure you started the chat with your bot in Telegram.
  * If on Render/Railway, make sure webhook is set with:

    ```
    https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=<YOUR_APP_URL>/webhook/<SECRET>
    ```
* **Always UNKNOWN?**

  * Instagram sometimes rate-limits → will retry next cycle.
  * Private accounts are shown as **ACTIVE**.
* **PythonAnywhere free tier very slow?**

  * That’s a CPU quota issue — use Render/Railway instead.

---

## **License**

MIT License © 2025

---

## 🔗 Connect With Me

<p align="center">
  <a href="https://instagram.com/parth_sancheti"><img src="https://user-images.githubusercontent.com/74038190/235294013-a33e5c43-a01c-43f6-b44d-a406d8b4ab75.gif" height="40"/></a>
  <a href="https://wa.me/+918275994253"><img src="https://user-images.githubusercontent.com/74038190/235294019-40007353-6219-4ec5-b661-b3c35136dd0b.gif" height="40"/></a>
  <a href="https://t.me/parth_sancheti"><img src="https://github.com/user-attachments/assets/0e431c33-dfa6-463a-8b52-7e729de03b12" height="40"/></a>
</p>
