import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json
import os

BOT_TOKEN = "7291725381:AAG7moo_kksmEHnDRrmm3kyH2hDZCrD1-YQ"
ADMIN_GROUP_ID = -1002775981240

USERS_FILE = "users.json"
BANNED_USERS_FILE = "banned_users.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

for file in [USERS_FILE, BANNED_USERS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump([], f)

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def add_user(user_id):
    users = load_json(USERS_FILE)
    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, users)

def is_banned(user_id):
    banned = load_json(BANNED_USERS_FILE)
    return user_id in banned

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_banned(user_id):
        return
    add_user(user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="👋 Welcome! Send me any message.")

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if is_banned(user_id):
        return

    add_user(user_id)
    msg = update.message
    forwarded = await msg.forward(chat_id=ADMIN_GROUP_ID)
    caption = "🆕 Message from @0 (1)".format(user.username or "NoUsername", user_id)
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=caption, reply_to_message_id=forwarded.message_id)

async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    text = update.message.text
    reply_msg = update.message.reply_to_message

    previous_text = reply_msg.text or ""
    if "(" in previous_text and ")" in previous_text:
        target_user_id = previous_text.split("(")[-1].split(")")[0]
        try:
            target_user_id = int(target_user_id)
            await context.bot.send_message(chat_id=target_user_id, text=text)
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text="✅ Replied to user.")
        except Exception as e:
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text="❌ Failed to send reply.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        target = int(context.args[0])
        banned = load_json(BANNED_USERS_FILE)
        if target not in banned:
            banned.append(target)
            save_json(BANNED_USERS_FILE, banned)
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text="🚫 User {} banned.".format(target))
        else:
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text="User already banned.")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        target = int(context.args[0])
        banned = load_json(BANNED_USERS_FILE)
        if target in banned:
            banned.remove(target)
            save_json(BANNED_USERS_FILE, banned)
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text="✅ User {} unbanned.".format(target))
        else:
            await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text="User not banned.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_json(USERS_FILE)
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text="📊 Total users: {}".format(len(users)))

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), forward_to_admin))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, reply_handler))
    app.run_polling()
