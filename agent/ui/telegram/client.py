import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

_bot = Bot(token=_TOKEN)

async def send_message(text: str, reply_markup=None):
    await _bot.send_message(
        chat_id=_CHAT_ID,
        text=text,
        reply_markup=reply_markup,
    )

async def update_buttons(message, reply_markup):
    await message.edit_reply_markup(reply_markup=reply_markup)
