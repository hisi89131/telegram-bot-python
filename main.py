import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "8232988598:AAGDs4P58C4lmo9nyOi_TJoAYJdjsnqRmTQ"
MAIN_ADMIN = 1086634832
MAIN_FORCE_CHANNEL = "@loader0fficial"

logging.basicConfig(level=logging.INFO)

users = {}
banned_users = set()
admins = set()
admin_banlist = set()
custom_commands = {}
force_channels = {MAIN_FORCE_CHANNEL}


# ---------------- FORCE JOIN CHECK ---------------- #

async def is_joined(user_id, context):
    for channel in force_channels:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


async def force_join_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = []
    for ch in force_channels:
        buttons.append([InlineKeyboardButton("Join Channel", url=f"https://t.me/{ch.replace('@','')}")])
    buttons.append([InlineKeyboardButton("Verify", callback_data="verify")])
    reply = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("पहले सभी चैनल जॉइन करो और Verify करो.", reply_markup=reply)


async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if await is_joined(user_id, context):
        await query.answer("Verified ✅", show_alert=True)
        await query.message.edit_text("अब आप /cmd से कमांड देख सकते हो.")
    else:
        await query.answer("पहले जॉइन करो ❌", show_alert=True)


# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in banned_users:
        return

    if not await is_joined(user_id, context):
        await force_join_message(update, context)
        return

    users[user_id] = update.effective_user.username
    await update.message.reply_text("Welcome! Use /cmd")


# ---------------- CMD ---------------- #

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_joined(user_id, context):
        await force_join_message(update, context)
        return

    text = "Available Commands:\n"
    for cmd_name in custom_commands:
        if custom_commands[cmd_name]["owner"] == user_id or user_id == MAIN_ADMIN:
            text += f"/{cmd_name}\n"

    text += "\n/support"
    await update.message.reply_text(text)


# ---------------- SUPPORT ---------------- #

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("अपना मैसेज भेजो।")
    context.user_data["support"] = True


async def support_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("support"):
        await context.bot.send_message(MAIN_ADMIN, f"Support from {update.effective_user.id}:\n{update.message.text}")
        await update.message.reply_text("Support Sent ✅")
        context.user_data["support"] = False


# ---------------- ADMIN ---------------- #

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN:
        return
    user_id = int(context.args[0])
    admins.add(user_id)
    await update.message.reply_text("Admin Added")


async def removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN:
        return
    user_id = int(context.args[0])
    admins.discard(user_id)
    await update.message.reply_text("Admin Removed")


async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Admins:\n"
    for a in admins:
        text += f"{a}\n"
    await update.message.reply_text(text)


# ---------------- USER BAN ---------------- #

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN:
        return
    user_id = int(context.args[0])
    banned_users.add(user_id)
    await update.message.reply_text("User Banned")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MAIN_ADMIN:
        return
    user_id = int(context.args[0])
    banned_users.discard(user_id)
    await update.message.reply_text("User Unbanned")


async def banlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Banned Users:\n"
    for u in banned_users:
        text += f"{u}\n"
    await update.message.reply_text(text)


# ---------------- CUSTOM COMMAND CREATE ---------------- #

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != MAIN_ADMIN and user_id not in admins:
        return

    cmd_name = context.args[0]
    custom_commands[cmd_name] = {
        "owner": user_id,
        "content": [],
        "created": datetime.now(),
    }

    context.user_data["creating"] = cmd_name
    await update.message.reply_text("अब फाइल/मैसेज भेजो, फिर /done")


async def save_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd_name = context.user_data.get("creating")
    if cmd_name:
        custom_commands[cmd_name]["content"].append(update.message.text)
        await update.message.reply_text("Saved")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd_name = context.user_data.get("creating")
    if not cmd_name:
        return
    custom_commands[cmd_name]["created"] = datetime.now()
    context.user_data["creating"] = None

    for u in users:
        try:
            await context.bot.send_message(u, "New Command Added! Check /cmd")
        except:
            pass

    await update.message.reply_text("Command Saved ✅")


# ---------------- EXECUTE CUSTOM ---------------- #

async def execute_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd_name = update.message.text.replace("/", "")
    if cmd_name in custom_commands:
        data = custom_commands[cmd_name]
        if datetime.now() > data["created"] + timedelta(hours=24):
            del custom_commands[cmd_name]
            await update.message.reply_text("Command Expired ❌")
            return

        for msg in data["content"]:
            await update.message.reply_text(msg)

        await update.message.reply_text(f"Uploaded Time: {data['created']}")


# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cmd", cmd))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("removeadmin", removeadmin))
    app.add_handler(CommandHandler("adminlist", adminlist))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("banlist", banlist))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("done", done))

    app.add_handler(CallbackQueryHandler(verify_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_content))
    app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, execute_custom))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, support_forward))

    app.run_polling()


if __name__ == "__main__":
    main()
