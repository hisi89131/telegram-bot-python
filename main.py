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

BOT_TOKEN = "8232988598:AAFS_8fLi_f7FAi9Lcyb3HS4UmFQ_uwz0zA"
MAIN_ADMIN_ID = 1086634832

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

# -------- COMMAND STORAGE SYSTEM --------
command_storage = {}
command_creation_mode = {}
COMMAND_EXPIRY_HOURS = 24
edit_mode = {}

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
    
# -------- SUPPORT SYSTEM --------

support_mode = {}

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in banned_users:
        return

    support_mode[user_id] = True
    await update.message.reply_text("Send your support message now.")


async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Ignore if creating command
    if user_id in command_creation_mode:
        return

    # 🔹 Admin replying to support
    if update.message.reply_to_message:
        replied_text = update.message.reply_to_message.text

        if replied_text and "Support Message From:" in replied_text:
            original_user_id = int(
                replied_text.split("Support Message From:")[1]
                .split("\n")[0]
                .strip()
            )

            await context.bot.send_message(
                chat_id=original_user_id,
                text="Admin Reply:\n\n" + update.message.text
            )
            return

    # 🔹 User sending support message
    if support_mode.get(user_id):
        support_mode[user_id] = False

        await context.bot.send_message(
            chat_id=MAIN_ADMIN_ID,
            text=f"Support Message From: {user_id}\n\n{update.message.text}"
        )

        await update.message.reply_text("Support message sent.")

# ---------- SET COMMAND SYSTEM ----------

command_creation_mode = {}
command_storage = {}
edit_mode = {}

import datetime
import pytz

tz = pytz.timezone("Asia/Kolkata")

# ---------------- SET ----------------

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_role(user_id)

    if role not in ["main_admin", "admin"]:
        await update.message.reply_text("❌ Access Denied")
        return

    if not context.args:
        await update.message.reply_text("Usage: /set command_name")
        return

    cmd_name = context.args[0].lower()

    command_creation_mode[user_id] = {
        "name": cmd_name,
        "data": [],
        "owner": user_id,
    }

    await update.message.reply_text(
        f"📦 Send files/text for /{cmd_name}\nWhen finished type /done"
    )

# ---------------- COLLECT DATA ----------------

async def collect_command_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # If creating new command
    if user_id in command_creation_mode:
        command_creation_mode[user_id]["data"].append(update.message)
        await update.message.reply_text("✅ Added")
        return

    # If editing command
    if user_id in edit_mode:
        cmd_name = edit_mode[user_id]
        command_storage[cmd_name]["data"].append(update.message)
        await update.message.reply_text("✅ Added (Edit Mode)")
        return

# ---------------- DONE ----------------

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # New command save
    if user_id in command_creation_mode:
        cmd_data = command_creation_mode[user_id]
        cmd_name = cmd_data["name"]

        command_storage[cmd_name] = {
            "data": cmd_data["data"],
            "owner": cmd_data["owner"],
            "time": datetime.datetime.now(tz).strftime("%d %B %Y | %I:%M %p IST")
        }

        del command_creation_mode[user_id]

        await update.message.reply_text(f"✅ Command /{cmd_name} saved successfully!")

        # Broadcast
        for uid in users:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=f"🚀 Key '{cmd_name}' uploaded/updated successfully!"
                )
            except:
                pass

        return

    # Edit save
    if user_id in edit_mode:
        cmd_name = edit_mode[user_id]
        del edit_mode[user_id]
        await update.message.reply_text(f"✅ Command /{cmd_name} updated successfully!")
        return

    await update.message.reply_text("❌ You are not creating or editing any command.")

# ---------------- CUSTOM COMMAND HANDLER ----------------

async def custom_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd_name = update.message.text[1:].lower()

    if cmd_name not in command_storage:
        return

    cmd_data = command_storage[cmd_name]

    for msg in cmd_data["data"]:
        try:
            await msg.copy(update.effective_chat.id)
        except:
            pass

    await update.message.reply_text(
        f"🕒 Uploaded On: {cmd_data['time']}"
    )     
    
# ---------- CMD LIST ---------- #

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_role(user_id)

    text = "📜 Available Commands:\n"

    if role == "main_admin":
        text += "All Custom Commands:\n"
        for cmd_name in custom_commands:
            text += f"/{cmd_name}\n"

    elif role == "admin":
        text += "Your Custom Commands:\n"
        for cmd_name, data in custom_commands.items():
            if data["owner"] == user_id:
                text += f"/{cmd_name}\n"

    else:
        for cmd_name in custom_commands:
            text += f"/{cmd_name}\n"
        text += "\n/support"

    await update.message.reply_text(text)

# -------- DELETE COMMAND --------

async def delcmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_role(user_id)

    # Command name missing
    if not context.args:
        await update.message.reply_text("Usage: /delcmd command_name")
        return

    cmd_name = context.args[0].lower()

    # Command not found
    if cmd_name not in command_storage:
        await update.message.reply_text("❌ Command not found.")
        return

    owner = command_storage[cmd_name]["owner"]

    # Main admin can delete any command
    if role == "main_admin":
        del command_storage[cmd_name]
        await update.message.reply_text(f"❌ /{cmd_name} deleted successfully.")
        return

    # Sub admin can delete only their own command
    if role == "admin" and owner == user_id:
        del command_storage[cmd_name]
        await update.message.reply_text(f"❌ /{cmd_name} deleted successfully.")
        return

    # Otherwise deny
    await update.message.reply_text("❌ You cannot delete this command.")

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
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("cmd", cmd))

    # ✅ SET SYSTEM
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("delcmd", delcmd))

    # ✅ FIRST collect files
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, collect_command_data))

    # ✅ THEN run custom commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_command_handler))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
