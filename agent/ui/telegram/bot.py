import os
from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from agent.ui.telegram.handlers import handle_button
from agent.ui.telegram.client import send_message
from agent.ui.telegram.buttons import proposal_action_keyboard

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Temporary test command
async def start(update, context):
    await send_message(
        text="🧠 Telegram UI wired successfully.",
        reply_markup=proposal_action_keyboard("test_proposal"),
    )

def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))

    app.run_polling()
