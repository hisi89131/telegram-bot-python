# ==========================================
# STAGE 1 - CORE SETUP (PRODUCTION BASE)
# ==========================================

import datetime
import re
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==============================
# BOT CONFIG
# ==============================

BOT_TOKEN = "8531299371:AAG6_UoEJMcvAuv0XKPHirP2n-XoHVpitD8"
MAIN_ADMIN_ID = 1086634832

# IST Timezone
tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

print("Stage 1 Loaded Successfully")

# ==========================================
# STAGE 2 - GLOBAL MEMORY STRUCTURE
# ==========================================

# All private users
users = set()

# All groups where bot is added
groups = set()

# Sub Admins
admins = set()

# Banned members
banned_users = set()

# Banned admins
banned_admins = set()

# ==============================
# FORCE JOIN SYSTEM
# ==============================

# Structure:
# {
#   admin_id: {
#       "channel_id": -100xxxxxxxx,
#       "emoji": "🔥"
#   }
# }
force_join_channels = {}

# ==============================
# CUSTOM COMMAND STORAGE
# ==============================

# Structure:
# {
#   "cmdname": {
#       "owner": user_id,
#       "files": [ file_data_objects ],
#       "time": "IST TIME STRING"
#   }
# }
command_storage = {}

# Temporary command creation mode
# {
#   user_id: {
#       "name": cmdname,
#       "files": []
#   }
# }
command_creation_mode = {}

# ==============================
# SUPPORT SYSTEM MEMORY
# ==============================

support_mode = {}

# ==========================================
# STAGE 3 - ROLE SYSTEM & SECURITY
# ==========================================

def get_role(user_id: int):
    if user_id == MAIN_ADMIN_ID:
        return "main_admin"
    elif user_id in admins:
        return "admin"
    else:
        return "member"


def is_banned(user_id: int):
    if user_id in banned_users:
        return True
    if user_id in banned_admins:
        return True
    return False


def can_use_admin_panel(user_id: int):
    role = get_role(user_id)
    if role in ["main_admin", "admin"] and user_id not in banned_admins:
        return True
    return False


def can_use_main_admin_only(user_id: int):
    if user_id == MAIN_ADMIN_ID:
        return True
    return False

# ==========================================
# STAGE 4 - START + TRACKING + FORCE JOIN
# ==========================================

