"""
Telegram bot entry point.
"""
import os
from dotenv import load_dotenv
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters

from agent.ui.telegram.handlers import handle_button, handle_rejection_reason

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def run_bot():
    """Start the Telegram bot polling loop."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rejection_reason))

    app.run_polling()
