import telebot
from telebot import types
import sqlite3
import re
from datetime import datetime
import pytz

BOT_TOKEN = "8232988598:AAGHFJRxnJozLOixN1a4GvgbLswMrMd7zAI"
MAIN_ADMIN = 1086634832
MAIN_CHANNEL = "@loader0fficial"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# ================= DATABASE =================

cur.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS admins (user_id TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS banned (user_id TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS force_groups (chat_id TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS commands (name TEXT PRIMARY KEY, owner TEXT, upload_time TEXT)")
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
cur.execute("INSERT OR IGNORE INTO admins VALUES(?)",(str(MAIN_ADMIN),))
conn.commit()

# ================= UTIL =================

def ist():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%d-%m-%Y %H:%M")

def clean(text):
    if not text:
        return None
    text = re.sub(r"http\S+","",text)
    text = re.sub(r"@\w+","🔰",text)
    return text.strip()

def is_admin(uid):
    cur.execute("SELECT 1 FROM admins WHERE user_id=?",(uid,))
    return cur.fetchone() is not None

def is_banned(uid):
    cur.execute("SELECT 1 FROM banned WHERE user_id=?",(uid,))
    return cur.fetchone() is not None

# ================= BAN SYSTEM =================

@bot.message_handler(commands=["ban"])
def ban(m):
    if not is_admin(str(m.from_user.id)):
        return
    try:
        uid=m.text.split()[1]
        cur.execute("INSERT OR IGNORE INTO banned VALUES(?)",(uid,))
        conn.commit()
        bot.send_message(m.chat.id,"User banned")
    except:
        bot.send_message(m.chat.id,"Usage: /ban user_id")

@bot.message_handler(commands=["unban"])
def unban(m):
    if not is_admin(str(m.from_user.id)):
        return
    try:
        uid=m.text.split()[1]
        cur.execute("DELETE FROM banned WHERE user_id=?",(uid,))
        conn.commit()
        bot.send_message(m.chat.id,"User unbanned")
    except:
        bot.send_message(m.chat.id,"Usage: /unban user_id")

@bot.message_handler(commands=["banlist"])
def banlist(m):
    if not is_admin(str(m.from_user.id)):
        return
    cur.execute("SELECT user_id FROM banned")
    data=cur.fetchall()
    text="Banned Users:\n\n"
    for u in data:
        text+=f"{u[0]}\n"
    bot.send_message(m.chat.id,text)

# ================= USERLIST =================

@bot.message_handler(commands=["userlist"])
def userlist(m):
    if not is_admin(str(m.from_user.id)):
        return
    cur.execute("SELECT user_id,username FROM users")
    users=cur.fetchall()
    text=f"Total Users: {len(users)}\n\n"
    for u in users:
        if u[1]:
            text+=f"@{u[1]} (ID:{u[0]})\n"
        else:
            text+=f"ID:{u[0]}\n"
    bot.send_message(m.chat.id,text[:4000])

# ================= ADMIN MANAGEMENT =================

@bot.message_handler(commands=["addadmin"])
def addadmin(m):
    if str(m.from_user.id)!=str(MAIN_ADMIN):
        return
    try:
        uid=m.text.split()[1]
        cur.execute("INSERT OR IGNORE INTO admins VALUES(?)",(uid,))
        conn.commit()
        bot.send_message(m.chat.id,"Admin added")
    except:
        bot.send_message(m.chat.id,"Usage: /addadmin user_id")

@bot.message_handler(commands=["removeadmin"])
def removeadmin(m):
    if str(m.from_user.id)!=str(MAIN_ADMIN):
        return
    try:
        uid=m.text.split()[1]
        cur.execute("DELETE FROM admins WHERE user_id=?",(uid,))
        conn.commit()
        bot.send_message(m.chat.id,"Admin removed")
    except:
        bot.send_message(m.chat.id,"Usage: /removeadmin user_id")

@bot.message_handler(commands=["adminlist"])
def adminlist(m):
    if not is_admin(str(m.from_user.id)):
        return
    cur.execute("SELECT user_id FROM admins")
    data=cur.fetchall()
    text="Admins:\n\n"
    for a in data:
        text+=f"{a[0]}\n"
    bot.send_message(m.chat.id,text)

# ================= FORCE JOIN =================

@bot.message_handler(commands=["addforce"])
def addforce(m):
    if not is_admin(str(m.from_user.id)):
        return
    try:
        gid=m.text.split()[1]
        cur.execute("INSERT OR IGNORE INTO force_groups VALUES(?)",(gid,))
        conn.commit()
        bot.send_message(m.chat.id,"Force group added")
    except:
        bot.send_message(m.chat.id,"Usage: /addforce @group")

@bot.message_handler(commands=["delforce"])
def delforce(m):
    if not is_admin(str(m.from_user.id)):
        return
    try:
        gid=m.text.split()[1]
        cur.execute("DELETE FROM force_groups WHERE chat_id=?",(gid,))
        conn.commit()
        bot.send_message(m.chat.id,"Force group removed")
    except:
        bot.send_message(m.chat.id,"Usage: /delforce @group")

# ================= BROADCAST =================

@bot.message_handler(commands=["broadcast"])
def broadcast(m):
    if str(m.from_user.id)!=str(MAIN_ADMIN):
        return
    text=m.text.replace("/broadcast","").strip()
    if not text:
        bot.send_message(m.chat.id,"Usage: /broadcast message")
        return
    cur.execute("SELECT user_id FROM users")
    users=cur.fetchall()
    for u in users:
        try:
            bot.send_message(u[0],text)
        except:
            pass
    bot.send_message(m.chat.id,"Broadcast sent")

# ================= SUPPORT =================

@bot.message_handler(commands=["support"])
def support(m):
    uid=str(m.from_user.id)
    text=m.text.replace("/support","").strip()
    if not text:
        bot.send_message(m.chat.id,"Usage: /support message")
        return
    sent=bot.send_message(MAIN_ADMIN,f"Support Request\nUser: {uid}\n\n{text}\nReply to respond")
    cur.execute("INSERT OR REPLACE INTO support_map VALUES(?,?)",(str(sent.message_id),uid))
    conn.commit()
    bot.send_message(m.chat.id,"Message sent to admin")

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def reply_support(m):
    if not is_admin(str(m.from_user.id)):
        return
    reply_id=str(m.reply_to_message.message_id)
    cur.execute("SELECT user_id FROM support_map WHERE admin_msg_id=?",(reply_id,))
    row=cur.fetchone()
    if row:
        bot.send_message(row[0],f"Admin Reply:\n\n{m.text}")

# ================= RUN =================

print("Bot Running...")
bot.infinity_polling(timeout=60,long_polling_timeout=60)
