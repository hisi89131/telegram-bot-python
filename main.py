import re
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 1086634832
TARGET_CHAT_ID = -1003714828296

YOUR_USERNAME1 = "@Loader0wner"
YOUR_USERNAME2 = "@Loader1king"

DELETE_AFTER_HOURS = 12
# ==========================================

user_data_store = []
sent_messages = []


def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID


def clean_text(text):
    if not text:
        return text

    has_link = re.search(r'https?://\S+|www\.\S+', text)
    has_username = re.search(r'@\w+', text)

    if not has_link and not has_username:
        return text

    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    text = re.sub(r'@\w+', '', text)

    text = text.strip()
    text += f"\n\n{YOUR_USERNAME1}\n{YOUR_USERNAME2}"

    return text.strip()


async def collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if update.message:
        user_data_store.append(update.message)


async def done_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_data_store

    if not is_owner(update):
        return

    if not user_data_store:
        await update.message.reply_text("❌ कोई data नहीं है")
        return

    for msg in user_data_store:

        cleaned_caption = clean_text(msg.caption) if msg.caption else None
        cleaned_text = clean_text(msg.text) if msg.text else None

        if cleaned_text:
            sent = await context.bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=cleaned_text
            )
            sent_messages.append((sent.chat_id, sent.message_id))

        elif msg.photo:
            sent = await context.bot.send_photo(
                chat_id=TARGET_CHAT_ID,
                photo=msg.photo[-1].file_id,
                caption=cleaned_caption
            )
            sent_messages.append((sent.chat_id, sent.message_id))

        elif msg.video:
            sent = await context.bot.send_video(
                chat_id=TARGET_CHAT_ID,
                video=msg.video.file_id,
                caption=cleaned_caption
            )
            sent_messages.append((sent.chat_id, sent.message_id))

        elif msg.document:
            sent = await context.bot.send_document(
                chat_id=TARGET_CHAT_ID,
                document=msg.document.file_id,
                caption=cleaned_caption
            )
            sent_messages.append((sent.chat_id, sent.message_id))

        elif msg.audio:
            sent = await context.bot.send_audio(
                chat_id=TARGET_CHAT_ID,
                audio=msg.audio.file_id,
                caption=cleaned_caption
            )
            sent_messages.append((sent.chat_id, sent.message_id))

    user_data_store = []
    await update.message.reply_text("🚀 Forward Complete!")

    asyncio.create_task(auto_delete())


async def auto_delete():
    await asyncio.sleep(DELETE_AFTER_HOURS * 3600)

    for chat_id, message_id in sent_messages:
        try:
            await app.bot.delete_message(chat_id, message_id)
        except:
            pass

    sent_messages.clear()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_owner(update):
        await update.message.reply_text("🔥 Bot Active & Secure")


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("done", done_forward))
app.add_handler(MessageHandler(filters.ALL, collect_data))

print("Bot Running...")
app.run_polling()
