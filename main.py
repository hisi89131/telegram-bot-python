import telebot
from telebot import types
import json
import os
import re
from datetime import datetime
import pytz

# ================= CONFIG =================

BOT_TOKEN = "8531299371:AAF_rlckrSG1YOtA3DWK5_95ANQwcInnjH8"
MAIN_ADMIN = 1086634832
MAIN_FORCE_GROUP = "@loader0fficial"  # Permanent Force Join

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "data.json"

# ================= INIT =================

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({
            "users": {},
            "banned": {},
            "admins": [MAIN_ADMIN],
            "commands": {},
            "set_mode": None,
            "force_groups": [],
            "warnings": {},
            "support_map": {}
        }, f)

def load():
    with open(DATA_FILE) as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()

# Ensure main force group always present
if MAIN_FORCE_GROUP not in data["force_groups"]:
    data["force_groups"].append(MAIN_FORCE_GROUP)
    save(data)

# ================= TIME =================

def ist_time():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%d-%m-%Y %H:%M")

# ================= FORCE JOIN =================

def check_join(user_id):
    for group in data["force_groups"]:
        try:
            status = bot.get_chat_member(group, user_id).status
            if status not in ["member","administrator","creator"]:
                return False
        except:
            return False
    return True

def force_buttons():
    markup = types.InlineKeyboardMarkup()
    for g in data["force_groups"]:
        if g.startswith("@"):
            link = f"https://t.me/{g.replace('@','')}"
            markup.add(types.InlineKeyboardButton("Join Group", url=link))
    markup.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
    return markup

# ================= CLEAN TEXT =================

def clean(text):
    if not text:
        return None
    text = re.sub(r"http\S+","",text)
    text = re.sub(r"@\w+","",text)
    return text.strip()

# ================= START =================

@bot.message_handler(commands=["start"])
def start(message):
    uid=str(message.from_user.id)

    if uid in data["banned"]:
        return

    data["users"][uid]=message.from_user.username
    save(data)

    if not check_join(message.from_user.id):
        bot.send_message(message.chat.id,"⚠ Join required groups",reply_markup=force_buttons())
        return

    bot.send_message(message.chat.id,"✅ Verified\nUse /cmd")

# ================= VERIFY CALLBACK =================

@bot.callback_query_handler(func=lambda call: call.data=="verify")
def verify(call):
    if check_join(call.from_user.id):
        bot.edit_message_text("✅ Verified Successfully\nUse /cmd",
                              call.message.chat.id,
                              call.message.message_id)
    else:
        bot.answer_callback_query(call.id,"Join all groups first")

# ================= CMD =================