async def check_force_join(user_id, context):
    if not force_join_channels:
        return True

    for admin_id, data in force_join_channels.items():
        channel_id = data["channel_id"]
        try:
            member = await context.bot.get_chat_member(channel_id, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False

    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    user_id = user.id

    # Ban check
    if is_banned(user_id):
        await update.message.reply_text("❌ You are banned from using this bot.")
        return

    # Track users & groups
    if chat.type == "private":
        users.add(user_id)
    else:
        groups.add(chat.id)

    # Force join check (private only)
    if chat.type == "private":
        joined = await check_force_join(user_id, context)

        if not joined:
            buttons = []
            for admin_id, data in force_join_channels.items():
                channel_id = data["channel_id"]
                emoji = data["emoji"]
                buttons.append(
                    [InlineKeyboardButton(f"{emoji} Join Channel", url=f"https://t.me/{str(channel_id).replace('-100','')}")]
                )

            buttons.append([InlineKeyboardButton("✅ Verify", callback_data="verify_join")])

            reply_markup = InlineKeyboardMarkup(buttons)

            await update.message.reply_text(
                "⚠️ You must join required channels before using this bot.",
                reply_markup=reply_markup
            )
            return

    # Role-based start message
    role = get_role(user_id)

    if role == "main_admin":
        await update.message.reply_text("👑 Main Admin Panel\nUse /adminpanel")
    elif role == "admin":
        await update.message.reply_text("🛠 Admin Panel\nUse /adminpanel")
    else:
        await update.message.reply_text("👤 Member Panel\nUse /memberpanel")


async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    joined = await check_force_join(user_id, context)

    if joined:
        await query.answer("Verified Successfully!", show_alert=True)
        await query.edit_message_text("✅ Verification Successful! Now use /start again.")
    else:
        await query.answer("❌ You have not joined all required channels.", show_alert=True)

# ==========================================
# STAGE 5 - ADMIN PANEL & USER MANAGEMENT
# ==========================================

async def adminpanel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_admin_panel(user_id):
        await update.message.reply_text("❌ Access Denied.")
        return

    role = get_role(user_id)

    text = "🛠 Admin Panel\n\n"

    # MAIN ADMIN COMMANDS
    if role == "main_admin":
        text += (
            "/addadmin USER_ID\n"
            "/removeadmin USER_ID\n"
            "/adminlist\n"
            "/userlist\n"
            "/ban USER_ID\n"
            "/unban USER_ID\n"
            "/banlist\n"
            "/broadcast (reply required)\n"
            "\n"
            "/addforce CHANNEL_ID EMOJI\n"
            "/removeforce ADMIN_ID\n"
            "/forcelist\n"
            "\n"
            "/set command_name\n"
            "/done\n"
            "/cmd\n"
            "/delcmd command_name\n"
            "/removefile command_name file_number\n"
        )

    # SUB ADMIN COMMANDS
    elif role == "admin":
        text += (
            "/addforce CHANNEL_ID EMOJI\n"
            "/removeforce\n"
            "/forcelist\n"
            "\n"
            "/set command_name\n"
            "/done\n"
            "/cmd\n"
            "/delcmd command_name\n"
            "/removefile command_name file_number\n"
        )

    await update.message.reply_text(text)


# Add Admin
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_main_admin_only(user_id):
        await update.message.reply_text("❌ Only Main Admin Allowed.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /addadmin USER_ID")
        return

    try:
        new_admin = int(context.args[0])
        admins.add(new_admin)
        await update.message.reply_text(f"✅ {new_admin} added as admin.")
    except:
        await update.message.reply_text("❌ Invalid USER_ID")


# Remove Admin
async def removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_main_admin_only(user_id):
        await update.message.reply_text("❌ Only Main Admin Allowed.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /removeadmin USER_ID")
        return

    try:
        remove_id = int(context.args[0])
        admins.discard(remove_id)
        await update.message.reply_text(f"❌ {remove_id} removed from admin.")
    except:
        await update.message.reply_text("❌ Invalid USER_ID")


# Admin List
async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_main_admin_only(user_id):
        await update.message.reply_text("❌ Only Main Admin Allowed.")
        return

    if not admins:
        await update.message.reply_text("No Sub Admins.")
        return

    text = "👑 Sub Admin List:\n\n"
    for a in admins:
        text += f"{a}\n"

    await update.message.reply_text(text)

# MEMBER PANEL FIX
async def memberpanel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if is_banned(update.effective_user.id):
            await update.message.reply_text("❌ You are banned.")
            return

        await update.message.reply_text("👤 Member Panel\nUse /cmd to see available commands")
# User List
async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_main_admin_only(user_id):
        await update.message.reply_text("❌ Only Main Admin Allowed.")
        return

    if not users:
        await update.message.reply_text("No Users Found.")
        return

    text = f"👥 Total Users: {len(users)}\n\n"

    for u in users:
        try:
            user_obj = await context.bot.get_chat(u)
            username = f"@{user_obj.username}" if user_obj.username else "No Username"
            text += f"{u} | {username}\n"
        except:
            text += f"{u}\n"

    await update.message.reply_text(text)

# Ban User
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_main_admin_only(user_id):
        await update.message.reply_text("❌ Only Main Admin Allowed.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /ban USER_ID")
        return

    try:
        target = int(context.args[0])

        if target in admins:
            banned_admins.add(target)
        else:
            banned_users.add(target)

        await update.message.reply_text(f"🚫 {target} banned successfully.")
    except:
        await update.message.reply_text("❌ Invalid USER_ID")


# Unban User
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_main_admin_only(user_id):
        await update.message.reply_text("❌ Only Main Admin Allowed.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /unban USER_ID")
        return

    try:
        target = int(context.args[0])
        banned_users.discard(target)
        banned_admins.discard(target)
        await update.message.reply_text(f"✅ {target} unbanned successfully.")
    except:
        await update.message.reply_text("❌ Invalid USER_ID")


# Ban List
async def banlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_main_admin_only(user_id):
        await update.message.reply_text("❌ Only Main Admin Allowed.")
        return

    text = "🚫 Banned Users:\n"
    for u in banned_users:
        text += f"{u}\n"

    text += "\n🚫 Banned Admins:\n"
    for a in banned_admins:
        text += f"{a}\n"

    await update.message.reply_text(text)

# ==========================================
# STAGE 6 - BROADCAST SYSTEM
# ==========================================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_main_admin_only(user_id):
        await update.message.reply_text("❌ Only Main Admin Allowed.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message with /broadcast")
        return

    msg = update.message.reply_to_message

    success = 0
    failed = 0

    # Send to Users
    for uid in users:
        if uid in banned_users:
            continue

        try:
            if msg.text:
                await context.bot.send_message(uid, msg.text)
            elif msg.photo:
                await context.bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption)
            elif msg.document:
                await context.bot.send_document(uid, msg.document.file_id, caption=msg.caption)
            elif msg.video:
                await context.bot.send_video(uid, msg.video.file_id, caption=msg.caption)

            success += 1
        except:
            failed += 1

    # Send to Groups
    for gid in groups:
        try:
            if msg.text:
                await context.bot.send_message(gid, msg.text)
            elif msg.photo:
                await context.bot.send_photo(gid, msg.photo[-1].file_id, caption=msg.caption)
            elif msg.document:
                await context.bot.send_document(gid, msg.document.file_id, caption=msg.caption)
            elif msg.video:
                await context.bot.send_video(gid, msg.video.file_id, caption=msg.caption)

            success += 1
        except:
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast Completed\n\n✅ Success: {success}\n❌ Failed: {failed}"
    )

