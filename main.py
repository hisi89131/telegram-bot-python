import telebot
from telebot import types
import sqlite3
import re
from datetime import datetime
import pytz

BOT_TOKEN = "8232988598:AAF1WVLtrRLWyaJrRfD2hpQjtwAAkbaN720"
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

def joined(uid):
    groups=[MAIN_CHANNEL]
    cur.execute("SELECT chat_id FROM force_groups")
    groups+=[g[0] for g in cur.fetchall()]
    for g in groups:
        try:
            st=bot.get_chat_member(g,int(uid)).status
            if st not in ["member","administrator","creator"]:
                return False
        except:
            return False
    return True

def join_markup():
    mk=types.InlineKeyboardMarkup()
    groups=[MAIN_CHANNEL]
    cur.execute("SELECT chat_id FROM force_groups")
    groups+=[g[0] for g in cur.fetchall()]
    for g in groups:
        link=f"https://t.me/{g.replace('@','')}"
        mk.add(types.InlineKeyboardButton("Join Group",url=link))
    mk.add(types.InlineKeyboardButton("Verify ✅",callback_data="verify"))
    return mk

# ================= START =================

@bot.message_handler(commands=["start"])
def start(m):
    uid=str(m.from_user.id)
    if is_banned(uid):
        return
    cur.execute("INSERT OR IGNORE INTO users VALUES(?,?)",(uid,m.from_user.username))
    conn.commit()
    if not joined(uid):
        bot.send_message(m.chat.id,"Join required groups",reply_markup=join_markup())
        return
    bot.send_message(m.chat.id,"Verified ✅\nUse /cmd")

@bot.callback_query_handler(func=lambda c:c.data=="verify")
def verify(c):
    if joined(str(c.from_user.id)):
        bot.edit_message_text("Verified ✅\nUse /cmd",c.message.chat.id,c.message.message_id)
    else:
        bot.answer_callback_query(c.id,"Join all groups")

# ================= CMD PANEL =================

@bot.message_handler(commands=["cmd"])
def panel(m):
    uid=str(m.from_user.id)
    if is_banned(uid):
        return

    if is_admin(uid):
        text="👑 Admin Panel\n\n"
        text+="/set name\n/done\n/edit name\n/deletecmd name\n"
        text+="/ban id\n/unban id\n/banlist\n/userlist\n"
        text+="/addadmin id\n/removeadmin id\n/adminlist\n"
        text+="/addforce @group\n/delforce @group\n"
        if uid==str(MAIN_ADMIN):
            text+="/broadcast message\n"
        text+="/support message\n\n"

        # show commands visible to admin
        if uid==str(MAIN_ADMIN):
            cur.execute("SELECT name FROM commands")
        else:
            cur.execute("SELECT name FROM commands WHERE owner=?",(uid,))
        cmds=cur.fetchall()
        text+="📦 Your Commands:\n"
        for c in cmds:
            text+=f"/{c[0]}\n"

        bot.send_message(m.chat.id,text)
    else:
        if not joined(uid):
            bot.send_message(m.chat.id,"Join required groups",reply_markup=join_markup())
            return
        cur.execute("SELECT name FROM commands")
        cmds=cur.fetchall()
        text="📦 Available Commands:\n\n"
        for c in cmds:
            text+=f"/{c[0]}\n"
        text+="\n/support message\n/cmd"
        bot.send_message(m.chat.id,text)

# ================= SET =================

current_set={}

@bot.message_handler(commands=["set"])
def set_cmd(m):
    uid=str(m.from_user.id)
    if not is_admin(uid):
        return
    try:
        name=m.text.split()[1]
        current_set[uid]=name
        cur.execute("INSERT OR REPLACE INTO commands VALUES(?,?,?)",(name,uid,""))
        cur.execute("DELETE FROM files WHERE command_name=?",(name,))
        conn.commit()
        bot.send_message(m.chat.id,"Send files then /done")
    except:
        bot.send_message(m.chat.id,"Usage: /set name")

@bot.message_handler(content_types=["document","photo","video","audio"])
def save_file(m):
    uid=str(m.from_user.id)
    if uid not in current_set:
        return
    cmd=current_set[uid]

    if m.document:
        fid=m.document.file_id
        ftype="document"
    elif m.photo:
        fid=m.photo[-1].file_id
        ftype="photo"
    elif m.video:
        fid=m.video.file_id
        ftype="video"
    elif m.audio:
        fid=m.audio.file_id
        ftype="audio"
    else:
        return

    cap=clean(m.caption)

    cur.execute("INSERT INTO files(command_name,file_id,file_type,caption) VALUES(?,?,?,?)",
                (cmd,fid,ftype,cap))
    conn.commit()

@bot.message_handler(commands=["done"])
def done(m):
    uid=str(m.from_user.id)
    if uid not in current_set:
        return
    cmd=current_set[uid]
    cur.execute("UPDATE commands SET upload_time=? WHERE name=?",(ist(),cmd))
    conn.commit()
    del current_set[uid]
    bot.send_message(m.chat.id,"Saved & Updated")

# ================= EDIT =================

@bot.message_handler(commands=["edit"])
def edit(m):
    uid=str(m.from_user.id)
    if not is_admin(uid):
        return
    try:
        name=m.text.split()[1]
        current_set[uid]=name
        cur.execute("DELETE FROM files WHERE command_name=?",(name,))
        conn.commit()
        bot.send_message(m.chat.id,"Send new files then /done")
    except:
        bot.send_message(m.chat.id,"Usage: /edit name")

@bot.message_handler(commands=["deletecmd"])
def delete(m):
    uid=str(m.from_user.id)
    if not is_admin(uid):
        return
    try:
        name=m.text.split()[1]
        cur.execute("DELETE FROM commands WHERE name=?",(name,))
        cur.execute("DELETE FROM files WHERE command_name=?",(name,))
        conn.commit()
        bot.send_message(m.chat.id,"Command deleted")
    except:
        bot.send_message(m.chat.id,"Usage: /deletecmd name")

# ================= DYNAMIC =================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
def dynamic(m):
    uid=str(m.from_user.id)
    cmd=m.text[1:]

    builtins=["start","cmd","set","done","edit","deletecmd","ban","unban","banlist","userlist",
              "addadmin","removeadmin","adminlist","addforce","delforce","broadcast","support"]

    if cmd in builtins:
        return

    if not joined(uid):
        bot.send_message(m.chat.id,"Join required groups",reply_markup=join_markup())
        return

    cur.execute("SELECT upload_time FROM commands WHERE name=?",(cmd,))
    row=cur.fetchone()
    if not row:
        return

    cur.execute("SELECT file_id,file_type,caption FROM files WHERE command_name=?",(cmd,))
    files=cur.fetchall()

    for f in files:
        if f[1]=="document":
            bot.send_document(m.chat.id,f[0],caption=f[2])
        elif f[1]=="photo":
            bot.send_photo(m.chat.id,f[0],caption=f[2])
        elif f[1]=="video":
            bot.send_video(m.chat.id,f[0],caption=f[2])
        elif f[1]=="audio":
            bot.send_audio(m.chat.id,f[0],caption=f[2])

    bot.send_message(m.chat.id,f"Uploaded: {row[0]}")

# ================= RUN =================

print("Bot Running...")
bot.infinity_polling(timeout=60,long_polling_timeout=60)
