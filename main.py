import telebot
import json
import os
import re
from datetime import datetime
import pytz

# ================== CONFIG ==================

BOT_TOKEN = "8163746024:AAE64JcAgTS25ZUBM5u9kOfF-Q7X4dh_Zxc"
MAIN_ADMIN = 1086634832
FORCE_CHANNEL = "@loader0fficial"

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "data.json"

# ================== INIT DATA ==================

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({
            "users": {},
            "banned": {},
            "admins": [MAIN_ADMIN],
            "commands": {},
            "set_mode": None
        }, f)

def load():
    with open(DATA_FILE) as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()

# ================== TIME (IST) ==================

def get_ist_time():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%d-%m-%Y %H:%M")

# ================== FORCE JOIN ==================

def is_joined(user_id):
    try:
        status = bot.get_chat_member(FORCE_CHANNEL, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# ================== CLEAN TEXT ==================

def clean_text(text):
    if not text:
        return None
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    return text.strip()

# ================== START ==================

@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.from_user.id)

    if uid in data["banned"]:
        return

    if uid not in data["users"]:
        data["users"][uid] = message.from_user.username
        save(data)

    if not is_joined(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Join Channel First Then /start")
        return

    bot.send_message(message.chat.id, "✅ Verified Successfully\nUse /cmd")

# ================== CMD ==================

@bot.message_handler(commands=["cmd"])
def cmd(message):
    uid = str(message.from_user.id)

    if uid in data["banned"]:
        return

    if message.from_user.id in data["admins"]:
        text = """👑 Admin Commands:

/set command
/done
/ban user_id
/unban user_id
/banlist
/userlist
/cmd"""
        bot.send_message(message.chat.id, text)
    else:
        if not is_joined(message.from_user.id):
            bot.send_message(message.chat.id, "⚠️ Join Channel First")
            return

        text = "📦 Available Commands:\n\n"
        for c in data["commands"]:
            text += f"/{c}\n"

        text += "\n/cmd"
        bot.send_message(message.chat.id, text)

# ================== SET ==================

@bot.message_handler(commands=["set"])
def set_cmd(message):
    if message.from_user.id not in data["admins"]:
        return

    try:
        cmd = message.text.split()[1].replace("/", "")
        data["set_mode"] = cmd
        data["commands"][cmd] = []
        save(data)
        bot.send_message(message.chat.id, "Send files now then /done")
    except:
        bot.send_message(message.chat.id, "Usage: /set commandname")

# ================== SAVE FILES ==================

@bot.message_handler(content_types=["document", "photo", "video", "audio"])
def handle_files(message):
    if message.from_user.id not in data["admins"]:
        return

    if not data["set_mode"]:
        return

    caption = clean_text(message.caption)

    file_data = {
        "type": message.content_type,
        "file_id": message.document.file_id if message.document else message.photo[-1].file_id if message.photo else message.video.file_id if message.video else message.audio.file_id,
        "caption": caption
    }

    data["commands"][data["set_mode"]].append(file_data)
    save(data)

# ================== DONE ==================

@bot.message_handler(commands=["done"])
def done(message):
    if message.from_user.id not in data["admins"]:
        return

    if not data["set_mode"]:
        return

    upload_time = get_ist_time()

    for file in data["commands"][data["set_mode"]]:
        file["time"] = upload_time

    save(data)

    # Broadcast
    for uid in data["users"]:
        try:
            bot.send_message(uid, "🔔 Key Updated")
        except:
            pass

    data["set_mode"] = None
    save(data)

    bot.send_message(message.chat.id, "✅ Command Saved & Broadcasted")

# ================== DYNAMIC COMMAND ==================

@bot.message_handler(func=lambda m: m.text and m.text[1:] in data["commands"])
def send_command(message):
    uid = str(message.from_user.id)

    if uid in data["banned"]:
        return

    if not is_joined(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Join Channel First")
        return

    cmd = message.text[1:]

    for file in data["commands"][cmd]:
        if file["type"] == "document":
            bot.send_document(message.chat.id, file["file_id"], caption=file["caption"])
        elif file["type"] == "photo":
            bot.send_photo(message.chat.id, file["file_id"], caption=file["caption"])
        elif file["type"] == "video":
            bot.send_video(message.chat.id, file["file_id"], caption=file["caption"])
        elif file["type"] == "audio":
            bot.send_audio(message.chat.id, file["file_id"], caption=file["caption"])

        bot.send_message(message.chat.id, f"📅 Uploaded: {file['time']} (IST)")

# ================== BAN ==================

@bot.message_handler(commands=["ban"])
def ban(message):
    if message.from_user.id not in data["admins"]:
        return

    try:
        uid = message.text.split()[1]
        data["banned"][uid] = True
        save(data)
        bot.send_message(message.chat.id, "User Banned")
    except:
        bot.send_message(message.chat.id, "Usage: /ban user_id")

# ================== UNBAN ==================

@bot.message_handler(commands=["unban"])
def unban(message):
    if message.from_user.id not in data["admins"]:
        return

    try:
        uid = message.text.split()[1]
        if uid in data["banned"]:
            del data["banned"][uid]
            save(data)
            bot.send_message(message.chat.id, "User Unbanned")
    except:
        bot.send_message(message.chat.id, "Usage: /unban user_id")

# ================== BANLIST ==================

@bot.message_handler(commands=["banlist"])
def banlist(message):
    if message.from_user.id not in data["admins"]:
        return

    text = "🚫 Banned Users:\n\n"
    for uid in data["banned"]:
        text += f"{uid}\n"

    bot.send_message(message.chat.id, text)

# ================== USERLIST ==================

@bot.message_handler(commands=["userlist"])
def userlist(message):
    if message.from_user.id not in data["admins"]:
        return

    text = f"📊 Total Users: {len(data['users'])}\n\n"

    for uid, username in data["users"].items():
        if username:
            text += f"@{username} (ID: {uid})\n"
        else:
            text += f"{uid}\n"

    bot.send_message(message.chat.id, text[:4000])

# ================== RUN ==================

print("Bot Running...")
bot.infinity_polling()
