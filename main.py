import telebot
from telebot import types
import sqlite3
import pytz
from datetime import datetime

# ================= CONFIG =================

BOT_TOKEN = "8163746024:AAGq9JB1oyYF0EvEtOBgE4O73RP7jfOcqPE"
MAIN_ADMIN = 1086634832

bot = telebot.TeleBot(BOT_TOKEN)

# ================= DATABASE =================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id TEXT PRIMARY KEY,
    username TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS admins(
    user_id TEXT PRIMARY KEY
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS banned(
    user_id TEXT PRIMARY KEY
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS force_groups(
    chat_id TEXT PRIMARY KEY
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS commands(
    name TEXT PRIMARY KEY,
    upload_time TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_name TEXT,
    file_id TEXT,
    file_type TEXT,
    caption TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS warnings(
    user_id TEXT PRIMARY KEY,
    count INTEGER
)""")

conn.commit()

# Insert main admin
cur.execute("INSERT OR IGNORE INTO admins VALUES(?)", (str(MAIN_ADMIN),))
conn.commit()

# ================= UTIL =================

def ist_time():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%d-%m-%Y %H:%M")

def is_admin(uid):
    cur.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def is_banned(uid):
    cur.execute("SELECT 1 FROM banned WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def register_user(user):
    cur.execute("INSERT OR IGNORE INTO users VALUES(?,?)",
                (str(user.id), user.username))
    conn.commit()

def check_force_join(user_id):
    cur.execute("SELECT chat_id FROM force_groups")
    groups = cur.fetchall()
    for (gid,) in groups:
        try:
            status = bot.get_chat_member(gid, int(user_id)).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def force_join_message(chat_id):
    markup = types.InlineKeyboardMarkup()
    cur.execute("SELECT chat_id FROM force_groups")
    groups = cur.fetchall()
    for (gid,) in groups:
        if gid.startswith("@"):
            link = f"https://t.me/{gid.replace('@','')}"
            markup.add(types.InlineKeyboardButton("Join Group", url=link))
    bot.send_message(chat_id, "⚠ Please join required groups first.", reply_markup=markup)

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)

    if is_banned(uid):
        return

    register_user(message.from_user)

    if not check_force_join(uid):
        force_join_message(message.chat.id)
        return

    bot.send_message(message.chat.id, "✅ Welcome to Study Bot\nUse /cmd")

# ================= CMD =================

@bot.message_handler(commands=['cmd'])
def show_cmd(message):
    uid = str(message.from_user.id)

    if is_banned(uid):
        return

    if is_admin(uid):
        text = """👑 Admin Commands:
/set name
/done
/deletecmd name
/edit name
/ban id
/unban id
/banlist
/userlist
/addforce chat_id
/delforce chat_id
/cmd"""
    else:
        if not check_force_join(uid):
            force_join_message(message.chat.id)
            return

        cur.execute("SELECT name FROM commands")
        cmds = cur.fetchall()
        text = "📦 Available Commands:\n\n"
        for (c,) in cmds:
            text += f"/{c}\n"

        text += "\n/cmd"

    bot.send_message(message.chat.id, text)

# ================= SET =================

current_set = {}

@bot.message_handler(commands=['set'])
def set_command(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        return

    try:
        name = message.text.split()[1]
        current_set[uid] = name
        cur.execute("DELETE FROM files WHERE command_name=?", (name,))
        cur.execute("INSERT OR REPLACE INTO commands VALUES(?,?)", (name, ""))
        conn.commit()
        bot.send_message(message.chat.id, "Send files now then /done")
    except:
        bot.send_message(message.chat.id, "Usage: /set commandname")

# ================= FILE HANDLER =================

@bot.message_handler(content_types=['document','photo','video','audio'])
def save_files(message):
    uid = str(message.from_user.id)

    if uid not in current_set:
        return

    cmd = current_set[uid]

    file_id = None
    file_type = message.content_type

    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.audio:
        file_id = message.audio.file_id

    caption = message.caption

    cur.execute("INSERT INTO files(command_name,file_id,file_type,caption) VALUES(?,?,?,?)",
                (cmd,file_id,file_type,caption))
    conn.commit()

# ================= DONE =================

@bot.message_handler(commands=['done'])
def done(message):
    uid = str(message.from_user.id)
    if uid not in current_set:
        return

    cmd = current_set[uid]
    upload_time = ist_time()

    cur.execute("UPDATE commands SET upload_time=? WHERE name=?",
                (upload_time,cmd))
    conn.commit()

    del current_set[uid]

    # Broadcast
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    for (u,) in users:
        try:
            bot.send_message(u, f"🔔 Key Updated\nUse /{cmd}")
        except:
            pass

    bot.send_message(message.chat.id, "✅ Saved & Broadcasted")

# ================= COMMAND CALL =================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
def dynamic_command(message):
    uid = str(message.from_user.id)

    if is_banned(uid):
        return

    if not check_force_join(uid):
        force_join_message(message.chat.id)
        return

    cmd = message.text[1:]

    cur.execute("SELECT upload_time FROM commands WHERE name=?", (cmd,))
    row = cur.fetchone()
    if not row:
        return

    upload_time = row[0]

    cur.execute("SELECT file_id,file_type,caption FROM files WHERE command_name=?", (cmd,))
    files = cur.fetchall()

    for file_id,file_type,caption in files:
        if file_type=="document":
            bot.send_document(message.chat.id,file_id,caption=caption)
        elif file_type=="photo":
            bot.send_photo(message.chat.id,file_id,caption=caption)
        elif file_type=="video":
            bot.send_video(message.chat.id,file_id,caption=caption)
        elif file_type=="audio":
            bot.send_audio(message.chat.id,file_id,caption=caption)

    bot.send_message(message.chat.id, f"📅 Uploaded: {upload_time}")

# ================= BAN =================

@bot.message_handler(commands=['ban'])
def ban(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        return
    try:
        target = message.text.split()[1]
        cur.execute("INSERT OR IGNORE INTO banned VALUES(?)",(target,))
        conn.commit()
        bot.send_message(message.chat.id,"User banned")
    except:
        bot.send_message(message.chat.id,"Usage: /ban user_id")

# ================= UNBAN =================

@bot.message_handler(commands=['unban'])
def unban(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        return
    try:
        target = message.text.split()[1]
        cur.execute("DELETE FROM banned WHERE user_id=?",(target,))
        conn.commit()
        bot.send_message(message.chat.id,"User unbanned")
    except:
        bot.send_message(message.chat.id,"Usage: /unban user_id")

# ================= BANLIST =================

@bot.message_handler(commands=['banlist'])
def banlist(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        return
    cur.execute("SELECT user_id FROM banned")
    data = cur.fetchall()
    text="🚫 Banned Users:\n"
    for (u,) in data:
        text+=f"{u}\n"
    bot.send_message(message.chat.id,text)

# ================= USERLIST =================

@bot.message_handler(commands=['userlist'])
def userlist(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        return
    cur.execute("SELECT user_id,username FROM users")
    data = cur.fetchall()
    text=f"📊 Total Users: {len(data)}\n\n"
    for u,name in data:
        if name:
            text+=f"@{name} (ID: {u})\n"
        else:
            text+=f"{u}\n"
    bot.send_message(message.chat.id,text[:4000])

# ================= FORCE GROUP MANAGEMENT =================

@bot.message_handler(commands=['addforce'])
def addforce(message):
    if not is_admin(str(message.from_user.id)):
        return
    try:
        gid = message.text.split()[1]
        cur.execute("INSERT OR IGNORE INTO force_groups VALUES(?)",(gid,))
        conn.commit()
        bot.send_message(message.chat.id,"Force group added")
    except:
        bot.send_message(message.chat.id,"Usage: /addforce @group")

@bot.message_handler(commands=['delforce'])
def delforce(message):
    if not is_admin(str(message.from_user.id)):
        return
    try:
        gid = message.text.split()[1]
        cur.execute("DELETE FROM force_groups WHERE chat_id=?",(gid,))
        conn.commit()
        bot.send_message(message.chat.id,"Force group removed")
    except:
        bot.send_message(message.chat.id,"Usage: /delforce @group")

# ================= RUN =================

print("Bot Running...")
bot.infinity_polling(timeout=60,long_polling_timeout=60)
