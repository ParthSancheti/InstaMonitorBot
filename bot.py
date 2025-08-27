import logging
import asyncio
import instaloader
from telegram import Update, ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === Your Bot Token ===
BOT_TOKEN = "8186493762:AAG1bJ9D8Cty8LTsmQDI_kLFyT7HNd7UP8I"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stores user data: {chat_id: {"username": str, "status": str, "interval": int}}
user_targets = {}

L = instaloader.Instaloader()

# --- Instagram status checker ---
def check_instagram_status(username: str):
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        return "Active ✅"
    except Exception:
        return "Deactivated ❌"

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "🎯 /target <username> → Set Instagram account\n"
        "🔍 /check → Check status now\n"
        "⏱ /interval <minutes> → Change auto-check interval (default 15)\n"
        "📊 /current → Last known status\n"
        "♻️ /reset → Clear your settings\n\n"
        "🔔 I’ll only notify you when the status *changes*!"
    )

async def target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /target <username>")
        return
    username = context.args[0]
    chat_id = update.message.chat_id
    status = check_instagram_status(username)
    user_targets[chat_id] = {"username": username, "status": status, "interval": 15}
    await update.message.reply_text(
        f"🎯 Target set to *{username}*\nCurrent status: {status}",
        parse_mode=ParseMode.MARKDOWN
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in user_targets:
        await update.message.reply_text("⚠️ No account set. Use /target first.")
        return
    username = user_targets[chat_id]["username"]
    status = check_instagram_status(username)
    await update.message.reply_text(f"🔍 *{username}* → {status}", parse_mode=ParseMode.MARKDOWN)

async def current(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in user_targets:
        await update.message.reply_text("⚠️ No account set. Use /target first.")
        return
    data = user_targets[chat_id]
    await update.message.reply_text(
        f"📊 Last known status of *{data['username']}*: {data['status']}\n"
        f"⏱ Auto-check every {data['interval']} min",
        parse_mode=ParseMode.MARKDOWN
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_targets.pop(chat_id, None)
    await update.message.reply_text("♻️ Target cleared. Use /target again.")

async def interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in user_targets:
        await update.message.reply_text("⚠️ No account set. Use /target first.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ Usage: /interval <minutes>")
        return
    minutes = int(context.args[0])
    user_targets[chat_id]["interval"] = minutes
    await update.message.reply_text(f"⏱ Interval updated to {minutes} minutes.")

# --- Auto checker ---
async def auto_check(app: Application):
    for chat_id, data in list(user_targets.items()):
        username = data["username"]
        new_status = check_instagram_status(username)
        if new_status != data["status"]:  # Notify only on change
            user_targets[chat_id]["status"] = new_status
            await app.bot.send_message(
                chat_id, f"🔔 *{username}* changed status → {new_status}",
                parse_mode=ParseMode.MARKDOWN
            )

# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("target", target))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("current", current))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("interval", interval))

    # Scheduler (checks every 15 min by default)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(auto_check(app)), "interval", minutes=15)
    scheduler.start()

    logger.info("🚀 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