# ==========================================
# STAGE 7 - FORCE JOIN CONTROL SYSTEM
# ==========================================

async def addforce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_admin_panel(user_id):
        await update.message.reply_text("❌ Admin Only.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage:\n/addforce CHANNEL_ID EMOJI")
        return

    try:
        channel_id = int(context.args[0])
        emoji = context.args[1]

        if len(emoji) > 3:
            await update.message.reply_text("❌ Only single emoji allowed.")
            return

        force_join_channels[user_id] = {
            "channel_id": channel_id,
            "emoji": emoji
        }

        await update.message.reply_text("✅ Force channel added successfully.")

    except:
        await update.message.reply_text("❌ Invalid Channel ID.")


async def removeforce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_admin_panel(user_id):
        await update.message.reply_text("❌ Admin Only.")
        return

    # Main admin can remove anyone's
    if can_use_main_admin_only(user_id):
        if not context.args:
            await update.message.reply_text("Usage: /removeforce ADMIN_ID")
            return

        try:
            target_admin = int(context.args[0])
            if target_admin in force_join_channels:
                del force_join_channels[target_admin]
                await update.message.reply_text("✅ Force channel removed.")
            else:
                await update.message.reply_text("❌ Not Found.")
        except:
            await update.message.reply_text("❌ Invalid ID.")
        return

    # Sub admin remove own
    if user_id in force_join_channels:
        del force_join_channels[user_id]
        await update.message.reply_text("✅ Your force channel removed.")
    else:
        await update.message.reply_text("❌ No force channel found.")


async def forcelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_admin_panel(user_id):
        await update.message.reply_text("❌ Admin Only.")
        return

    if not force_join_channels:
        await update.message.reply_text("No Force Channels Set.")
        return

    text = "📌 Active Force Channels:\n\n"

    for admin_id, data in force_join_channels.items():
        text += f"Admin: {admin_id}\nChannel: {data['channel_id']}\nEmoji: {data['emoji']}\n\n"

    await update.message.reply_text(text)

