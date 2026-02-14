import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import re
from datetime import datetime

TOKEN = "8163746024:AAFjaZm-0gQw2bu0pBrcI_a14KJXAo7ZV0o"
MAIN_ADMIN = 1086634832
FORCE_CHANNEL = "@loader0fficial"
BOT_USERNAME = "Loader_father_bot"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# ---------------- DATABASE ---------------- #

cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS banned (id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS commands (name TEXT PRIMARY KEY, time TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS files (cmd TEXT, file_id TEXT, type TEXT)")
conn.commit()

cursor.execute("INSERT OR IGNORE INTO admins VALUES (?)",(MAIN_ADMIN,))
conn.commit()

# ---------------- HELPERS ---------------- #

def is_admin(uid):
    cursor.execute("SELECT id FROM admins WHERE id=?",(uid,))
    return cursor.fetchone() is not None

def is_banned(uid):
    cursor.execute("SELECT id FROM banned WHERE id=?",(uid,))
    return cursor.fetchone() is not None

def joined(uid):
    try:
        status = bot.get_chat_member(FORCE_CHANNEL, uid).status
        return status in ["member","administrator","creator"]
    except:
        return False

def join_markup():
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"))
    m.add(InlineKeyboardButton("Verify", callback_data="verify"))
    return m

def clean_caption(text):
    if not text:
        return None
    text = re.sub(r'https?://\S+','',text)
    text = re.sub(r'@\w+','',text)
    return text.strip()

# ---------------- START ---------------- #

@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id

    if is_banned(uid):
        return

    if not joined(uid):
        bot.send_message(msg.chat.id,"❌ Join Channel First",reply_markup=join_markup())
        return

    cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?)",
                   (uid,msg.from_user.username))
    conn.commit()

    bot.send_message(msg.chat.id,"✅ Verified Successfully\nUse /help")

# ---------------- VERIFY ---------------- #

@bot.callback_query_handler(func=lambda call: call.data=="verify")
def verify(call):
    if joined(call.from_user.id):
        bot.edit_message_text("✅ Verified Successfully\nUse /help",
                              call.message.chat.id,
                              call.message.message_id)
    else:
        bot.answer_callback_query(call.id,"Join Channel First")

# ---------------- HELP ---------------- #

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    if not joined(msg.from_user.id):
        bot.send_message(msg.chat.id,"❌ Join Channel First",reply_markup=join_markup())
        return

    if is_admin(msg.from_user.id):
        text = """👑 Admin Panel:
/set <name>
/done
/delcmd <name>
/broadcast <text>
/ban <id>
/unban <id>
/banlist
/users"""
    else:
        text = "📌 Available Commands:\nUse custom command like /loader1"

    bot.send_message(msg.chat.id,text)

# ---------------- USERS ---------------- #

@bot.message_handler(commands=['users'])
def users(msg):
    if not is_admin(msg.from_user.id):
        return
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    bot.send_message(msg.chat.id,f"👥 Total Users: {total}")

# ---------------- BAN ---------------- #

@bot.message_handler(commands=['ban'])
def ban(msg):
    if not is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.split()[1])
        cursor.execute("INSERT OR IGNORE INTO banned VALUES (?)",(uid,))
        conn.commit()
        bot.send_message(msg.chat.id,"User Banned")
    except:
        bot.send_message(msg.chat.id,"Usage: /ban 123456")

@bot.message_handler(commands=['unban'])
def unban(msg):
    if not is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.split()[1])
        cursor.execute("DELETE FROM banned WHERE id=?",(uid,))
        conn.commit()
        bot.send_message(msg.chat.id,"User Unbanned")
    except:
        bot.send_message(msg.chat.id,"Usage: /unban 123456")

@bot.message_handler(commands=['banlist'])
def banlist(msg):
    if not is_admin(msg.from_user.id):
        return
    cursor.execute("SELECT id FROM banned")
    data = cursor.fetchall()
    text = "🚫 Ban List:\n"
    for u in data:
        text += str(u[0])+"\n"
    bot.send_message(msg.chat.id,text)

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
            bot.send_message(u[0],text)
        except:
            pass

    bot.send_message(msg.chat.id,"Broadcast Done")

# ---------------- CUSTOM COMMAND SYSTEM ---------------- #

uploading = {}

@bot.message_handler(commands=['set'])
def set_cmd(msg):
    if not is_admin(msg.from_user.id):
        return
    try:
        name = msg.text.split()[1].replace("/","")
        uploading[msg.from_user.id] = name
        bot.send_message(msg.chat.id,"Send Files Now Then /done")
    except:
        bot.send_message(msg.chat.id,"Usage: /set loader1")

@bot.message_handler(commands=['done'])
def done(msg):
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

    bot.send_message(msg.chat.id,"Command Saved & Broadcasted")

# ---------------- FILE SAVE ---------------- #

@bot.message_handler(content_types=['document','photo','video'])
def save_file(msg):
    if msg.from_user.id not in uploading:
        return

    cmd = uploading[msg.from_user.id]

    if msg.document:
        cursor.execute("INSERT INTO files VALUES (?,?,?)",
                       (cmd,msg.document.file_id,"document"))
    elif msg.photo:
        cursor.execute("INSERT INTO files VALUES (?,?,?)",
                       (cmd,msg.photo[-1].file_id,"photo"))
    elif msg.video:
        cursor.execute("INSERT INTO files VALUES (?,?,?)",
                       (cmd,msg.video.file_id,"video"))

    conn.commit()

# ---------------- CUSTOM COMMAND EXECUTE ---------------- #

@bot.message_handler(func=lambda m: True)
def handle_all(msg):
    uid = msg.from_user.id

    if is_banned(uid):
        return

    if not joined(uid):
        bot.send_message(msg.chat.id,"❌ Join Channel First",reply_markup=join_markup())
        return

    if not msg.text:
        return

    cmd = msg.text.replace("/","")

    cursor.execute("SELECT name,time FROM commands WHERE name=?",(cmd,))
    data = cursor.fetchone()

    if data:
        name,time_saved = data

        cursor.execute("SELECT file_id,type FROM files WHERE cmd=?",(name,))
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
