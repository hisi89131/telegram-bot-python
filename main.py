import telebot
from telebot import types
import json
import os
import re
from datetime import datetime

TOKEN = "8163746024:AAGjB8B2M_D1z8iWkiC9sY4qG5dsxlZqX5k"
MAIN_ADMIN = 1086634832
FORCE_CHANNEL = "@loader0fficial"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DB_FILE = "database.json"

# ---------------- DATABASE ---------------- #

def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": {},
            "admins": [MAIN_ADMIN],
            "banned": [],
            "commands": {},
            "warnings": {}
        }
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

# ---------------- UTIL ---------------- #

def is_admin(user_id):
    return user_id in db["admins"]

def is_banned(user_id):
    return user_id in db["banned"]

def check_join(user_id):
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def clean_caption(text):
    if not text:
        return None
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'https?://\S+', '', text)
    return text.strip()

def register_user(user):
    if str(user.id) not in db["users"]:
        db["users"][str(user.id)] = {
            "username": user.username,
            "first_name": user.first_name
        }
        save_db(db)

# ---------------- FORCE JOIN ---------------- #

def force_join_required(func):
    def wrapper(message):
        user_id = message.from_user.id

        if is_admin(user_id):
            return func(message)

        if not check_join(user_id):
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}")
            btn2 = types.InlineKeyboardButton("✅ Verify", callback_data="verify")
            markup.add(btn1)
            markup.add(btn2)

            bot.send_message(
                user_id,
                "⚠️ Please join channel first then click Verify.",
                reply_markup=markup
            )
            return
        return func(message)
    return wrapper

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):
    if check_join(call.from_user.id):
        bot.answer_callback_query(call.id, "Verified Successfully")
        bot.send_message(call.from_user.id, "✅ Verified Successfully\nUse /help")
    else:
        bot.answer_callback_query(call.id, "Join channel first!", show_alert=True)

# ---------------- START ---------------- #

@bot.message_handler(commands=["start"])
@force_join_required
def start(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, "✅ Bot is working!")

# ---------------- HELP ---------------- #

@bot.message_handler(commands=["help"])
@force_join_required
def help_cmd(message):
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id,
        "👑 Admin Commands:\n"
        "/set command\n"
        "/done\n"
        "/broadcast text\n"
        "/ban id\n"
        "/unban id\n"
        "/users\n"
        "/banlist\n"
        "/admins\n"
        "/support"
        )
    else:
        bot.send_message(message.chat.id,
        "📌 Available Commands:\n"
        "Use custom command like /loader1\n"
        "/support"
        )

# ---------------- SET COMMAND ---------------- #

active_set = {}

@bot.message_handler(commands=["set"])
def set_command(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /set commandname")
        return

    cmd = parts[1].lower()
    active_set[message.from_user.id] = {"command": cmd, "files": []}
    bot.reply_to(message, "Send Files Now Then /done")

@bot.message_handler(commands=["done"])
def done_command(message):
    if not is_admin(message.from_user.id):
        return

    if message.from_user.id not in active_set:
        return

    data = active_set.pop(message.from_user.id)
    upload_time = datetime.now().strftime("%d-%m-%Y %H:%M")

    db["commands"][data["command"]] = {
        "files": data["files"],
        "time": upload_time
    }

    save_db(db)

    bot.reply_to(message, "🔔 Key Updated\nCommand Saved")

    # Broadcast
    for uid in db["users"]:
        try:
            bot.send_message(uid, f"🔔 Key Updated\nUse /{data['command']}")
        except:
            pass

# ---------------- FILE CAPTURE ---------------- #

@bot.message_handler(content_types=["document", "photo", "video"])
def capture_files(message):
    if message.from_user.id in active_set:
        file_info = {
            "file_id": message.document.file_id if message.document else message.photo[-1].file_id,
            "caption": clean_caption(message.caption)
        }
        active_set[message.from_user.id]["files"].append(file_info)

# ---------------- CUSTOM COMMAND ---------------- #

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
@force_join_required
def custom_handler(message):
    cmd = message.text[1:].lower()

    if cmd in db["commands"]:
        data = db["commands"][cmd]
        for f in data["files"]:
            bot.send_document(
                message.chat.id,
                f["file_id"],
                caption=f"{f['caption']}\n\n📅 Uploaded: {data['time']}" if f["caption"] else f"📅 Uploaded: {data['time']}"
            )

# ---------------- BROADCAST ---------------- #

@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/broadcast ", "")
    for uid in db["users"]:
        try:
            bot.send_message(uid, text)
        except:
            pass

# ---------------- USERS ---------------- #

@bot.message_handler(commands=["users"])
def users_cmd(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, f"👥 Total Users: {len(db['users'])}")

# ---------------- BAN ---------------- #

@bot.message_handler(commands=["ban"])
def ban_user(message):
    if not is_admin(message.from_user.id):
        return
    uid = int(message.text.split()[1])
    db["banned"].append(uid)
    save_db(db)
    bot.send_message(message.chat.id, "User Banned")

@bot.message_handler(commands=["unban"])
def unban_user(message):
    if not is_admin(message.from_user.id):
        return
    uid = int(message.text.split()[1])
    if uid in db["banned"]:
        db["banned"].remove(uid)
        save_db(db)
    bot.send_message(message.chat.id, "User Unbanned")

@bot.message_handler(commands=["banlist"])
def banlist(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, f"Banned Users: {db['banned']}")

# ---------------- RUN ---------------- #

print("Bot Running...")
bot.infinity_polling()
