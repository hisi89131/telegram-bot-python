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
        
# ---------- ADD ADMIN ---------- #

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /addadmin USER_ID")
        return

    user_id = int(context.args[0])
    admins.add(user_id)
    await update.message.reply_text(f"✅ Admin Added: {user_id}")


# ---------- REMOVE ADMIN ---------- #

async def removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /removeadmin USER_ID")
        return

    user_id = int(context.args[0])
    admins.discard(user_id)
    await update.message.reply_text(f"❌ Admin Removed: {user_id}")


# ---------- ADMIN LIST ---------- #

async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN_ID:
        return

    if not admins:
        await update.message.reply_text("No Sub Admins")
        return

    text = "🛠 Sub Admin List:\n"
    for a in admins:
        text += f"{a}\n"

    await update.message.reply_text(text)


# ---------- BAN USER ---------- #

async def banuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /banuser USER_ID")
        return

    user_id = int(context.args[0])
    banned_users.add(user_id)
    await update.message.reply_text(f"🚫 User Banned: {user_id}")


# ---------- UNBAN USER ---------- #

async def unbanuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /unbanuser USER_ID")
        return

    user_id = int(context.args[0])
    banned_users.discard(user_id)
    await update.message.reply_text(f"✅ User Unbanned: {user_id}")


# ---------- BAN LIST ---------- #

async def banlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN_ID:
        return

    if not banned_users:
        await update.message.reply_text("No Banned Users")
        return

    text = "🚫 Banned Users:\n"
    for u in banned_users:
        text += f"{u}\n"

    await update.message.reply_text(text)


# ---------- USER LIST ---------- #

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN_ID:
        return

    if not users:
        await update.message.reply_text("No Users Yet")
        return

    text = "👥 Users List:\n"
    for uid, uname in users.items():
        if uname:
            text += f"{uname} - {uid}\n"
        else:
            text += f"{uid}\n"

    await update.message.reply_text(text)

# ---------- MAIN ---------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("memberpanel", memberpanel))
    app.add_handler(CommandHandler("adminpanel", adminpanel))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("removeadmin", removeadmin))
    app.add_handler(CommandHandler("adminlist", adminlist))
    app.add_handler(CommandHandler("banuser", banuser))
    app.add_handler(CommandHandler("unbanuser", unbanuser))
    app.add_handler(CommandHandler("banlist", banlist))
    app.add_handler(CommandHandler("userlist", userlist))
    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
