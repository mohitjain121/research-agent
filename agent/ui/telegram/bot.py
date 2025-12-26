import os
from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CallbackQueryHandler,
)

from agent.ui.telegram.handlers import handle_button

from telegram.ext import MessageHandler, filters
from agent.ui.telegram.handlers import handle_rejection_reason


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rejection_reason))


    app.run_polling()
