import telebot
import re
import time

TOKEN = "8310389267:AAFhrYCABb2u6iVWY2GzyzYk6rv8JmRyTa4"
bot = telebot.TeleBot(TOKEN)

bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Bot is working ✅")

def clean_text(text):
    if not text:
        return None
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    return text.strip()

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
