import telebot
import json
import os
import re
from datetime import datetime
import pytz

# ================= CONFIG =================

BOT_TOKEN = "8531299371:AAFTWsPousrpXdY1MUJvXU6Ef_7Rz-X8tVU"
MAIN_ADMIN = 1086634832
PERMANENT_FORCE = "@loader0fficial"

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "data.json"

# ================= INIT =================

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({
            "users": {},
            "admins": [MAIN_ADMIN],
            "banned": {},
            "commands": {},
            "set_mode": None,
            "force_groups": [],
            "support_map": {}
        }, f)

def load():
    with open(DATA_FILE) as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()

# ================= IST TIME =================

def get_ist():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%d-%m-%Y %H:%M")

# ================= CLEAN TEXT =================

def clean_text(text):
    if not text:
        return None
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "👤", text)
    return text.strip()

# ================= FORCE JOIN CHECK =================

def check_join(user_id):
    groups = [PERMANENT_FORCE] + data["force_groups"]

    for g in groups:
        try:
            status = bot.get_chat_member(g, user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_msg(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    link = f"https://t.me/{PERMANENT_FORCE.replace('@','')}"
    markup.add(telebot.types.InlineKeyboardButton("🔔 Join Channel", url=link))
    bot.send_message(chat_id, "⚠ Join Required Channel First", reply_markup=markup)

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)

    if uid in data["banned"]:
        return

    data["users"][uid] = message.from_user.username
    save(data)

    if not check_join(message.from_user.id):
        join_msg(message.chat.id)
        return

    bot.send_message(message.chat.id, "✅ Verified\nUse /cmd")

# ================= CMD =================

@bot.message_handler(commands=['cmd'])
def cmd(message):
    uid = str(message.from_user.id)

    if uid in data["banned"]:
        return

    if message.from_user.id in data["admins"]:
        text = """👑 Admin Commands

/set name
/done
/edit name
/deletecmd name
/ban id
/unban id
/banlist
/userlist
/addforce @group
/delforce @group
/support reply
/cmd"""
    else:
        if not check_join(message.from_user.id):
            join_msg(message.chat.id)
            return

        text = "📦 Available Commands:\n\n"
        for c in data["commands"]:
            text += f"/{c}\n"
        text += "\n/support\n/cmd"

    bot.send_message(message.chat.id, text)

# ================= SET =================

@bot.message_handler(commands=['set'])
def set_cmd(message):
    if message.from_user.id not in data["admins"]:
        return

    try:
        name = message.text.split()[1]
        data["set_mode"] = name
        data["commands"][name] = {"files": [], "time": ""}
        save(data)
        bot.send_message(message.chat.id, "Send files then /done")
    except:
        bot.send_message(message.chat.id, "Usage: /set commandname")

# ================= FILE SAVE =================

@bot.message_handler(content_types=['document','photo','video','audio'])
def save_file(message):
    if message.from_user.id not in data["admins"]:
        return

    if not data["set_mode"]:
        return

    cmd = data["set_mode"]

    file_info = {
        "type": message.content_type,
        "file_id": message.document.file_id if message.document else
                   message.photo[-1].file_id if message.photo else
                   message.video.file_id if message.video else
                   message.audio.file_id,
        "caption": clean_text(message.caption)
    }

    data["commands"][cmd]["files"].append(file_info)
    save(data)

# ================= DONE =================

@bot.message_handler(commands=['done'])
def done(message):
    if message.from_user.id not in data["admins"]:
        return

    if not data["set_mode"]:
        return

    cmd = data["set_mode"]
    data["commands"][cmd]["time"] = get_ist()
    save(data)

    for uid in data["users"]:
        try:
            bot.send_message(uid, f"🔔 Key Updated\nUse /{cmd}")
        except:
            pass

    data["set_mode"] = None
    save(data)

    bot.send_message(message.chat.id, "✅ Saved & Broadcasted")

# ================= EDIT =================

@bot.message_handler(commands=['edit'])
def edit_cmd(message):
    if message.from_user.id not in data["admins"]:
        return
    try:
        name = message.text.split()[1]
        if name in data["commands"]:
            data["set_mode"] = name
            data["commands"][name]["files"] = []
            save(data)
            bot.send_message(message.chat.id, "Send new files then /done")
    except:
        bot.send_message(message.chat.id, "Usage: /edit name")

# ================= DELETE CMD =================

@bot.message_handler(commands=['deletecmd'])
def delete_cmd(message):
    if message.from_user.id not in data["admins"]:
        return
    try:
        name = message.text.split()[1]
        if name in data["commands"]:
            del data["commands"][name]
            save(data)
            bot.send_message(message.chat.id, "Command deleted")
    except:
        bot.send_message(message.chat.id, "Usage: /deletecmd name")

# ================= DYNAMIC =================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
def dynamic(message):
    uid = str(message.from_user.id)

    if uid in data["banned"]:
        return

    if not check_join(message.from_user.id):
        join_msg(message.chat.id)
        return

    cmd = message.text[1:]

    if cmd not in data["commands"]:
        return

    files = data["commands"][cmd]["files"]
    upload_time = data["commands"][cmd]["time"]

    for f in files:
        bot.send_document(message.chat.id, f["file_id"], caption=f["caption"])

    bot.send_message(message.chat.id, f"📅 Uploaded: {upload_time}")

# ================= BAN =================

@bot.message_handler(commands=['ban'])
def ban(message):
    if message.from_user.id not in data["admins"]:
        return
    try:
        uid = message.text.split()[1]
        data["banned"][uid] = True
        save(data)
        bot.send_message(message.chat.id, "User banned")
    except:
        bot.send_message(message.chat.id, "Usage: /ban user_id")

# ================= UNBAN =================

@bot.message_handler(commands=['unban'])
def unban(message):
    if message.from_user.id not in data["admins"]:
        return
    try:
        uid = message.text.split()[1]
        if uid in data["banned"]:
            del data["banned"][uid]
            save(data)
            bot.send_message(message.chat.id, "User unbanned")
    except:
        bot.send_message(message.chat.id, "Usage: /unban user_id")

# ================= RUN =================

print("Bot Running...")
bot.infinity_polling()
