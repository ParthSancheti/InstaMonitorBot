#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Insta Status Monitor Bot — SINGLE FILE (web JSON first, then HTML fallback; HTML-safe messages)
Changes in this version:
- Admin-only commands (see bottom of /start message and code comments)
- Much simpler user messages (no timestamps, no debug “reason” lines)
- Cleaner status-change alerts (just emoji + status)

User Commands:
  /start
  /target <InstaID>
  /check
  /current
  /delay <minutes>
  /reset

Admin-Only Commands:
  /admin_list                         – show all users with target + status
  /admin_settarget <uid> <username>   – set a user’s target
  /admin_check <uid>                  – force a check for a user
  /admin_delay <uid> <minutes>        – set a user’s interval
  /admin_broadcast <message>          – send a message to all users
"""

# ========= PUT YOUR TELEGRAM BOT TOKEN HERE =========
BOT_TOKEN = ""   # <-- REPLACE THIS
# Optional: where to store the SQLite file:
DB_PATH = "./bot.db"
# Default auto-check interval in minutes:
DEFAULT_INTERVAL_MIN = 15
# Admin Telegram user IDs:
ADMIN_IDS = {}  # <-- REPLACE with your Telegram numeric ID(s)
# ====================================================

import asyncio
import os
import re
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Optional, Tuple
from html import escape

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ---------- Helpers ----------
def esc(s) -> str:
    return escape(str(s), quote=False)

def is_admin(update: Update) -> bool:
    uid = update.effective_user.id if update and update.effective_user else None
    return uid in ADMIN_IDS

# Limits/Defaults
MIN_INTERVAL = 5
MAX_INTERVAL = 360
REQUEST_TIMEOUT = 12.0
RETRY_ATTEMPTS = 1

# Emojis
ACTIVE_EMOJI = "🟢"
DEACTIVATED_EMOJI = "🔴"
UNKNOWN_EMOJI = "⚪"

# Instagram endpoints & headers
WEB_JSON_URLS = [
    "https://www.instagram.com/api/v1/users/web_profile_info/?username={username}",
    "https://i.instagram.com/api/v1/users/web_profile_info/?username={username}",
]
# Web UA and Mobile UA
WEB_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36"
)

INSTAGRAM_URL_TEMPLATE = "https://www.instagram.com/{username}/"
# lowercased markers (we .lower() the HTML before checking)
NOT_FOUND_MARKERS = [
    "sorry, this page isn't available",
    "the link you followed may be broken",
    "page may have been removed",
    "page not found",
]

# ---------- SQLite ----------
def db_init():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_user_id INTEGER PRIMARY KEY,
                target_username TEXT,
                last_known_status TEXT,
                last_checked_at TEXT,
                check_interval_minutes INTEGER DEFAULT 15,
                consecutive_errors INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()

def db_get_user(user_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE telegram_user_id = ?", (user_id,))
        return cur.fetchone()

def db_upsert_user(
    user_id: int,
    target_username: Optional[str] = None,
    last_known_status: Optional[str] = None,
    last_checked_at: Optional[str] = None,
    check_interval_minutes: Optional[int] = None,
    consecutive_errors: Optional[int] = None,
):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE telegram_user_id = ?", (user_id,))
        exists = cur.fetchone() is not None
        if not exists:
            cur.execute(
                """
                INSERT INTO users (telegram_user_id, target_username, last_known_status, last_checked_at, check_interval_minutes, consecutive_errors)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    target_username,
                    last_known_status if last_known_status is not None else "UNKNOWN",
                    last_checked_at,
                    check_interval_minutes if check_interval_minutes is not None else DEFAULT_INTERVAL_MIN,
                    consecutive_errors if consecutive_errors is not None else 0,
                ),
            )
        else:
            fields, values = [], []
            if target_username is not None:
                fields.append("target_username = ?"); values.append(target_username)
            if last_known_status is not None:
                fields.append("last_known_status = ?"); values.append(last_known_status)
            if last_checked_at is not None:
                fields.append("last_checked_at = ?"); values.append(last_checked_at)
            if check_interval_minutes is not None:
                fields.append("check_interval_minutes = ?"); values.append(check_interval_minutes)
            if consecutive_errors is not None:
                fields.append("consecutive_errors = ?"); values.append(consecutive_errors)
            if fields:
                values.append(user_id)
                cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE telegram_user_id = ?", values)
        conn.commit()

