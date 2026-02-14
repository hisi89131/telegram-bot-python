import telebot
import json
import os
import re
from datetime import datetime

# ============ CONFIG ============
TOKEN = "8163746024:AAGFfQbHgPtrdFmbG9KJN9BHJRhtnWVMj8E"
OWNER_ID = 1086634832
FORCE_JOIN = "@loader0fficial"
DATA_FILE = "data.json"
# =================================

bot = telebot.TeleBot(TOKEN)

# ---------- DATA ----------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({
            "admins": [OWNER_ID],
            "banned": [],
            "users": [],
            "commands": {}
        }, f)

def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------- CHECKS ----------
def is_admin(user_id):
    data = load_data()
    return user_id in data["admins"]

def is_banned(user_id):
    data = load_data()
    return user_id in data["banned"]

def force_join_check(user_id):
    try:
        member = bot.get_chat_member(FORCE_JOIN, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    data = load_data()

    if is_banned(user_id):
        return

    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

    if not force_join_check(user_id):
        bot.reply_to(message,
            f"⚠️ Please join our group first:\n{FORCE_JOIN}")
        return

    bot.reply_to(message, "✅ Bot is working!")

# ---------- HELP ----------
@bot.message_handler(commands=["help"])
def help_cmd(message):
    user_id = message.from_user.id

    if is_admin(user_id):
        bot.reply_to(message,
            "👑 Admin Commands:\n"
            "/broadcast - Send message to all\n"
            "/ban <id>\n"
            "/unban <id>\n"
            "/admins\n"
            "/users\n"
            "/help")
    else:
        bot.reply_to(message,
            "👤 User Commands:\n"
            "/start\n"
            "/help")

# ---------- BROADCAST ----------
@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if not is_admin(message.from_user.id):
        return

    msg = message.text.replace("/broadcast ", "")
    data = load_data()

    for user in data["users"]:
        try:
            bot.send_message(user, msg)
        except:
            pass

    bot.reply_to(message, "✅ Broadcast Sent")

# ---------- BAN ----------
@bot.message_handler(commands=["ban"])
def ban_user(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int(message.text.split()[1])
        data = load_data()
        if user_id not in data["banned"]:
            data["banned"].append(user_id)
            save_data(data)
        bot.reply_to(message, "🚫 User Banned")
    except:
        bot.reply_to(message, "Usage: /ban user_id")

# ---------- UNBAN ----------
@bot.message_handler(commands=["unban"])
def unban_user(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int(message.text.split()[1])
        data = load_data()
        if user_id in data["banned"]:
            data["banned"].remove(user_id)
            save_data(data)
        bot.reply_to(message, "✅ User Unbanned")
    except:
        bot.reply_to(message, "Usage: /unban user_id")

# ---------- LIST ADMINS ----------
@bot.message_handler(commands=["admins"])
def list_admins(message):
    if not is_admin(message.from_user.id):
        return

    data = load_data()
    text = "👑 Admin List:\n"
    for admin in data["admins"]:
        text += f"{admin} (admin)\n"
    bot.reply_to(message, text)

# ---------- LIST USERS ----------
@bot.message_handler(commands=["users"])
def list_users(message):
    if not is_admin(message.from_user.id):
        return

    data = load_data()
    bot.reply_to(message, f"👥 Total Users: {len(data['users'])}")

# ---------- CLEAN TEXT ----------
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    return text.strip()

# ---------- FILE HANDLER ----------
@bot.message_handler(content_types=["document", "video", "photo", "audio", "voice"])
def handle_files(message):
    if is_banned(message.from_user.id):
        return

    caption = clean_text(message.caption)
    bot.copy_message(
        chat_id=message.chat.id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        caption=caption
    )

# ---------- RUN ----------
print("Bot is running...")
bot.infinity_polling()    if msg.from_user.id != MAIN_ADMIN:
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
