import telebot
import re
import time

TOKEN = "8506015791:AAGqMPeh9fjZ7Sees4ntCUO-pxQM30hG8DA"

bot = telebot.TeleBot(TOKEN)

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
