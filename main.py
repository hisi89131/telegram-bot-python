import telebot
from telebot import types
import sqlite3
import re
from datetime import datetime
import pytz

# ================= CONFIG =================

BOT_TOKEN = "8531299371:AAG_x1EsAbLrjeRTtWyFcnn7LrpPN3NGd18"
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
cur.execute("CREATE TABLE IF NOT EXISTS commands (name TEXT PRIMARY KEY, upload_time TEXT, owner TEXT)")
cur.execute("""CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_name TEXT,
    file_id TEXT,
    file_type TEXT,
    caption TEXT
)""")
cur.execute("CREATE TABLE IF NOT EXISTS support_map (admin_msg_id TEXT PRIMARY KEY, user_id TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS bot_groups (chat_id TEXT PRIMARY KEY)")
conn.commit()

cur.execute("INSERT OR IGNORE INTO admins VALUES(?)", (str(MAIN_ADMIN),))
conn.commit()

# ================= UTIL =================

def ist_time():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%d-%m-%Y %H:%M")

def clean_caption(text):
    if not text:
        return None

    original = text

    has_link = re.search(r"http\S+", text)
    has_username = re.search(r"@\w+", text)

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "🔰", text)

    if has_link or has_username:
        return text.strip()
    else:
        return original  # preserve mono if no link/username

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

# ================= FORCE JOIN =================

def check_join(user_id):
    groups = [MAIN_CHANNEL]
    cur.execute("SELECT chat_id FROM force_groups")
    groups += [g[0] for g in cur.fetchall()]

    for g in groups:
        try:
            status = bot.get_chat_member(g, int(user_id)).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_markup():
    markup = types.InlineKeyboardMarkup()
    groups = [MAIN_CHANNEL]
    cur.execute("SELECT chat_id FROM force_groups")
    groups += [g[0] for g in cur.fetchall()]

    for g in groups:
        link = f"https://t.me/{g.replace('@','')}"
        markup.add(types.InlineKeyboardButton(f"Join {g}", url=link))

    markup.add(types.InlineKeyboardButton("Verify ✅", callback_data="verify"))
    return markup

# ================= START =================

@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.from_user.id)

    if is_banned(uid):
        return

    register_user(message.from_user)

    if not check_join(uid):
        bot.send_message(message.chat.id,
                         "Join required groups first",
                         reply_markup=join_markup())
        return

    bot.send_message(message.chat.id, "Verified ✅\nUse /cmd")

# ================= VERIFY =================

@bot.callback_query_handler(func=lambda c: c.data == "verify")
def verify(call):
    if check_join(call.from_user.id):
        bot.edit_message_text("Verified ✅\nUse /cmd",
                              call.message.chat.id,
                              call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Join all groups first")

# ================= CMD =================

@bot.message_handler(commands=["cmd"])
def cmd(message):
    uid = str(message.from_user.id)

    if is_banned(uid):
        return

    if is_admin(uid):
        text = """👑 Admin Commands:

/set name
/done
/ban id
/unban id
/banlist
/userlist
/addadmin id
/removeadmin id
/adminlist
/addforce @group
/delforce @group
/broadcast message
/support message
/cmd"""
    else:
        if not check_join(uid):
            bot.send_message(message.chat.id,
                             "Join required groups",
                             reply_markup=join_markup())
            return

        cur.execute("SELECT name FROM commands")
        cmds = cur.fetchall()

        text = "📦 Available Commands:\n\n"
        for c in cmds:
            text += f"/{c[0]}\n"

        text += "\n/support message\n/cmd"

    bot.send_message(message.chat.id, text)

# ================= COMMAND SET =================

current_set = {}

@bot.message_handler(commands=["set"])
def set_command(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        return

    try:
        name = message.text.split()[1]
        current_set[uid] = name

        cur.execute("INSERT OR REPLACE INTO commands VALUES(?,?,?)",
                    (name, "", uid))
        cur.execute("DELETE FROM files WHERE command_name=?", (name,))
        conn.commit()

        bot.send_message(message.chat.id, "Send files then /done")

    except:
        bot.send_message(message.chat.id, "Usage: /set name")

# ================= FILE SAVE =================

@bot.message_handler(content_types=["document","photo","video","audio"])
def save_file(message):
    uid = str(message.from_user.id)

    if uid not in current_set:
        return

    cmd = current_set[uid]

    if message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
    else:
        return

    caption = clean_caption(message.caption)

    cur.execute("INSERT INTO files(command_name,file_id,file_type,caption) VALUES(?,?,?,?)",
                (cmd,file_id,file_type,caption))
    conn.commit()

# ================= DONE =================

@bot.message_handler(commands=["done"])
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

    bot.send_message(message.chat.id,"Saved & Updated")

# ================= DYNAMIC =================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
def dynamic(message):
    uid = str(message.from_user.id)

    if is_banned(uid):
        return

    cmd = message.text[1:]

    cur.execute("SELECT upload_time FROM commands WHERE name=?", (cmd,))
    row = cur.fetchone()

    if not row:
        return

    if not check_join(uid):
        bot.send_message(message.chat.id,
                         "Join required groups",
                         reply_markup=join_markup())
        return

    upload_time = row[0]

    cur.execute("SELECT file_id,file_type,caption FROM files WHERE command_name=?", (cmd,))
    files = cur.fetchall()

    for f in files:
        if f[1]=="document":
            bot.send_document(message.chat.id,f[0],caption=f[2])
        elif f[1]=="photo":
            bot.send_photo(message.chat.id,f[0],caption=f[2])
        elif f[1]=="video":
            bot.send_video(message.chat.id,f[0],caption=f[2])
        elif f[1]=="audio":
            bot.send_audio(message.chat.id,f[0],caption=f[2])

    bot.send_message(message.chat.id, f"📅 Uploaded: {upload_time}")

# ================= SUPPORT =================

@bot.message_handler(commands=["support"])
def support(message):
    uid = str(message.from_user.id)

    if is_banned(uid):
        return

    text = message.text.replace("/support","").strip()
    if not text:
        bot.send_message(message.chat.id,"Usage: /support message")
        return

    sent = bot.send_message(
        MAIN_ADMIN,
        f"Support Request\nUser: {uid}\n\n{text}\n\nReply to respond."
    )

    cur.execute("INSERT OR REPLACE INTO support_map VALUES(?,?)",
                (str(sent.message_id), uid))
    conn.commit()

    bot.send_message(message.chat.id,"Message sent to admin")

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def reply_support(message):
    if not is_admin(str(message.from_user.id)):
        return

    reply_id = str(message.reply_to_message.message_id)
    cur.execute("SELECT user_id FROM support_map WHERE admin_msg_id=?",(reply_id,))
    row = cur.fetchone()

    if row:
        bot.send_message(row[0], f"Admin Reply:\n\n{message.text}")

# ================= RUN =================

print("Bot Running...")
bot.infinity_polling(timeout=60,long_polling_timeout=60)
