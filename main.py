import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import re
import time
from datetime import datetime

TOKEN = "8163746024:AAEXe_-2GP3_H7KbT6bj5tp5-fcm8DZfLn4"
MAIN_ADMIN = 1086634832
FORCE_CHANNEL = "@loader0fficial"
BOT_USERNAME = "Loader_father_bot"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# ---------------- DATABASE ---------------- #

cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS banned (id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS warnings (id INTEGER PRIMARY KEY, count INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS commands (name TEXT PRIMARY KEY, time TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS files (cmd TEXT, file_id TEXT, type TEXT)")
conn.commit()

cursor.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (MAIN_ADMIN,))
conn.commit()

# ---------------- HELPERS ---------------- #

def is_admin(user_id):
    cursor.execute("SELECT id FROM admins WHERE id=?", (user_id,))
    return cursor.fetchone() is not None

def is_banned(user_id):
    cursor.execute("SELECT id FROM banned WHERE id=?", (user_id,))
    return cursor.fetchone() is not None

def force_join_check(user_id):
    try:
        status = bot.get_chat_member(FORCE_CHANNEL, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

def join_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"))
    markup.add(InlineKeyboardButton("Verify", callback_data="verify"))
    return markup

def clean_caption(text):
    if not text:
        return None
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    return text.strip()

# ---------------- START ---------------- #

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id

    if is_banned(user_id):
        return

    if not force_join_check(user_id):
        bot.send_message(msg.chat.id, "Please join channel first", reply_markup=join_markup())
        return

    cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?)",
                   (user_id, msg.from_user.username))
    conn.commit()

    bot.send_message(msg.chat.id, "✅ Bot is working!")

# ---------------- VERIFY ---------------- #

@bot.callback_query_handler(func=lambda call: call.data=="verify")
def verify(call):
    if force_join_check(call.from_user.id):
        bot.edit_message_text("✅ Verified Successfully",
                              call.message.chat.id,
                              call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Join channel first")

# ---------------- HELP ---------------- #

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    if is_admin(msg.from_user.id):
        text = """👑 Admin Commands:
/set <name>
/done
/delcmd <name>
/broadcast <text>
/ban <id>
/unban <id>
/users
/banlist"""
    else:
        text = "📌 Available Commands:\n/help"

    bot.send_message(msg.chat.id, text)

# ---------------- USERS ---------------- #

@bot.message_handler(commands=['users'])
def users_count(msg):
    if not is_admin(msg.from_user.id):
        return
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    bot.send_message(msg.chat.id, f"👥 Total Users: {total}")

# ---------------- BAN SYSTEM ---------------- #

@bot.message_handler(commands=['ban'])
def ban_user(msg):
    if not is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.split()[1])
        cursor.execute("INSERT OR IGNORE INTO banned VALUES (?)",(uid,))
        conn.commit()
        bot.send_message(msg.chat.id,"User banned")
    except:
        bot.send_message(msg.chat.id,"Usage: /ban 123456")

@bot.message_handler(commands=['unban'])
def unban_user(msg):
    if not is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.split()[1])
        cursor.execute("DELETE FROM banned WHERE id=?",(uid,))
        conn.commit()
        bot.send_message(msg.chat.id,"User unbanned")
    except:
        bot.send_message(msg.chat.id,"Usage: /unban 123456")

# ---------------- BROADCAST ---------------- #

@bot.message_handler(commands=['broadcast'])
def broadcast(msg):
    if not is_admin(msg.from_user.id):
        return

    text = msg.text.replace("/broadcast","").strip()

    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    for u in users:
        try:
            bot.send_message(u[0], text)
        except:
            pass

    bot.send_message(msg.chat.id,"Broadcast Sent")

# ---------------- COMMAND SYSTEM ---------------- #

uploading = {}

@bot.message_handler(commands=['set'])
def set_cmd(msg):
    if not is_admin(msg.from_user.id):
        return

    try:
        name = msg.text.split()[1]
        uploading[msg.from_user.id] = name
        bot.send_message(msg.chat.id,"Send files then /done")
    except:
        bot.send_message(msg.chat.id,"Usage: /set commandname")

@bot.message_handler(commands=['done'])
def done_cmd(msg):
    if msg.from_user.id not in uploading:
        return

    cmd = uploading[msg.from_user.id]
    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    cursor.execute("INSERT OR REPLACE INTO commands VALUES (?,?)",(cmd,now))
    conn.commit()

    del uploading[msg.from_user.id]

    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    for u in users:
        try:
            bot.send_message(u[0],"🔔 Key Updated")
        except:
            pass

    bot.send_message(msg.chat.id,"Command Saved")

# ---------------- FILE SAVE ---------------- #

@bot.message_handler(content_types=['document','photo','video'])
def save_files(msg):
    if msg.from_user.id not in uploading:
        return

    cmd = uploading[msg.from_user.id]

    if msg.document:
        cursor.execute("INSERT INTO files VALUES (?,?,?)",(cmd,msg.document.file_id,"document"))
    elif msg.photo:
        cursor.execute("INSERT INTO files VALUES (?,?,?)",(cmd,msg.photo[-1].file_id,"photo"))
    elif msg.video:
        cursor.execute("INSERT INTO files VALUES (?,?,?)",(cmd,msg.video.file_id,"video"))

    conn.commit()

# ---------------- CUSTOM COMMAND EXECUTE ---------------- #

@bot.message_handler(func=lambda m: True)
def all_messages(msg):
    user_id = msg.from_user.id

    if is_banned(user_id):
        return

    if not force_join_check(user_id):
        bot.send_message(msg.chat.id,"Join Channel First",reply_markup=join_markup())
        return

    text = msg.text
    cursor.execute("SELECT name,time FROM commands WHERE name=?",(text,))
    data = cursor.fetchone()

    if data:
        cmd,time_saved = data
        cursor.execute("SELECT file_id,type FROM files WHERE cmd=?",(cmd,))
        files = cursor.fetchall()

        for f in files:
            if f[1]=="document":
                bot.send_document(msg.chat.id,f[0])
            elif f[1]=="photo":
                bot.send_photo(msg.chat.id,f[0])
            elif f[1]=="video":
                bot.send_video(msg.chat.id,f[0])

        bot.send_message(msg.chat.id,f"📅 Uploaded: {time_saved}")

bot.infinity_polling()
