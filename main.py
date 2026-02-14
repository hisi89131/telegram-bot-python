import telebot
from telebot import types
import sqlite3
from datetime import datetime
import pytz

# ================= CONFIG =================

BOT_TOKEN = "8531299371:AAH1TYjwf2DZhjam62fBo2XsIpcCmztDKIw"
MAIN_ADMIN = 1086634832
MAIN_CHANNEL = "@loader0fficial"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ================= DATABASE =================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS admins (user_id TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS banned (user_id TEXT PRIMARY KEY)")
cur.execute("""CREATE TABLE IF NOT EXISTS commands (
    name TEXT PRIMARY KEY,
    upload_time TEXT,
    owner_id TEXT
)""")

conn.commit()
cur.execute("INSERT OR IGNORE INTO admins VALUES(?)", (str(MAIN_ADMIN),))
conn.commit()

# ================= UTIL =================

def ist_time():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%d-%m-%Y %H:%M")

def is_admin(uid):
    cur.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def is_main(uid):
    return str(uid) == str(MAIN_ADMIN)

# ================= CMD PANEL =================

@bot.message_handler(commands=["cmd"])
def cmd_panel(message):
    uid = str(message.from_user.id)

    if not is_admin(uid):
        bot.send_message(message.chat.id,"Only Admin Access")
        return

    if is_main(uid):
        cur.execute("SELECT name FROM commands")
        cmds = cur.fetchall()
        text="👑 MAIN ADMIN PANEL\n\nCommands:\n"
        for c in cmds:
            text+=f"/{c[0]}\n"

        text+="\n/addadmin\n/removeadmin\n/adminlist\n/broadcast\n"
    else:
        cur.execute("SELECT name FROM commands WHERE owner_id=?",(uid,))
        cmds = cur.fetchall()
        text="🛡 YOUR COMMANDS:\n\n"
        for c in cmds:
            text+=f"/{c[0]}\n"

    bot.send_message(message.chat.id,text)

# ================= SET COMMAND =================

@bot.message_handler(commands=["set"])
def set_cmd(message):
    uid=str(message.from_user.id)
    if not is_admin(uid):
        return
    try:
        name=message.text.split()[1]
        cur.execute("INSERT OR REPLACE INTO commands VALUES(?,?,?)",
                    (name,"",uid))
        conn.commit()
        bot.send_message(message.chat.id,"Command Created")
    except:
        bot.send_message(message.chat.id,"Usage: /set name")

# ================= DELETE COMMAND =================

@bot.message_handler(commands=["deletecmd"])
def delete_cmd(message):
    uid=str(message.from_user.id)
    if not is_admin(uid):
        return
    try:
        name=message.text.split()[1]
        cur.execute("SELECT owner_id FROM commands WHERE name=?",(name,))
        row=cur.fetchone()
        if not row:
            return

        if is_main(uid) or row[0]==uid:
            cur.execute("DELETE FROM commands WHERE name=?",(name,))
            conn.commit()
            bot.send_message(message.chat.id,"Deleted")
        else:
            bot.send_message(message.chat.id,"No Permission")
    except:
        bot.send_message(message.chat.id,"Usage: /deletecmd name")

# ================= ADMIN MANAGEMENT =================

@bot.message_handler(commands=["addadmin"])
def addadmin(message):
    if not is_main(message.from_user.id):
        return
    try:
        uid=message.text.split()[1]
        cur.execute("INSERT OR IGNORE INTO admins VALUES(?)",(uid,))
        conn.commit()
        bot.send_message(message.chat.id,"Admin Added")
    except:
        bot.send_message(message.chat.id,"Usage: /addadmin id")

@bot.message_handler(commands=["removeadmin"])
def removeadmin(message):
    if not is_main(message.from_user.id):
        return
    try:
        uid=message.text.split()[1]
        cur.execute("DELETE FROM admins WHERE user_id=?",(uid,))
        conn.commit()
        bot.send_message(message.chat.id,"Admin Removed")
    except:
        bot.send_message(message.chat.id,"Usage: /removeadmin id")

@bot.message_handler(commands=["adminlist"])
def adminlist(message):
    if not is_admin(str(message.from_user.id)):
        return
    cur.execute("SELECT user_id FROM admins")
    data=cur.fetchall()
    text="Admins:\n\n"
    for a in data:
        text+=f"{a[0]}\n"
    bot.send_message(message.chat.id,text)

# ================= BROADCAST =================

@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if not is_main(message.from_user.id):
        return
    text=message.text.replace("/broadcast","").strip()
    if not text:
        return
    cur.execute("SELECT user_id FROM users")
    users=cur.fetchall()
    for u in users:
        try:
            bot.send_message(u[0],text)
        except:
            pass
    bot.send_message(message.chat.id,"Broadcast Done")

# ================= RUN =================

print("Bot Running...")
bot.infinity_polling()
