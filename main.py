import telebot
import time
import re
from datetime import datetime

TOKEN = "8310389267:AAF1ssKWRGuJECXG9FPvhpvyI8RC1kkFDbQ"
ADMIN_IDS = [1086634832]
FORCE_GROUP = "@loader0fficial"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# Storage
commands_data = {}
user_upload_mode = {}
admins = set(ADMIN_IDS)


# ---------------- FORCE JOIN CHECK ----------------
def is_joined(user_id):
    try:
        member = bot.get_chat_member(FORCE_GROUP, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


def force_join_message(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("Join Group", url=f"https://t.me/{FORCE_GROUP.replace('@','')}"),
    )
    markup.add(
        telebot.types.InlineKeyboardButton("Verify", callback_data="verify_join")
    )
    bot.send_message(message.chat.id, "Join group to use bot.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    if is_joined(call.from_user.id):
        bot.answer_callback_query(call.id, "Verified ✅")
        bot.send_message(call.message.chat.id, "Access granted.")
    else:
        bot.answer_callback_query(call.id, "Still not joined ❌")


# ---------------- ADMIN CHECK ----------------
def is_admin(user_id):
    return user_id in admins


# ---------------- START ----------------
@bot.message_handler(commands=["start"])
def start_cmd(message):
    if not is_joined(message.from_user.id):
        return force_join_message(message)
    bot.reply_to(message, "Bot is working ✅")


# ---------------- HELP ----------------
@bot.message_handler(commands=["help"])
def help_cmd(message):
    if not is_joined(message.from_user.id):
        return force_join_message(message)

    text = """
Available Commands:

/add name → Start new loader
/done → Finish upload
/delete name → Delete loader
/edit name → Edit loader
/addadmin id → Add admin
/removeadmin id → Remove admin
/help → Show commands
"""
    bot.send_message(message.chat.id, text)


# ---------------- ADD LOADER ----------------
@bot.message_handler(commands=["add"])
def add_loader(message):
    if not is_admin(message.from_user.id):
        return
    try:
        name = message.text.split()[1].lower()
        user_upload_mode[message.from_user.id] = name
        commands_data[name] = []
        bot.reply_to(message, f"Send files for {name}. Use /done when finished.")
    except:
        bot.reply_to(message, "Usage: /add loadername")


# ---------------- DONE ----------------
@bot.message_handler(commands=["done"])
def done_upload(message):
    if not is_admin(message.from_user.id):
        return
    if message.from_user.id in user_upload_mode:
        name = user_upload_mode.pop(message.from_user.id)
        bot.reply_to(message, f"{name} saved successfully ✅")


# ---------------- DELETE LOADER ----------------
@bot.message_handler(commands=["delete"])
def delete_loader(message):
    if not is_admin(message.from_user.id):
        return
    try:
        name = message.text.split()[1].lower()
        if name in commands_data:
            del commands_data[name]
            bot.reply_to(message, "Deleted successfully.")
        else:
            bot.reply_to(message, "Loader not found.")
    except:
        bot.reply_to(message, "Usage: /delete loadername")


# ---------------- EDIT LOADER ----------------
@bot.message_handler(commands=["edit"])
def edit_loader(message):
    if not is_admin(message.from_user.id):
        return
    try:
        name = message.text.split()[1].lower()
        if name in commands_data:
            user_upload_mode[message.from_user.id] = name
            commands_data[name] = []
            bot.reply_to(message, f"Editing {name}. Send new files then /done")
        else:
            bot.reply_to(message, "Loader not found.")
    except:
        bot.reply_to(message, "Usage: /edit loadername")


# ---------------- ADD ADMIN ----------------
@bot.message_handler(commands=["addadmin"])
def add_admin(message):
    if not is_admin(message.from_user.id):
        return
    try:
        new_admin = int(message.text.split()[1])
        admins.add(new_admin)
        bot.reply_to(message, "Admin added.")
    except:
        bot.reply_to(message, "Usage: /addadmin userid")


# ---------------- REMOVE ADMIN ----------------
@bot.message_handler(commands=["removeadmin"])
def remove_admin(message):
    if not is_admin(message.from_user.id):
        return
    try:
        remove_id = int(message.text.split()[1])
        admins.discard(remove_id)
        bot.reply_to(message, "Admin removed.")
    except:
        bot.reply_to(message, "Usage: /removeadmin userid")


# ---------------- HANDLE FILES ----------------
@bot.message_handler(content_types=["document", "video", "photo", "audio", "voice", "animation"])
def handle_files(message):
    if message.from_user.id in user_upload_mode:
        name = user_upload_mode[message.from_user.id]
        upload_time = datetime.now().strftime("%d %b %Y | %I:%M %p")
        commands_data[name].append({
            "message_id": message.message_id,
            "chat_id": message.chat.id,
            "time": upload_time
        })


# ---------------- USER COMMAND FETCH ----------------
@bot.message_handler(func=lambda message: True)
def user_commands(message):
    if not is_joined(message.from_user.id):
        return force_join_message(message)

    cmd = message.text.lower().strip()
    if cmd in commands_data:
        files = commands_data[cmd]
        for file in files:
            bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=file["chat_id"],
                message_id=file["message_id"]
            )
            bot.send_message(message.chat.id, f"🕒 Uploaded: {file['time']}")


print("Bot running...")
bot.infinity_polling()
    text = message.text.replace("/", "")

    if text in stored_files:

        file_msg = stored_files[text]

        caption = clean_caption(file_msg.caption)

        bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=file_msg.chat.id,
            message_id=file_msg.message_id,
            caption=caption
        )

print("Bot running...")

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
