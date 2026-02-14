import telebot
import os
import json
import re
import time
from datetime import datetime

TOKEN = "8163746024:AAGQ9ARweqJl1sftXszz2WtG5F14l3kccJA"

MAIN_ADMIN = 1086634832
FORCE_GROUP = "@loader0fficial"

bot = telebot.TeleBot(TOKEN)

# Files
USERS = "users.json"
ADMINS = "admins.json"
BANNED = "banned.json"
COMMANDS = "commands.json"
WARNINGS = "warnings.json"

# ------------------ Utility ------------------

def load(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def clean_text(text):
    if not text:
        return None
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    return text.strip()

# ------------------ Start ------------------

@bot.message_handler(commands=['start'])
def start(msg):
    banned = load(BANNED)
    if str(msg.from_user.id) in banned:
        return

    users = load(USERS)
    users[str(msg.from_user.id)] = msg.from_user.username
    save(USERS, users)

    bot.reply_to(msg, "Bot is working ✅")

# ------------------ Help ------------------

@bot.message_handler(commands=['help'])
def help_user(msg):
    text = """
User Commands:

/support <message>
Use any created command name
"""
    bot.reply_to(msg, text)

@bot.message_handler(commands=['adminhelp'])
def help_admin(msg):
    if msg.from_user.id != MAIN_ADMIN and str(msg.from_user.id) not in load(ADMINS):
        return
    text = """
Admin Commands:

/setcmd name
/done
/delcmd name
/addadmin id
/removeadmin id
/adminlist
/ban id
/unban id
/banlist
/broadcast message
/users
"""
    bot.reply_to(msg, text)

# ------------------ Admin System ------------------

@bot.message_handler(commands=['addadmin'])
def addadmin(msg):
    if msg.from_user.id != MAIN_ADMIN:
        return
    admin_id = msg.text.split()[1]
    admins = load(ADMINS)
    admins[admin_id] = "ADMIN"
    save(ADMINS, admins)
    bot.reply_to(msg, "Admin Added ✅")

@bot.message_handler(commands=['removeadmin'])
def removeadmin(msg):
    if msg.from_user.id != MAIN_ADMIN:
        return
    admin_id = msg.text.split()[1]
    admins = load(ADMINS)
    if admin_id in admins:
        del admins[admin_id]
        save(ADMINS, admins)
        bot.reply_to(msg, "Admin Removed ✅")

@bot.message_handler(commands=['adminlist'])
def adminlist(msg):
    if msg.from_user.id != MAIN_ADMIN:
        return
    admins = load(ADMINS)
    text = "Admins:\n"
    for i in admins:
        text += f"{i} - ADMIN\n"
    bot.reply_to(msg, text)

# ------------------ Ban System ------------------

@bot.message_handler(commands=['ban'])
def ban(msg):
    if msg.from_user.id != MAIN_ADMIN:
        return
    user_id = msg.text.split()[1]
    banned = load(BANNED)
    banned[user_id] = "BANNED"
    save(BANNED, banned)
    bot.reply_to(msg, "User Banned 🚫")

@bot.message_handler(commands=['unban'])
def unban(msg):
    if msg.from_user.id != MAIN_ADMIN:
        return
    user_id = msg.text.split()[1]
    banned = load(BANNED)
    if user_id in banned:
        del banned[user_id]
        save(BANNED, banned)
        bot.reply_to(msg, "User Unbanned ✅")

@bot.message_handler(commands=['banlist'])
def banlist(msg):
    if msg.from_user.id != MAIN_ADMIN:
        return
    banned = load(BANNED)
    bot.reply_to(msg, str(banned))

# ------------------ Command Create ------------------

active_cmd = {}

@bot.message_handler(commands=['setcmd'])
def setcmd(msg):
    if msg.from_user.id != MAIN_ADMIN:
        return
    name = msg.text.split()[1]
    active_cmd[msg.from_user.id] = name
    bot.reply_to(msg, f"Send files for {name}")

@bot.message_handler(content_types=['document','video','photo','audio'])
def save_files(msg):
    if msg.from_user.id not in active_cmd:
        return

    commands = load(COMMANDS)
    name = active_cmd[msg.from_user.id]

    if name not in commands:
        commands[name] = {"files": [], "time": ""}

    commands[name]["files"].append(msg.message_id)
    save(COMMANDS, commands)

@bot.message_handler(commands=['done'])
def done(msg):
    if msg.from_user.id not in active_cmd:
        return
    name = active_cmd[msg.from_user.id]
    commands = load(COMMANDS)
    commands[name]["time"] = datetime.now().strftime("%d-%m-%Y %H:%M")
    save(COMMANDS, commands)
    del active_cmd[msg.from_user.id]
    bot.reply_to(msg, "Command Saved ✅")

# ------------------ Delete Command ------------------

@bot.message_handler(commands=['delcmd'])
def delcmd(msg):
    if msg.from_user.id != MAIN_ADMIN:
        return
    name = msg.text.split()[1]
    commands = load(COMMANDS)
    if name in commands:
        del commands[name]
        save(COMMANDS, commands)
        bot.reply_to(msg, "Deleted ✅")

# ------------------ Use Command ------------------

@bot.message_handler(func=lambda msg: True)
def handle_all(msg):
    banned = load(BANNED)
    if str(msg.from_user.id) in banned:
        return

    commands = load(COMMANDS)
    text = msg.text

    if text in commands:
        data = commands[text]
        bot.send_message(msg.chat.id, f"Uploaded: {data['time']}")
        for mid in data["files"]:
            bot.copy_message(msg.chat.id, MAIN_ADMIN, mid)

# ------------------ Support ------------------

@bot.message_handler(commands=['support'])
def support(msg):
    message = msg.text.replace("/support ","")
    bot.send_message(MAIN_ADMIN, f"Support from {msg.from_user.id}:\n{message}")

print("Bot Running...")
bot.infinity_polling()        bot.reply_to(message, f"{name} saved successfully ✅")


# ---------------- DELETE LOADER ----------------
@bot.message_handler(commands=["delete"])
def delete_loader(message):
    if not is_admin(message.from_user.id):
        return
    try:
        name = message.text.split()[1].lower()
        if name in commands_data:
            del commands_data[name]
            bot.reply_to(message, "Deleted successfully.")
        else:
            bot.reply_to(message, "Loader not found.")
    except:
        bot.reply_to(message, "Usage: /delete loadername")


# ---------------- EDIT LOADER ----------------
@bot.message_handler(commands=["edit"])
def edit_loader(message):
    if not is_admin(message.from_user.id):
        return
    try:
        name = message.text.split()[1].lower()
        if name in commands_data:
            user_upload_mode[message.from_user.id] = name
            commands_data[name] = []
            bot.reply_to(message, f"Editing {name}. Send new files then /done")
        else:
            bot.reply_to(message, "Loader not found.")
    except:
        bot.reply_to(message, "Usage: /edit loadername")


# ---------------- ADD ADMIN ----------------
@bot.message_handler(commands=["addadmin"])
def add_admin(message):
    if not is_admin(message.from_user.id):
        return
    try:
        new_admin = int(message.text.split()[1])
        admins.add(new_admin)
        bot.reply_to(message, "Admin added.")
    except:
        bot.reply_to(message, "Usage: /addadmin userid")


# ---------------- REMOVE ADMIN ----------------
@bot.message_handler(commands=["removeadmin"])
def remove_admin(message):
    if not is_admin(message.from_user.id):
        return
    try:
        remove_id = int(message.text.split()[1])
        admins.discard(remove_id)
        bot.reply_to(message, "Admin removed.")
    except:
        bot.reply_to(message, "Usage: /removeadmin userid")


# ---------------- HANDLE FILES ----------------
@bot.message_handler(content_types=["document", "video", "photo", "audio", "voice", "animation"])
def handle_files(message):
    if message.from_user.id in user_upload_mode:
        name = user_upload_mode[message.from_user.id]
        upload_time = datetime.now().strftime("%d %b %Y | %I:%M %p")
        commands_data[name].append({
            "message_id": message.message_id,
            "chat_id": message.chat.id,
            "time": upload_time
        })


# ---------------- USER COMMAND FETCH ----------------
@bot.message_handler(func=lambda message: True)
def user_commands(message):
    if not is_joined(message.from_user.id):
        return force_join_message(message)

    cmd = message.text.lower().strip()
    if cmd in commands_data:
        files = commands_data[cmd]
        for file in files:
            bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=file["chat_id"],
                message_id=file["message_id"]
            )
            bot.send_message(message.chat.id, f"🕒 Uploaded: {file['time']}")


print("Bot running...")
bot.infinity_polling()
    text = message.text.replace("/", "")

    if text in stored_files:

        file_msg = stored_files[text]

        caption = clean_caption(file_msg.caption)

        bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=file_msg.chat.id,
            message_id=file_msg.message_id,
            caption=caption
        )

print("Bot running...")

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
