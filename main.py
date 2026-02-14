import telebot
from telebot import types
import sqlite3
import re
from datetime import datetime
import pytz

# ================= CONFIG =================

BOT_TOKEN = "8531299371:AAEN-DofYoW7HElnAAq1B2xT-QHZ-HwKNqg"
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
cur.execute("""CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_name TEXT,
    file_id TEXT,
    file_type TEXT,
    caption TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS support_map(
    admin_msg_id TEXT PRIMARY KEY,
    user_id TEXT
)""")

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

    has_link = re.search(r"http\S+", text)
    has_user = re.search(r"@\w+", text)

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "🔰", text)

    return text.strip()

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

def joined(user_id):
    groups = [MAIN_CHANNEL]
    cur.execute("SELECT chat_id FROM force_groups")
    groups += [g[0] for g in cur.fetchall()]

    for g in groups:
        try:
            status = bot.get_chat_member(g, int(user_id)).status
            if status not in ["member","administrator","creator"]:
                return False
        except:
            return False
    return True

def join_buttons():
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
def start(msg):
    uid = str(msg.from_user.id)

    if is_banned(uid):
        return

    register_user(msg.from_user)

    if not joined(uid):
        bot.send_message(msg.chat.id,
                         "Please join required groups",
                         reply_markup=join_buttons())
        return

    bot.send_message(msg.chat.id,"Verified ✅\nUse /cmd")

@bot.callback_query_handler(func=lambda c: c.data=="verify")
def verify(call):
    if joined(call.from_user.id):
        bot.edit_message_text("Verified ✅\nUse /cmd",
                              call.message.chat.id,
                              call.message.message_id)
    else:
        bot.answer_callback_query(call.id,"Join all groups first")

# ================= CMD PANEL =================

@bot.message_handler(commands=["cmd"])
def cmd(msg):
    uid = str(msg.from_user.id)

    if is_banned(uid):
        return

    if is_admin(uid):
        text = """👑 Admin Panel:

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
        cmds = cur.fetchall()

        text="Available Commands:\n\n"
        for c in cmds:
            text+=f"/{c[0]}\n"

        text+="\n/support message\n/cmd"

    bot.send_message(msg.chat.id,text)

# ================= USERLIST (UNCHANGED) =================

@bot.message_handler(commands=["userlist"])
def userlist(msg):
    if not is_admin(str(msg.from_user.id)):
        return

    cur.execute("SELECT user_id,username FROM users")
    users=cur.fetchall()

    text=f"Total Users: {len(users)}\n\n"
    for u in users:
        if u[1]:
            text+=f"@{u[1]} (ID:{u[0]})\n"
        else:
            text+=f"ID:{u[0]}\n"

    bot.send_message(msg.chat.id,text[:4000])

# ================= BAN SYSTEM (UNCHANGED) =================

@bot.message_handler(commands=["ban"])
def ban(msg):
    if not is_admin(str(msg.from_user.id)):
        return
    try:
        uid=msg.text.split()[1]
        cur.execute("INSERT OR IGNORE INTO banned VALUES(?)",(uid,))
        conn.commit()
        bot.send_message(msg.chat.id,"User banned")
    except:
        bot.send_message(msg.chat.id,"Usage: /ban id")

@bot.message_handler(commands=["unban"])
def unban(msg):
    if not is_admin(str(msg.from_user.id)):
        return
    try:
        uid=msg.text.split()[1]
        cur.execute("DELETE FROM banned WHERE user_id=?",(uid,))
        conn.commit()
        bot.send_message(msg.chat.id,"User unbanned")
    except:
        bot.send_message(msg.chat.id,"Usage: /unban id")

@bot.message_handler(commands=["banlist"])
def banlist(msg):
    if not is_admin(str(msg.from_user.id)):
        return
    cur.execute("SELECT user_id FROM banned")
    users=cur.fetchall()
    text="Banned Users:\n\n"
    for u in users:
        text+=f"{u[0]}\n"
    bot.send_message(msg.chat.id,text)

# ================= FORCE =================

@bot.message_handler(commands=["addforce"])
def addforce(msg):
    if not is_admin(str(msg.from_user.id)):
        return
    try:
        gid=msg.text.split()[1]
        cur.execute("INSERT OR IGNORE INTO force_groups VALUES(?)",(gid,))
        conn.commit()
        bot.send_message(msg.chat.id,"Force group added")
    except:
        bot.send_message(msg.chat.id,"Usage: /addforce @group")

@bot.message_handler(commands=["delforce"])
def delforce(msg):
    if not is_admin(str(msg.from_user.id)):
        return
    try:
        gid=msg.text.split()[1]
        cur.execute("DELETE FROM force_groups WHERE chat_id=?",(gid,))
        conn.commit()
        bot.send_message(msg.chat.id,"Force group removed")
    except:
        bot.send_message(msg.chat.id,"Usage: /delforce @group")

# ================= BROADCAST =================

@bot.message_handler(commands=["broadcast"])
def broadcast(msg):
    if str(msg.from_user.id)!=str(MAIN_ADMIN):
        return

    text=msg.text.replace("/broadcast","").strip()
    if not text:
        bot.send_message(msg.chat.id,"Usage: /broadcast message")
        return

    cur.execute("SELECT user_id FROM users")
    users=cur.fetchall()

    for u in users:
        try:
            bot.send_message(u[0],text)
        except:
            pass

    bot.send_message(msg.chat.id,"Broadcast Sent")

# ================= SUPPORT =================

@bot.message_handler(commands=["support"])
def support(msg):
    uid=str(msg.from_user.id)
    if is_banned(uid):
        return

    text=msg.text.replace("/support","").strip()
    if not text:
        bot.send_message(msg.chat.id,"Usage: /support message")
        return

    sent=bot.send_message(MAIN_ADMIN,
                          f"Support Request\n\nUser: {uid}\n\n{text}\n\nReply to respond")

    cur.execute("INSERT OR REPLACE INTO support_map VALUES(?,?)",
                (str(sent.message_id),uid))
    conn.commit()

    bot.send_message(msg.chat.id,"Message sent to admin")

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def reply_support(msg):
    if not is_admin(str(msg.from_user.id)):
        return

    reply_id=str(msg.reply_to_message.message_id)
    cur.execute("SELECT user_id FROM support_map WHERE admin_msg_id=?",(reply_id,))
    row=cur.fetchone()

    if row:
        bot.send_message(row[0],f"Admin Reply:\n\n{msg.text}")

# ================= RUN =================

print("Bot Running...")
bot.infinity_polling(timeout=60,long_polling_timeout=60)
