import telebot
import re
import time

TOKEN = "8310389267:AAHhlEvDc5ECKNtiltVG1a_Zd1d7FVVgnj0"
ADMIN_ID = 1086634832  # <-- अपना Telegram ID डालो

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

stored_files = {}

# ---------- CLEAN CAPTION ----------
def clean_caption(text):
    if not text:
        return None
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    return text.strip()

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Bot is working ✅")

# ---------- HELP ----------
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message,
        "/add name - Add file\n"
        "/edit name - Replace file\n"
        "/delete name - Delete file\n"
    )

# ---------- ADD ----------
@bot.message_handler(commands=['add'])
def add_file(message):

    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Access denied ❌")
        return

    try:
        name = message.text.split()[1]
    except:
        bot.reply_to(message, "Usage: /add loader1")
        return

    msg = bot.reply_to(message, "Send file now")
    bot.register_next_step_handler(msg, save_file, name)

# ---------- SAVE FILE ----------
def save_file(message, name):

    if not (message.document or message.video or message.photo or message.audio):
        bot.reply_to(message, "Invalid file ❌")
        return

    stored_files[name] = message
    bot.reply_to(message, f"Saved as /{name} ✅")

# ---------- EDIT ----------
@bot.message_handler(commands=['edit'])
def edit_file(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        name = message.text.split()[1]
    except:
        return

    if name not in stored_files:
        bot.reply_to(message, "Command not found ❌")
        return

    msg = bot.reply_to(message, "Send new file to replace")
    bot.register_next_step_handler(msg, save_file, name)

# ---------- DELETE ----------
@bot.message_handler(commands=['delete'])
def delete_file(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        name = message.text.split()[1]
    except:
        return

    if name in stored_files:
        del stored_files[name]
        bot.reply_to(message, f"/{name} deleted ✅")
    else:
        bot.reply_to(message, "Not found ❌")

# ---------- SEND FILE ----------
@bot.message_handler(func=lambda message: True)
def send_file(message):

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
