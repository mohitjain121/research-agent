from telegram import Update
from telegram.ext import ContextTypes

from agent.ui.telegram.buttons import resolved_keyboard

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "resolved":
        await query.answer(
            "⚠️ This proposal has already been resolved.",
            show_alert=False,
        )
        return

    action, proposal_id = data.split(":")

    # Update buttons only (immutability)
    await query.edit_message_reply_markup(
        reply_markup=resolved_keyboard(
            "approved" if action == "approve" else "rejected"
        )
    )

    # TEMP: confirmation only (real wiring next step)
    if action == "approve":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Proposal approved.",
        )
    else:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Proposal rejected.",
        )
