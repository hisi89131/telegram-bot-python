import logging
import pytz
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from config import MAIN_ADMIN_ID, MAIN_FORCE_CHANNEL, TIMEZONE

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8232988598:AAH16Uai8UwFKLdGkAt6rxSSZnGAThxGbzk"

# ---------- MEMORY STORAGE ---------- #

users = {}
admins = set()
admin_banned = set()
banned_users = set()
force_channels = {MAIN_FORCE_CHANNEL}
custom_commands = {}
editing_state = {}
support_warnings = {}

tz = pytz.timezone(TIMEZONE)


# ---------- ROLE CHECK ---------- #

def get_role(user_id):
    if user_id == MAIN_ADMIN_ID:
        return "main_admin"
    elif user_id in admins:
        return "admin"
    else:
        return "member"


# ---------- START ---------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id in banned_users:
        return

    users[user.id] = user.username

    role = get_role(user.id)

    if role == "main_admin":
        await update.message.reply_text("👑 Main Admin Panel\nUse /adminpanel")
    elif role == "admin":
        await update.message.reply_text("🛠 Sub Admin Panel\nUse /adminpanel")
    else:
        await update.message.reply_text("👤 Member Panel\nUse /memberpanel")


# ---------- MEMBER PANEL ---------- #

async def memberpanel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Member Commands:\n"
        "/cmd\n"
        "/support"
    )


# ---------- ADMIN PANEL ---------- #

async def adminpanel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = get_role(update.effective_user.id)

    if role == "main_admin":
        await update.message.reply_text(
            "Main Admin Commands:\n"
            "/addadmin\n"
            "/removeadmin\n"
            "/adminlist\n"
            "/banuser\n"
            "/unbanuser\n"
            "/banlist\n"
            "/forceadd\n"
            "/forceremove\n"
            "/forcelist\n"
            "/set\n"
            "/edit\n"
            "/done\n"
            "/broadcast\n"
            "/userlist"
        )
    elif role == "admin":
        await update.message.reply_text(
            "Sub Admin Commands:\n"
            "/set\n"
            "/edit\n"
            "/done\n"
            "/cmd"
        )
    else:
        await update.message.reply_text("❌ Access Denied")


# ---------- MAIN ---------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("memberpanel", memberpanel))
    app.add_handler(CommandHandler("adminpanel", adminpanel))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
