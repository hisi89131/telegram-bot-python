import telebot
import re
import time

TOKEN = "8310389267:AAHhlEvDc5ECKNtiltVG1a_Zd1d7FVVgnj0"
ADMIN_ID = 1086634832  # <-- अपना Telegram user id डालना

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# ---------- TEXT CLEAN FUNCTION ----------
def clean_text(text):
    if not text:
        return None
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    return text.strip()

# ---------- START COMMAND ----------
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Bot is working ✅")

# ---------- HELP COMMAND ----------
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message,
        "/start - Check bot status\n"
        "/help - Show commands\n"
    )

# ---------- FILE HANDLER ----------
@bot.message_handler(content_types=[
    'document', 'video', 'photo',
    'audio', 'voice', 'animation'
])
def handle_files(message):

    cleaned_caption = clean_text(message.caption)

    bot.copy_message(
        chat_id=message.chat.id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        caption=cleaned_caption
    )

print("Bot is running...")

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
