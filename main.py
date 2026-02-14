import telebot
from telebot import types
import sqlite3
import re
from datetime import datetime
import pytz

# ================= CONFIG =================

BOT_TOKEN = "8531299371:AAHSpAzJgp9HxOZM6MTLf1tBkA2gToLpsW8"
MAIN_ADMIN = 1086634832
MAIN_CHANNEL = "@loader0fficial"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ================= DATABASE =================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS admins (user_id TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS banned (user_id TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS force_groups (chat_id TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS commands (name TEXT PRIMARY KEY, upload_time TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, command_name TEXT, file_id TEXT, file_type TEXT, caption TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS support (admin_msg_id TEXT PRIMARY KEY, user_id TEXT)")
conn.commit()

cur.execute("INSERT OR IGNORE INTO admins VALUES(?)", (str(MAIN_ADMIN),))
conn.commit()

# ================= UTIL =================

def ist():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%d-%m-%Y %H:%M")

def clean_caption(text):
    if not text:
        return None

    has_link = re.search(r"http\S+", text)
    has_user = re.search(r"@\w+", text)

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "🔰", text)

    if has_link or has_user:
        return text.strip()
    return text  # preserve mono if no change

def is_admin(uid):
    cur.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def is_banned(uid):
    cur.execute("SELECT 1 FROM banned WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def register(user):
    cur.execute("INSERT OR IGNORE INTO users VALUES(?,?)",
                (str(user.id), user.username))
    conn.commit()

# ================= FORCE JOIN =================

def required_groups():
    groups = [MAIN_CHANNEL]
    cur.execute("SELECT chat_id FROM force_groups")
    groups += [g[0] for g in cur.fetchall()]
    return groups

def joined(uid):
    for g in required_groups():
        try:
            status = bot.get_chat_member(g, int(uid)).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_buttons():
    markup = types.InlineKeyboardMarkup()
    for g in required_groups():
        link = f"https://t.me/{g.replace('@','')}"
        markup.add(types.InlineKeyboardButton(f"Join {g}", url=link))
    markup.add(types.InlineKeyboardButton("Verify ✅", callback_data="verify"))
    return markup

# ================= START =================

@bot.message_handler(commands=["start"])
def start(msg):
    uid = str(msg.from_user.id)

    if is_banned(uid):
        return

    register(msg.from_user)

    if not joined(uid):
        bot.send_message(msg.chat.id,
                         "⚠️ Join all required groups",
                         reply_markup=join_buttons())
        return

    bot.send_message(msg.chat.id, "✅ Verified\nUse /cmd")

# ================= VERIFY =================

@bot.callback_query_handler(func=lambda c: c.data=="verify")
def verify(call):
    if joined(call.from_user.id):
        bot.edit_message_text("✅ Verified\nUse /cmd",
                              call.message.chat.id,
                              call.message.message_id)
    else:
        bot.answer_callback_query(call.id,"Join all groups first")

# ================= CMD =================

@bot.message_handler(commands=["cmd"])
def cmd(msg):
    uid = str(msg.from_user.id)

    if is_banned(uid):
        return

    if is_admin(uid):
        text = """👑 Admin Panel

/set name
/done
/ban id
/unban id
/banlist
/userlist
/addforce @group
/delforce @group
/broadcast message
/support message
/cmd"""
    else:
        if not joined(uid):
            bot.send_message(msg.chat.id,
                             "Join required groups",
                             reply_markup=join_buttons())
            return

        cur.execute("SELECT name FROM commands")
        rows = cur.fetchall()

        text = "📦 Available Commands:\n\n"
        for r in rows:
            text += f"/{r[0]}\n"

        text += "\n/support message\n/cmd"

    bot.send_message(msg.chat.id, text)

# ================= SET =================

active_set = {}

@bot.message_handler(commands=["set"])
def set_cmd(msg):
    uid = str(msg.from_user.id)
    if not is_admin(uid):
        return
    try:
        name = msg.text.split()[1]
        active_set[uid] = name
        cur.execute("INSERT OR REPLACE INTO commands VALUES(?,?)", (name,""))
        cur.execute("DELETE FROM files WHERE command_name=?", (name,))
        conn.commit()
        bot.send_message(msg.chat.id,"Send files then /done")
    except:
        bot.send_message(msg.chat.id,"Usage: /set name")

# ================= SAVE FILE =================

@bot.message_handler(content_types=["document","photo","video","audio"])
def save_file(msg):
    uid = str(msg.from_user.id)
    if uid not in active_set:
        return

    cmd = active_set[uid]

    if msg.document:
        fid = msg.document.file_id
        ftype = "document"
    elif msg.photo:
        fid = msg.photo[-1].file_id
        ftype = "photo"
    elif msg.video:
        fid = msg.video.file_id
        ftype = "video"
    elif msg.audio:
        fid = msg.audio.file_id
        ftype = "audio"
    else:
        return

    cap = clean_caption(msg.caption)

    cur.execute("INSERT INTO files(command_name,file_id,file_type,caption) VALUES(?,?,?,?)",
                (cmd,fid,ftype,cap))
    conn.commit()

# ================= DONE =================

@bot.message_handler(commands=["done"])
def done(msg):
    uid = str(msg.from_user.id)
    if uid not in active_set:
        return

    cmd = active_set[uid]
    time = ist()

    cur.execute("UPDATE commands SET upload_time=? WHERE name=?", (time,cmd))
    conn.commit()

    del active_set[uid]

    bot.send_message(msg.chat.id,"✅ Saved")

# ================= DYNAMIC =================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
def dynamic(msg):
    uid = str(msg.from_user.id)
    if is_banned(uid):
        return

    cmd = msg.text[1:]

    builtins = ["start","cmd","set","done","ban","unban",
                "banlist","userlist","addforce","delforce",
                "broadcast","support"]

    if cmd in builtins:
        return

    cur.execute("SELECT upload_time FROM commands WHERE name=?", (cmd,))
    row = cur.fetchone()
    if not row:
        return

    if not joined(uid):
        bot.send_message(msg.chat.id,
                         "Join required groups",
                         reply_markup=join_buttons())
        return

    cur.execute("SELECT file_id,file_type,caption FROM files WHERE command_name=?", (cmd,))
    files = cur.fetchall()

    for f in files:
        if f[1]=="document":
            bot.send_document(msg.chat.id,f[0],caption=f[2])
        elif f[1]=="photo":
            bot.send_photo(msg.chat.id,f[0],caption=f[2])
        elif f[1]=="video":
            bot.send_video(msg.chat.id,f[0],caption=f[2])
        elif f[1]=="audio":
            bot.send_audio(msg.chat.id,f[0],caption=f[2])

    bot.send_message(msg.chat.id, f"📅 Uploaded: {row[0]}")

# ================= USERLIST =================

@bot.message_handler(commands=["userlist"])
def userlist(msg):
    if not is_admin(str(msg.from_user.id)):
        return
    cur.execute("SELECT user_id,username FROM users")
    data = cur.fetchall()
    text = f"Total Users: {len(data)}\n\n"
    for u in data:
        if u[1]:
            text += f"@{u[1]} (ID: {u[0]})\n"
        else:
            text += f"{u[0]}\n"
    bot.send_message(msg.chat.id,text[:4000])

# ================= SUPPORT =================

@bot.message_handler(commands=["support"])
def support(msg):
    uid = str(msg.from_user.id)
    if is_banned(uid):
        return
    text = msg.text.replace("/support","").strip()
    if not text:
        bot.send_message(msg.chat.id,"Usage: /support message")
        return

    sent = bot.send_message(MAIN_ADMIN,
                            f"Support\nUser: {uid}\n\n{text}\n\nReply to respond")

    cur.execute("INSERT OR REPLACE INTO support VALUES(?,?)",
                (str(sent.message_id), uid))
    conn.commit()

    bot.send_message(msg.chat.id,"Message sent to admin")

@bot.message_handler(func=lambda m: m.reply_to_message)
def support_reply(msg):
    if not is_admin(str(msg.from_user.id)):
        return
    rid = str(msg.reply_to_message.message_id)
    cur.execute("SELECT user_id FROM support WHERE admin_msg_id=?", (rid,))
    row = cur.fetchone()
    if row:
        bot.send_message(row[0], f"Admin Reply:\n\n{msg.text}")

# ================= RUN =================

print("Bot Running...")
bot.infinity_polling(timeout=60,long_polling_timeout=60)