def db_reset_user(user_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE users
               SET target_username = NULL,
                   last_known_status = 'UNKNOWN',
                   last_checked_at = NULL,
                   consecutive_errors = 0
             WHERE telegram_user_id = ?
            """,
            (user_id,),
        )
        conn.commit()

def db_all_users():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        return cur.fetchall()

# ---------- HTTP helpers ----------
async def fetch_text(client: httpx.AsyncClient, url: str, headers: dict) -> httpx.Response:
    return await client.get(
        url,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
    )

# ---------- Status detector ----------
# Regexes for multiple reliable profile signals (HTML fallback)
OG_URL_RE = re.compile(
    r'<meta\s+property=["\']og:url["\']\s+content=["\']https?://(?:www\.)?instagram\.com/([^/]+)/?["\']',
    re.IGNORECASE,
)
CANONICAL_RE = re.compile(
    r'<link\s+rel=["\']canonical["\']\s+href=["\']https?://(?:www\.)?instagram\.com/([^/]+)/?["\']',
    re.IGNORECASE,
)
AL_ANDROID_RE = re.compile(
    r'<meta\s+property=["\']al:android:url["\']\s+content=["\']instagram://user\?username=([^"\']+)["\']',
    re.IGNORECASE,
)
AL_IOS_RE = re.compile(
    r'<meta\s+property=["\']al:ios:url["\']\s+content=["\']instagram://user\?username=([^"\']+)["\']',
    re.IGNORECASE,
)

def login_next_patterns(username: str):
    uname = re.escape(username)
    return [
        re.compile(rf'/accounts/login/\?next=/{uname}/?', re.IGNORECASE),
        re.compile(rf'/accounts/login/\?next=%2F{uname}%2F', re.IGNORECASE),
    ]

async def try_web_json(username: str) -> Tuple[Optional[str], str]:
    """
    Try Instagram's web JSON endpoints. Return:
      ("ACTIVE"/"DEACTIVATED"/None, debug_reason)
    """
    uname = username.strip()
    headers_web = {
        "User-Agent": WEB_UA,
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    }
    headers_mobile = {
        "User-Agent": MOBILE_UA,
        "Accept": "application/json, text/plain, */*",
        # Public Web App ID commonly used by Instagram web
        "X-IG-App-ID": "936619743392459",
    }

    async with httpx.AsyncClient() as client:
        for idx, tmpl in enumerate(WEB_JSON_URLS):
            url = tmpl.format(username=uname)
            headers = headers_web if idx == 0 else headers_mobile
            try:
                resp = await fetch_text(client, url, headers)
                code = resp.status_code
                text = resp.text
                if code == 200:
                    try:
                        payload = resp.json()
                    except json.JSONDecodeError:
                        payload = json.loads(text)
                    data = payload.get("data") if isinstance(payload, dict) else None
                    user = None
                    if isinstance(data, dict) and "user" in data:
                        user = data["user"]
                    elif isinstance(payload, dict) and "user" in payload:
                        user = payload["user"]
                    if isinstance(user, dict):
                        return "ACTIVE", f"web_json[{idx}] 200 user found"
                    return "DEACTIVATED", f"web_json[{idx}] 200 but no user"
                elif code == 404:
                    return "DEACTIVATED", f"web_json[{idx}] 404"
                elif code in (401, 403):
                    continue
                elif code in (429, 503):
                    return None, f"web_json[{idx}] {code} limited"
                else:
                    continue
            except Exception:
                continue

    return None, "web_json none or blocked"

async def get_instagram_status(username: str) -> Tuple[str, str]:
    """
    Returns: ("ACTIVE" | "DEACTIVATED" | "UNKNOWN", debug_info)
    Strategy:
      1) Try web JSON endpoints (no login)
      2) Fallback HTML page markers
    """
    uname_lc = username.lower().strip("/")

    status_from_api, reason_api = await try_web_json(uname_lc)
    if status_from_api is not None:
        return status_from_api, reason_api

    url = INSTAGRAM_URL_TEMPLATE.format(username=uname_lc)
    async with httpx.AsyncClient() as client:
        attempt = 0
        while attempt <= RETRY_ATTEMPTS:
            try:
                resp = await client.get(
                    url,
                    headers={
                        "User-Agent": WEB_UA,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                    },
                    timeout=REQUEST_TIMEOUT,
                    follow_redirects=True,
                )
                code = resp.status_code
                body = resp.text
                lowered = body.lower()

                if code in (404, 410):
                    return "DEACTIVATED", f"html {code}"

                if code == 200:
                    if any(marker in lowered for marker in NOT_FOUND_MARKERS):
                        return "DEACTIVATED", "html 200 not-available marker"

                    m1 = OG_URL_RE.search(body)
                    if m1 and m1.group(1).lower() == uname_lc:
                        return "ACTIVE", "html og:url match"

                    m2 = CANONICAL_RE.search(body)
                    if m2 and m2.group(1).lower() == uname_lc:
                        return "ACTIVE", "html canonical match"

                    for pat in login_next_patterns(uname_lc):
                        if pat.search(lowered):
                            return "ACTIVE", "html login next=/username/"

                    a1 = AL_ANDROID_RE.search(body)
                    if a1 and a1.group(1).lower() == uname_lc:
                        return "ACTIVE", "html al:android match"

                    a2 = AL_IOS_RE.search(body)
                    if a2 and a2.group(1).lower() == uname_lc:
                        return "ACTIVE", "html al:ios match"

                    return "UNKNOWN", "html 200 no reliable markers"

                if code in (429, 503):
                    return "UNKNOWN", f"html {code} limited"

                return "UNKNOWN", f"html {code} unexpected"

            except Exception:
                attempt += 1
                await asyncio.sleep(1.0 + 0.5 * attempt)

    return "UNKNOWN", "exception while fetching"

# ---------- Scheduler ----------
scheduler: Optional[AsyncIOScheduler] = None
JOB_PREFIX = "user_job_"

def job_id_for(user_id: int) -> str:
    return f"{JOB_PREFIX}{user_id}"

def schedule_user_job(user_row, application: Application):
    global scheduler
    if scheduler is None:
        return
    user_id = user_row["telegram_user_id"]
    interval = int(user_row["check_interval_minutes"] or DEFAULT_INTERVAL_MIN)
    interval = max(MIN_INTERVAL, min(MAX_INTERVAL, interval))
    jid = job_id_for(user_id)

    try:
        scheduler.remove_job(jid)
    except Exception:
        pass

    trigger = IntervalTrigger(minutes=interval)
    scheduler.add_job(
        func=check_and_notify_user,
        trigger=trigger,
        id=jid,
        kwargs={"user_id": user_id, "application": application},
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

async def check_and_notify_user(user_id: int, application: Application):
    row = db_get_user(user_id)
    if row is None or not row["target_username"]:
        return

    username = row["target_username"]

    new_status, _reason = await get_instagram_status(username)
    old_status = row["last_known_status"] or "UNKNOWN"

    # Track last check and error counters internally
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db_upsert_user(user_id, last_checked_at=now_iso)

    if new_status == "UNKNOWN":
        db_upsert_user(user_id, consecutive_errors=(row["consecutive_errors"] or 0) + 1)
        return

    db_upsert_user(user_id, consecutive_errors=0)

    if new_status != old_status:
        db_upsert_user(user_id, last_known_status=new_status)
        e = ACTIVE_EMOJI if new_status == "ACTIVE" else DEACTIVATED_EMOJI
        # Simpler notification: no timestamp, no debug reason
        text = f"{e} <b>{esc(username)}</b> status is now <b>{esc(new_status)}</b>"
        try:
            await application.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
        except Exception:
            pass

# ---------- Utils ----------
USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")

def valid_username(u: str) -> bool:
    return bool(USERNAME_RE.match(u or ""))

def emoji_for(status: str) -> str:
    return ACTIVE_EMOJI if status == "ACTIVE" else DEACTIVATED_EMOJI if status == "DEACTIVATED" else UNKNOWN_EMOJI

# ---------- Command Handlers (Users) ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 <b>Insta Status Monitor</b>\n\n"
        "🛰️ I track one Instagram ID you choose and alert only when it switches between <b>ACTIVE</b> ✅ and <b>DEACTIVATED</b> 🚫.\n\n"
        "🧑‍💻 <b>User Commands</b>\n"
        "• <code><a href=\"tg://sendMessage?text=/target\">/target &lt;username&gt;</a></code> 🎯\n"
        "• <code><a href=\"tg://sendMessage?text=/check\">/check</a></code> ⚡\n"
        "• <code><a href=\"tg://sendMessage?text=/current\">/current</a></code> 🧪\n"
        "• <code><a href=\"tg://sendMessage?text=/delay\">/delay &lt;minutes&gt;</a></code> ⏱️\n"
        "• <code><a href=\"tg://sendMessage?text=/reset\">/reset</a></code> 🧹\n"
    )
    
    if is_admin(update):
        msg += (
            "\n🛡️ <b>Admin Commands</b>\n"
            "• <code><a href=\"tg://sendMessage?text=/admin_list\">/admin_list</a></code> 📜\n"
            "• <code><a href=\"tg://sendMessage?text=/admin_settarget\">/admin_settarget &lt;uid&gt; &lt;username&gt;</a></code> 🎯\n"
            "• <code><a href=\"tg://sendMessage?text=/admin_check\">/admin_check &lt;uid&gt;</a></code> 🔍\n"
            "• <code><a href=\"tg://sendMessage?text=/admin_delay\">/admin_delay &lt;uid&gt; &lt;m&gt;</a></code> ⏳\n"
            "• <code><a href=\"tg://sendMessage?text=/admin_broadcast\">/admin_broadcast &lt;text&gt;</a></code> 📣\n"
        )

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def target_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args or []
    if not args:
        await update.message.reply_text("📌 Use: <code><a href=\"tg://sendMessage?text=/target\">/target &lt;username&gt;</a></code>", parse_mode=ParseMode.HTML)
        return
    username = args[0].strip().lstrip("@")
    if not valid_username(username):
        await update.message.reply_text("🚫 Invalid username. Use letters, numbers, dot or underscore (max 30).")
        return

    db_upsert_user(user_id, target_username=username)
    await update.message.reply_text(f"🎯 Target set to <b>{esc(username)}</b>. Checking… ⏳", parse_mode=ParseMode.HTML)

    new_status, _reason = await get_instagram_status(username)
    db_upsert_user(user_id, last_known_status=new_status, consecutive_errors=0)

    e = emoji_for(new_status)
    await update.message.reply_text(
        f"{e} <b>{esc(username)}</b>: <b>{esc(new_status)}</b>",
        parse_mode=ParseMode.HTML,
    )

    row = db_get_user(user_id)
    schedule_user_job(row, context.application)

async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    row = db_get_user(user_id)
    if row is None or not row["target_username"]:
        await update.message.reply_text("❗ No target yet. Use <code><a href=\"tg://sendMessage?text=/target\">/target &lt;InstaID&gt;</a></code> first.", parse_mode=ParseMode.HTML)
        return
    username = row["target_username"]
    await update.message.reply_text(f"🔎 Checking <b>{esc(username)}</b>…", parse_mode=ParseMode.HTML)

    new_status, _reason = await get_instagram_status(username)
    old_status = row["last_known_status"] or "UNKNOWN"

    if new_status != "UNKNOWN":
        db_upsert_user(user_id, last_known_status=new_status, consecutive_errors=0)
    else:
        db_upsert_user(user_id, consecutive_errors=(row["consecutive_errors"] or 0) + 1)

    e = emoji_for(new_status)
    changed = " (changed 🔔)" if (new_status != "UNKNOWN" and new_status != old_status) else ""
    await update.message.reply_text(
        f"{e} <b>{esc(username)}</b>: <b>{esc(new_status)}</b>{changed}",
        parse_mode=ParseMode.HTML,
    )

async def current_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    row = db_get_user(user_id)
    if row is None or not row["target_username"]:
        await update.message.reply_text("❗ No target yet. Use <code><a href=\"tg://sendMessage?text=/target\">/target &lt;InstaID&gt;</a></code> first.", parse_mode=ParseMode.HTML)
        return
    username = row["target_username"]
    status = row["last_known_status"] or "UNKNOWN"
    e = emoji_for(status)
    await update.message.reply_text(
        f"ℹ️ <b>{esc(username)}</b>: {e} <b>{esc(status)}</b>",
        parse_mode=ParseMode.HTML,
    )

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_reset_user(user_id)
    global scheduler
    if scheduler is not None:
        try:
            scheduler.remove_job(job_id_for(user_id))
        except Exception:
            pass
    await update.message.reply_text("🧹 Cleared. Set a new target with <code><a href=\"tg://sendMessage?text=/target\">/target &lt;InstaID&gt;</a></code>.", parse_mode=ParseMode.HTML)

async def delay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args or []
    if not args:
        await update.message.reply_text(
            f"⏱️ Use: <code><a href=\"tg://sendMessage?text=/delay\">/delay &lt;minutes&gt;</a></code> ({MIN_INTERVAL}-{MAX_INTERVAL})",
            parse_mode=ParseMode.HTML,
        )
        return
    try:
        minutes = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Please send a number, e.g., <code>/delay 20</code>", parse_mode=ParseMode.HTML)
        return
    minutes = max(MIN_INTERVAL, min(MAX_INTERVAL, minutes))
    db_upsert_user(user_id, check_interval_minutes=minutes)
    row = db_get_user(user_id)
    schedule_user_job(row, context.application)
    await update.message.reply_text(f"⏱️ Interval set to <b>{minutes}</b> minutes. ✅", parse_mode=ParseMode.HTML)

# ---------- Admin Commands ----------
async def admin_only(update: Update) -> bool:
    if not is_admin(update):
        await update.message.reply_text("🛑 Admin only.")
        return False
    return True

async def admin_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return
    rows = db_all_users()
    if not rows:
        await update.message.reply_text("😶 No users yet.")
        return
    lines = ["👥 <b>Users</b>:", ""]  # header
    for r in rows:
        uid = r["telegram_user_id"]
        uname = r["target_username"] or "-"
        status = r["last_known_status"] or "UNKNOWN"
        interval = r["check_interval_minutes"] or DEFAULT_INTERVAL_MIN
        lines.append(f"• {uid}: {uname} – {status} ({interval}m)")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def admin_settarget_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("🧩 Use: <code>/admin_settarget &lt;uid&gt; &lt;username&gt;</code>", parse_mode=ParseMode.HTML)
        return
    try:
        uid = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ First argument must be a user ID number.")
        return
    username = args[1].lstrip("@")
    if not valid_username(username):
        await update.message.reply_text("🚫 Invalid username.")
        return
    db_upsert_user(uid, target_username=username)
    await update.message.reply_text(f"✅ OK. Target for <b>{uid}</b> set to <b>{esc(username)}</b>.", parse_mode=ParseMode.HTML)

async def admin_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("🧪 Use: <code>/admin_check &lt;uid&gt;</code>", parse_mode=ParseMode.HTML)
        return
    try:
        uid = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ User ID must be a number.")
        return
    row = db_get_user(uid)
    if not row or not row["target_username"]:
        await update.message.reply_text("🙅 That user has no target.")
        return
    username = row["target_username"]
    new_status, _ = await get_instagram_status(username)
    if new_status != "UNKNOWN":
        db_upsert_user(uid, last_known_status=new_status, consecutive_errors=0)
    e = emoji_for(new_status)
    await update.message.reply_text(f"🧪 {uid}: {username} -> {e} {new_status}", parse_mode=ParseMode.HTML)

async def admin_delay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("⏳ Use: <code>/admin_delay &lt;uid&gt; &lt;minutes&gt;</code>", parse_mode=ParseMode.HTML)
        return
    try:
        uid = int(args[0])
        minutes = int(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Both uid and minutes must be numbers.")
        return
    minutes = max(MIN_INTERVAL, min(MAX_INTERVAL, minutes))
    db_upsert_user(uid, check_interval_minutes=minutes)
    await update.message.reply_text(f"✅ OK. Interval for <b>{uid}</b> is <b>{minutes}</b> minutes.", parse_mode=ParseMode.HTML)

async def admin_broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return
    text = " ".join(context.args or [])
    if not text:
        await update.message.reply_text("📣 Use: <code>/admin_broadcast &lt;message&gt;</code>", parse_mode=ParseMode.HTML)
        return
    n_ok = 0
    for r in db_all_users():
        try:
            await context.application.bot.send_message(chat_id=r["telegram_user_id"], text=text)
            n_ok += 1
        except Exception:
            pass
    await update.message.reply_text(f"📤 Sent to <b>{n_ok}</b> user(s).", parse_mode=ParseMode.HTML)

# ---------- Bootstrap ----------
async def on_startup(application: Application):
    db_init()
    global scheduler
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.start()
    for row in db_all_users():
        if row["target_username"]:
            schedule_user_job(row, application)

def build_application() -> Application:
    if not BOT_TOKEN or BOT_TOKEN.strip() == "" or "PASTE_YOUR_BOT_TOKEN_HERE" in BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty. Open the file and set your bot token at the top.")
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(on_startup)
        .build()
    )
    # User commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("target", target_cmd))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("current", current_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("delay", delay_cmd))
    # Admin commands
    app.add_handler(CommandHandler("admin_list", admin_list_cmd))
    app.add_handler(CommandHandler("admin_settarget", admin_settarget_cmd))
    app.add_handler(CommandHandler("admin_check", admin_check_cmd))
    app.add_handler(CommandHandler("admin_delay", admin_delay_cmd))
    app.add_handler(CommandHandler("admin_broadcast", admin_broadcast_cmd))
    return app


def main():
    app = build_application()
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=2.0,
        timeout=30,
    )

if __name__ == "__main__":
    main()

