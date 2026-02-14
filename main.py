
import telebot
from flask import Flask, request
import re

# 🔴 यहाँ अपना Bot Token डालो
TOKEN = "8506015791:AAEYT5RI2w21EFVCqsDXdrCy95kd2r6RhYs"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ===== TEXT CLEAN FUNCTION =====
def clean_text(text):
    if not text:
        return None

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # Remove @usernames
    text = re.sub(r'@\w+', '', text)

    return text.strip()

# ===== HANDLE FILES =====
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

# ===== WEBHOOK SYSTEM =====
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "Bot Running ✅"

if __name__ == "__main__":
    bot.remove_webhook()
    app.run(host="0.0.0.0", port=8000)
