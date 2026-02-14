import telebot
import json
import os
import re

TOKEN = "8163746024:AAEQUev_pEQqxdsTSMA2BlDTbUcDskdK2vE"
OWNER_ID = 1086634832
FORCE_JOIN = "@loader0fficial"
DATA_FILE = "data.json"

bot = telebot.TeleBot(TOKEN)

# ---------- DATA CREATE ----------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({
            "admins": [OWNER_ID],
            "users": [],
            "banned": []
        }, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------- CHECK FUNCTIONS ----------
def is_admin(user_id):
    data = load_data()
    return user_id in data["admins"]

def is_banned(user_id):
    data = load_data()
    return user_id in data["banned"]

def check_force_join(user_id):
    try:
        member = bot.get_chat_member(FORCE_JOIN, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start_cmd(message):
    user_id = message.from_user.id
    data = load_data()

    if is_banned(user_id):
        return

    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

    if not check_force_join(user_id):
        bot.reply_to(message, f"⚠️ Join First:\n{FORCE_JOIN}")
        return

    bot.reply_to(message, "✅ Bot is working!")

# ---------- HELP ----------
@bot.message_handler(commands=["help"])
def help_cmd(message):
    if is_admin(message.from_user.id):
        bot.reply_to(message,
            "👑 Admin Commands:\n"
            "/broadcast <text>\n"
            "/ban <id>\n"
            "/unban <id>\n"
            "/users\n"
            "/admins\n"
            "/help"
        )
    else:
        bot.reply_to(message,
            "👤 User Commands:\n"
            "/start\n"
            "/help"
        )

# ---------- BROADCAST ----------
@bot.message_handler(commands=["broadcast"])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id):
        return

    text = message.text.replace("/broadcast ", "")
    data = load_data()

    for user in data["users"]:
        try:
            bot.send_message(user, text)
        except:
            pass

    bot.reply_to(message, "✅ Broadcast Sent")

# ---------- BAN ----------
@bot.message_handler(commands=["ban"])
def ban_cmd(message):
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
def unban_cmd(message):
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

# ---------- USERS ----------
@bot.message_handler(commands=["users"])
def users_cmd(message):
    if not is_admin(message.from_user.id):
        return

    data = load_data()
    bot.reply_to(message, f"👥 Total Users: {len(data['users'])}")

# ---------- ADMINS ----------
@bot.message_handler(commands=["admins"])
def admins_cmd(message):
    if not is_admin(message.from_user.id):
        return

    data = load_data()
    text = "👑 Admin List:\n"
    for admin in data["admins"]:
        text += f"{admin} (admin)\n"

    bot.reply_to(message, text)

# ---------- CLEAN TEXT ----------
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    return text.strip()

# ---------- FILE HANDLER ----------
@bot.message_handler(content_types=["document", "video", "photo", "audio", "voice"])
def handle_file(message):
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
print("Bot Running...")
bot.infinity_polling()
