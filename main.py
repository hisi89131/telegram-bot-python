import telebot
import json
import os
import re
import pytz
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8163746024:AAGuqYln0nMGtFqD8IS1OZGfD5t_RsmgXGk"
MAIN_ADMIN = 1086634832
FORCE_CHANNEL = "@loader0fficial"
GROUP_ID = "@loader0fficial"

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# -------------------- LOAD DATA --------------------
def load():
    if not os.path.exists(DATA_FILE):
        return {
            "users": {},
            "admins": [MAIN_ADMIN],
            "banned": {},
            "commands": {},
            "set_mode": {},
            "support_map": {},
            "warnings": {}
        }
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()

# -------------------- FORCE JOIN CHECK --------------------
def is_joined(user_id):
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member","administrator","creator"]
    except:
        return False

def join_buttons():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"),
        InlineKeyboardButton("✅ Verify", callback_data="verify")
    )
    return markup

@bot.callback_query_handler(func=lambda call: call.data=="verify")
def verify(call):
    if is_joined(call.from_user.id):
        bot.edit_message_text("✅ Verified Successfully\nUse /help", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Join channel first!", show_alert=True)

# -------------------- START --------------------
@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.from_user.id)

    if uid in data["banned"]:
        return

    data["users"][uid] = message.from_user.username
    save(data)

    if not is_joined(message.from_user.id):
        bot.send_message(message.chat.id,"⚠ Join Channel First", reply_markup=join_buttons())
        return

    bot.send_message(message.chat.id,"✅ Verified Successfully\nUse /help")

# -------------------- HELP --------------------
@bot.message_handler(commands=["help"])
def help_cmd(message):
    if message.from_user.id in data["admins"]:
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
        "/support reply")
    else:
        bot.send_message(message.chat.id,"📌 Use custom command like /loader1")

# -------------------- SET COMMAND --------------------
@bot.message_handler(commands=["set"])
def set_command(message):
    if message.from_user.id not in data["admins"]:
        return
    try:
        cmd = message.text.split()[1]
        data["set_mode"][str(message.from_user.id)] = cmd
        data["commands"][cmd] = []
        save(data)
        bot.send_message(message.chat.id,"Send files now then /done")
    except:
        bot.send_message(message.chat.id,"Usage: /set commandname")

# -------------------- CAPTURE FILES --------------------
@bot.message_handler(content_types=["document","photo","video","text"])
def capture(message):
    uid = str(message.from_user.id)

    # Spam filter
    bad_words = ["madarchod","gali","spam"]
    if any(word in message.text.lower() for word in bad_words if message.text):
        warn = data["warnings"].get(uid,0)+1
        data["warnings"][uid]=warn
        save(data)
        bot.delete_message(message.chat.id,message.message_id)
        if warn>=2:
            data["banned"][uid]=True
            save(data)
            bot.send_message(MAIN_ADMIN,f"User {uid} auto banned")
        return

    if uid in data["set_mode"]:
        cmd = data["set_mode"][uid]

        caption = message.caption or message.text or ""
        caption = re.sub(r'@\w+','',caption)
        caption = re.sub(r'http\S+','',caption)

        ist = pytz.timezone("Asia/Kolkata")
        now = datetime.now(ist).strftime("%d-%m-%Y %H:%M")

        data["commands"][cmd].append({
            "file_id": message.document.file_id if message.document else None,
            "caption": caption,
            "time": now
        })
        save(data)

# -------------------- DONE --------------------
@bot.message_handler(commands=["done"])
def done(message):
    uid = str(message.from_user.id)
    if uid not in data["set_mode"]:
        return
    cmd = data["set_mode"][uid]
    del data["set_mode"][uid]
    save(data)

    # Broadcast
    for user in data["users"]:
        try:
            bot.send_message(user,f"🔔 Key Updated\nUse /{cmd}")
        except:
            pass

    bot.send_message(GROUP_ID,f"🔔 Key Updated\n@{bot.get_me().username}")
    bot.send_message(message.chat.id,"Command Saved & Broadcasted")

# -------------------- CUSTOM COMMAND HANDLER --------------------
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
def custom(m):
    cmd = m.text.replace("/","")
    uid = str(m.from_user.id)

    if uid in data["banned"]:
        return

    if not is_joined(m.from_user.id):
        bot.send_message(m.chat.id,"⚠ Join Channel First", reply_markup=join_buttons())
        return

    if cmd in data["commands"]:
        for item in data["commands"][cmd]:
            bot.send_document(m.chat.id,item["file_id"],caption=item["caption"])
            bot.send_message(m.chat.id,f"📅 Uploaded: {item['time']}")

# -------------------- USERS --------------------
@bot.message_handler(commands=["users"])
def users(message):
    if message.from_user.id not in data["admins"]:
        return
    txt="Total Users:\n"
    for u in data["users"]:
        txt+=f"{u} @{data['users'][u]}\n"
    bot.send_message(message.chat.id,txt)

# -------------------- BAN --------------------
@bot.message_handler(commands=["ban"])
def ban(message):
    if message.from_user.id not in data["admins"]:
        return
    uid=message.text.split()[1]
    data["banned"][uid]=True
    save(data)
    bot.send_message(message.chat.id,"Banned")

@bot.message_handler(commands=["unban"])
def unban(message):
    if message.from_user.id not in data["admins"]:
        return
    uid=message.text.split()[1]
    if uid in data["banned"]:
        del data["banned"][uid]
        save(data)
        bot.send_message(message.chat.id,"Unbanned")

@bot.message_handler(commands=["banlist"])
def banlist(message):
    if message.from_user.id not in data["admins"]:
        return
    bot.send_message(message.chat.id,str(data["banned"]))

# -------------------- SUPPORT --------------------
@bot.message_handler(commands=["support"])
def support(message):
    uid=str(message.from_user.id)
    text=message.text.replace("/support","").strip()
    if not text:
        bot.send_message(message.chat.id,"Usage: /support your message")
        return

    for admin in data["admins"]:
        sent=bot.send_message(admin,f"Support from {uid}\n{text}")
        data["support_map"][str(sent.message_id)]=uid
    save(data)
    bot.send_message(message.chat.id,"Message sent to admin")

@bot.message_handler(func=lambda m: m.reply_to_message and str(m.reply_to_message.message_id) in data["support_map"])
def reply_support(message):
    if message.from_user.id not in data["admins"]:
        return
    original=str(message.reply_to_message.message_id)
    user=data["support_map"][original]
    bot.send_message(user,f"Admin Reply:\n{message.text}")

# -------------------- RUN --------------------
print("Bot Running...")
bot.infinity_polling()