# ==========================================
# STAGE 8 - CUSTOM COMMAND CREATION SYSTEM (UPDATED)
# ==========================================

def clean_text(text):
    if not text:
        return None
    text = re.sub(r'@\w+', '', text)  # remove usernames
    text = re.sub(r'http\S+', '', text)  # remove links
    return text.strip()


async def set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not can_use_admin_panel(user_id):
        await update.message.reply_text("❌ Admin Only.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /set command_name")
        return

    cmd_name = context.args[0].lower()

    command_creation_mode[user_id] = {
        "name": cmd_name,
        "files": [],
        "owner": user_id
    }

    await update.message.reply_text(
        f"📦 Send files/text for /{cmd_name}\nWhen finished type /done"
    )


async def collect_command_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in command_creation_mode:
        return

    msg = update.message

    file_data = {}

    if msg.text:
        file_data["type"] = "text"
        file_data["content"] = clean_text(msg.text)

    elif msg.photo:
        file_data["type"] = "photo"
        file_data["file_id"] = msg.photo[-1].file_id
        file_data["caption"] = clean_text(msg.caption)

    elif msg.document:
        file_data["type"] = "document"
        file_data["file_id"] = msg.document.file_id
        file_data["caption"] = clean_text(msg.caption)

    elif msg.video:
        file_data["type"] = "video"
        file_data["file_id"] = msg.video.file_id
        file_data["caption"] = clean_text(msg.caption)

    else:
        return

    command_creation_mode[user_id]["files"].append(file_data)
    await update.message.reply_text("✅ Added")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in command_creation_mode:
        await update.message.reply_text("❌ You are not creating any command.")
        return

    data = command_creation_mode[user_id]
    cmd_name = data["name"]

    ist_time = datetime.datetime.now(tz).strftime("%d %B %Y | %I:%M %p IST")

    command_storage[cmd_name] = {
        "files": data["files"],
        "owner": data["owner"],
        "time": ist_time
    }

    del command_creation_mode[user_id]

    await update.message.reply_text(f"✅ Command /{cmd_name} saved successfully!")

    # ==========================================
    # #--- CLEAN BROADCAST FIX
    # ==========================================

    for uid in list(users):
        if uid in banned_users:
            continue

        if uid == user_id:
            continue   # creator ko dobara send nahi karega

        for file in command_storage[cmd_name]["files"]:
            try:
                if file["type"] == "text":
                    await context.bot.send_message(uid, file["content"])

                elif file["type"] == "photo":
                    await context.bot.send_photo(uid, file["file_id"], caption=file["caption"])

                elif file["type"] == "document":
                    await context.bot.send_document(uid, file["file_id"], caption=file["caption"])

                elif file["type"] == "video":
                    await context.bot.send_video(uid, file["file_id"], caption=file["caption"])

            except:
                pass

        await context.bot.send_message(
            uid,
            f"📅 Uploaded On:\n{ist_time}"
        )

# ==========================================
# STAGE 9 - CUSTOM COMMAND EXECUTION (UPDATED)
# ==========================================

async def custom_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return

    cmd_name = update.message.text.strip().replace("/", "").lower()

    if cmd_name not in command_storage:
        return

    data = command_storage[cmd_name]

    for file in data["files"]:
        try:
            if file["type"] == "text":
                await context.bot.send_message(update.effective_chat.id, file["content"])

            elif file["type"] == "photo":
                await context.bot.send_photo(update.effective_chat.id, file["file_id"], caption=file["caption"])

            elif file["type"] == "document":
                await context.bot.send_document(update.effective_chat.id, file["file_id"], caption=file["caption"])

            elif file["type"] == "video":
                await context.bot.send_video(update.effective_chat.id, file["file_id"], caption=file["caption"])

        except:
            pass

    await context.bot.send_message(
        update.effective_chat.id,
        f"📅 Uploaded On:\n{data['time']}"
    )

