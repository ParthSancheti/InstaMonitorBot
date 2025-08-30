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
* Friendly emoji-rich messages and HTML-safe formatting  

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
* Uses Instagram **public web JSON API** (with fallback to HTML heuristics)  
* SQLite database per user: stores target, last status, last check time, and interval  
* Scheduler checks every X minutes (default 15) and notifies only on change  

---

## 🎬 Preview

<p align="center">
  <img src="https://github.com/user-attachments/assets/66b556c4-0d95-4d0d-a0dd-81c3197ee8a1" width="80%" alt="InstaMonitorBot Demo 1" />
  <br />
  <img src="https://github.com/user-attachments/assets/432a51f7-b2df-496f-9389-1dfb6dc6aa44" width="80%" alt="InstaMonitorBot Demo 2" />
  <br />
  <img src="https://github.com/user-attachments/assets/fd768c70-d367-4e03-b9d8-11748c7d46a1" width="80%" alt="InstaMonitorBot Demo 3" />
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
source .venv/bin/activate   # (on Windows: .venv\Scripts\activate)
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

### **4. Run**

```bash
python main.py
```

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

## **24×7 Hosting Options** ☁️

### 🔹 PythonAnywhere (simplest)

* Upload `main.py`
* Install requirements in Bash console
* Use **Always-on tasks** (paid plan)
* Command:

  ```
  python3 /home/<yourusername>/main.py
  ```

### 🔹 Railway / Render (webhook mode)

* Fork repo → Deploy to Railway/Render
* Add env vars:

  * `BOT_TOKEN` = your Telegram token
  * `WEBHOOK_URL` = your app URL (`https://yourapp.up.railway.app`)
* The bot switches to webhook mode automatically for 24/7 hosting.

---

## **Notes** 📝

* Avoid spamming `/check` to prevent Instagram **rate-limits (429)**.
* Private accounts are treated as **ACTIVE ✅** (if accessible).
* Notifications are sent **only when the status changes**.

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
```