@bot.message_handler(commands=["cmd"])
def cmd(message):
    uid=str(message.from_user.id)

    if uid in data["banned"]:
        return

    if message.from_user.id in data["admins"]:
        text="""👑 Admin Commands

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
            bot.send_message(message.chat.id,"Join groups first",reply_markup=force_buttons())
            return
        text="📦 Available Commands:\n\n"
        for c in data["commands"]:
            text+=f"/{c}\n"
        text+="\n/support message\n/cmd"

    bot.send_message(message.chat.id,text)

# ================= SET =================

@bot.message_handler(commands=["set"])
def setcmd(message):
    if message.from_user.id not in data["admins"]:
        return
    try:
        name=message.text.split()[1]
        data["set_mode"]=name
        data["commands"][name]={"files":[],"time":""}
        save(data)
        bot.send_message(message.chat.id,"Send files then /done")
    except:
        bot.send_message(message.chat.id,"Usage: /set name")

# ================= SAVE FILE =================

@bot.message_handler(content_types=["document","photo","video","audio"])
def savefile(message):
    if message.from_user.id not in data["admins"]:
        return
    if not data["set_mode"]:
        return

    file_id=None
    if message.document:
        file_id=message.document.file_id
    elif message.photo:
        file_id=message.photo[-1].file_id
    elif message.video:
        file_id=message.video.file_id
    elif message.audio:
        file_id=message.audio.file_id

    data["commands"][data["set_mode"]]["files"].append({
        "type":message.content_type,
        "file_id":file_id,
        "caption":clean(message.caption)
    })
    save(data)

# ================= DONE =================

@bot.message_handler(commands=["done"])
def done(message):
    if message.from_user.id not in data["admins"]:
        return
    if not data["set_mode"]:
        return

    cmd=data["set_mode"]
    data["commands"][cmd]["time"]=ist_time()
    data["set_mode"]=None
    save(data)

    for uid in data["users"]:
        try:
            bot.send_message(uid,f"🔔 Updated\nUse /{cmd}")
        except:
            pass

    bot.send_message(message.chat.id,"Saved & Broadcasted")

# ================= DYNAMIC COMMAND =================

@bot.message_handler(func=lambda m:m.text and m.text[1:] in data["commands"])
def dynamic(message):
    uid=str(message.from_user.id)

    if uid in data["banned"]:
        return

    if not check_join(message.from_user.id):
        bot.send_message(message.chat.id,"Join groups first",reply_markup=force_buttons())
        return

    cmd=message.text[1:]
    files=data["commands"][cmd]["files"]
    time=data["commands"][cmd]["time"]

    for f in files:
        if f["type"]=="document":
            bot.send_document(message.chat.id,f["file_id"],caption=f["caption"])
        elif f["type"]=="photo":
            bot.send_photo(message.chat.id,f["file_id"],caption=f["caption"])
        elif f["type"]=="video":
            bot.send_video(message.chat.id,f["file_id"],caption=f["caption"])
        elif f["type"]=="audio":
            bot.send_audio(message.chat.id,f["file_id"],caption=f["caption"])

    bot.send_message(message.chat.id,f"📅 Uploaded: {time}")

# ================= SUPPORT =================

@bot.message_handler(commands=["support"])
def support(message):
    uid=str(message.from_user.id)

    if uid in data["banned"]:
        return

    text=message.text.replace("/support","").strip()
    if not text:
        bot.send_message(message.chat.id,"Usage: /support message")
        return

    if any(bad in text.lower() for bad in ["gali","spam","fuck"]):
        count=data["warnings"].get(uid,0)+1
        data["warnings"][uid]=count
        save(data)
        if count>=3:
            data["banned"][uid]=True
            save(data)
            bot.send_message(message.chat.id,"You are banned")
            return
        bot.send_message(message.chat.id,f"Warning {count}/3")
        return

    for admin in data["admins"]:
        msg=bot.send_message(admin,f"Support from {uid}\n{text}")
        data["support_map"][str(msg.message_id)]=uid
    save(data)
    bot.send_message(message.chat.id,"Message sent to admin")

# ================= ADMIN REPLY =================

@bot.message_handler(func=lambda m:m.reply_to_message and str(m.reply_to_message.message_id) in data["support_map"])
def reply_support(message):
    if message.from_user.id not in data["admins"]:
        return
    user=data["support_map"][str(message.reply_to_message.message_id)]
    bot.send_message(user,f"Admin Reply:\n{message.text}")

# ================= BAN SYSTEM =================

@bot.message_handler(commands=["ban"])
def ban(message):
    if message.from_user.id not in data["admins"]:
        return
    try:
        uid=message.text.split()[1]
        data["banned"][uid]=True
        save(data)
        bot.send_message(message.chat.id,"User banned")
    except:
        pass

@bot.message_handler(commands=["unban"])
def unban(message):
    if message.from_user.id not in data["admins"]:
        return
    try:
        uid=message.text.split()[1]
        if uid in data["banned"]:
            del data["banned"][uid]
            save(data)
            bot.send_message(message.chat.id,"User unbanned")
    except:
        pass

# ================= USERLIST =================

@bot.message_handler(commands=["userlist"])
def userlist(message):
    if message.from_user.id not in data["admins"]:
        return
    text=f"Total Users: {len(data['users'])}\n\n"
    for u,name in data["users"].items():
        if name:
            text+=f"@{name} (ID:{u})\n"
        else:
            text+=f"{u}\n"
    bot.send_message(message.chat.id,text[:4000])

# ================= RUN =================

print("Bot Running...")
bot.infinity_polling(timeout=60,long_polling_timeout=60)