# ==========================================
# LIST ALL CUSTOM COMMANDS
# ==========================================

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not command_storage:
        await update.message.reply_text("No Commands Available.")
        return

    text = "📜 Available Commands:\n\n"

    for name in command_storage.keys():
        text += f"/{name}\n"

    await update.message.reply_text(text)
    
# ==========================================
# DELETE COMMAND
# ==========================================

async def delcmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_role(user_id)

    if not can_use_admin_panel(user_id):
        await update.message.reply_text("❌ Admin Only.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /delcmd command_name")
        return

    cmd_name = context.args[0].lower()

    if cmd_name not in command_storage:
        await update.message.reply_text("❌ Command Not Found.")
        return

    if role == "admin" and command_storage[cmd_name]["owner"] != user_id:
        await update.message.reply_text("❌ You cannot delete this command.")
        return

    del command_storage[cmd_name]
    await update.message.reply_text("✅ Command deleted successfully.")


# ==========================================
# REMOVE FILE BY NUMBER
# ==========================================

async def removefile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_role(user_id)

    if not can_use_admin_panel(user_id):
        await update.message.reply_text("❌ Admin Only.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /removefile command_name file_number")
        return

    cmd_name = context.args[0].lower()

    if cmd_name not in command_storage:
        await update.message.reply_text("❌ Command Not Found.")
        return

    if role == "admin" and command_storage[cmd_name]["owner"] != user_id:
        await update.message.reply_text("❌ You cannot edit this command.")
        return

    try:
        index = int(context.args[1]) - 1
        files = command_storage[cmd_name]["files"]

        if index < 0 or index >= len(files):
            await update.message.reply_text("❌ Invalid file number.")
            return

        del files[index]
        await update.message.reply_text("✅ File removed successfully.")

    except:
        await update.message.reply_text("❌ Invalid input.")

# ==========================================
# STAGE 10 - SUPPORT SYSTEM
# ==========================================

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_banned(user_id):
        await update.message.reply_text("❌ You are banned.")
        return

    support_mode[user_id] = True
    await update.message.reply_text("✍ Send your issue. Admin will receive it.")


async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in support_mode:
        return

    message_text = update.message.text

    try:
        await context.bot.send_message(
            MAIN_ADMIN_ID,
            f"📩 Support Message\n\nFrom: {user_id}\n\n{message_text}"
        )
        await update.message.reply_text("✅ Your message has been sent to Admin.")
    except:
        await update.message.reply_text("❌ Failed to send message.")

    del support_mode[user_id]

# ==========================================
# FINAL STAGE - HANDLER REGISTRATION
# ==========================================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Start & verify
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_join, pattern="^verify_join$"))

    # Role/Admin system
    app.add_handler(CommandHandler("adminpanel", adminpanel))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("removeadmin", removeadmin))
    app.add_handler(CommandHandler("adminlist", adminlist))
    app.add_handler(CommandHandler("memberpanel", memberpanel))
    # User tracking
    app.add_handler(CommandHandler("userlist", userlist))

    # Ban system
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("banlist", banlist))

    # Broadcast
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Force join
    app.add_handler(CommandHandler("addforce", addforce))
    app.add_handler(CommandHandler("removeforce", removeforce))
    app.add_handler(CommandHandler("forcelist", forcelist))

    # Custom command system
    app.add_handler(CommandHandler("set", set))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("cmd", cmd))
    app.add_handler(CommandHandler("delcmd", delcmd))
    app.add_handler(CommandHandler("removefile", removefile))

    # Support system
    app.add_handler(CommandHandler("support", support))

    # ==========================================
    # #--- FIXED MESSAGE HANDLER ORDER
    # ==========================================

    # 1️⃣ Support system first
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support))

    # 2️⃣ Custom command creation collector
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, collect_command_data))

    # 3️⃣ Custom command execution LAST
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_command_handler))

    print("🚀 BOT STARTED SUCCESSFULLY")
    app.run_polling()


if __name__ == "__main__":
    main()
