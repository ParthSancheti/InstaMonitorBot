# **InstaMonitorBot** 📱

**Small Description:**
A Telegram bot that monitors Instagram accounts and notifies you when their status changes ✅❌⚠️. Works for public & private accounts.

<p align="center">
  <img src="https://github.com/user-attachments/assets/c6945438-e273-4953-b32b-db0fdecf46b2" width="80%" alt="HeyMelody Logo" />
</p>

---

## **Features** ✨

* 🎯 Set your own Instagram account to monitor
* ⏱ Auto-check every 15 minutes (customizable per user)
* 🔔 Notifications only on **status change**
* 🔍 Force check anytime with `/check`
* ♻️ Reset your account with `/reset`
* 📊 View last known status with `/current`
* Friendly emoji-rich messages and Markdown formatting

---
## *Try It Out*

<div align="center">
  <a href="https://t.me/InstaAccReactivation_bot">
    <img src="https://github.com/user-attachments/assets/ae45c8a9-38b1-4802-b98c-0140e57cc50b" width="220" style="border-radius:50px;"/>
  </a>
</div>

---

## **How It Works** ⚙️

* Built using **Google Apps Script**
* Stores per-user data with **PropertiesService**
* Uses `UrlFetchApp` to check Instagram account status
* Detects **ACTIVE**, **DEACTIVATED**, **PRIVATE**, and **RATE\_LIMITED**
* Sends notifications via **Telegram Bot API**
* Time-driven triggers handle auto-check every X minutes

---

## 🎬 Preview

<p align="center">
  <img src="https://github.com/user-attachments/assets/66b556c4-0d95-4d0d-a0dd-81c3197ee8a1" width="80%" alt="HeyMelody UI Demo" />
  <br />
    <img src="https://github.com/user-attachments/assets/432a51f7-b2df-496f-9389-1dfb6dc6aa44" width="80%" alt="HeyMelody UI Demo" />
  <br />
      <img src="https://github.com/user-attachments/assets/fd768c70-d367-4e03-b9d8-11748c7d46a1" width="80%" alt="HeyMelody UI Demo" />
  <br />
</p>

---

## **Getting Started** 🚀

### **1. Create Your Telegram Bot**

1. Open Telegram and search for **BotFather**.
2. Send `/newbot` and follow the instructions.
3. Copy the **bot token** provided.

---

### **2. Deploy the Bot on Google Apps Script**

1. Go to [Google Apps Script](https://script.google.com/) and create a new project.
2. Paste the **InstaMonitorBot code** into the editor.
3. Replace `YOUR_BOT_TOKEN` with your BotFather token.

---

### **3. Deploy as Web App**

1. Click **Deploy → New Deployment → Web App**
2. Set **Execute as:** Me
3. Set **Who has access:** Anyone, even anonymous
4. Copy the **Web App URL**

---

### **4. Set Telegram Webhook**

```bash
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_WEB_APP_URL>
```

---

### **5. Set Auto-Check Trigger**

1. In Apps Script, go to **Triggers (clock icon)**
2. Add trigger → Function: `autoCheckAllUsers` → Event source: Time-driven → Minutes timer → Every 15 minutes

---

### **6. Commands**

| Command              | Description                        |
| -------------------- | ---------------------------------- |
| `/start`             | Welcome message + list of commands |
| `/target <username>` | Set Instagram username to monitor  |
| `/check`             | Force immediate status check       |
| `/current`           | Show last known status             |
| `/reset`             | Reset stored target and data       |
| `/delay <minutes>`   | Set auto-check interval            |

---

### **7. Notes**

* Avoid frequent `/check` calls to prevent Instagram **rate-limit (429)**
* Private accounts are treated as **ACTIVE ✅**
* Notifications are sent **only when status changes**

---

### **8. Make Your Own Bot**

1. Fork this repository
2. Replace the bot token with your own
3. Deploy as Web App
4. Set up webhook & triggers
5. Start monitoring Instagram accounts via Telegram

---

### **9. License**

MIT License © 2025

---

I can also create a **ready-to-use GitHub template folder** with:

* `Code.gs` (full bot code)
* `README.md` (this file)
* `.gitignore` for Apps Script exports

This makes it **plug-and-play for anyone**.

## 🔗 Connect With Us

<p align="center">
  <a href="https://instagram.com/parth_sancheti"><img src="https://user-images.githubusercontent.com/74038190/235294013-a33e5c43-a01c-43f6-b44d-a406d8b4ab75.gif" height="40"/></a>
  <a href="https://wa.me/+918275994253"><img src="https://user-images.githubusercontent.com/74038190/235294019-40007353-6219-4ec5-b661-b3c35136dd0b.gif" height="40"/></a>
  <a href="https://t.me/parth_sancheti"><img src="https://github.com/user-attachments/assets/0e431c33-dfa6-463a-8b52-7e729de03b12" height="40"/></a>
</p>

