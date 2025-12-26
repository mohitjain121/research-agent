from telegram import Update
from telegram.ext import ContextTypes

from agent.ui.telegram.buttons import resolved_keyboard

from agent.db.pending import fetch_pending_proposals
from agent.proposals.factory import build_proposal_from_row
from agent.review.handler import review_and_apply_proposal


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # Inert clicks on resolved proposals
    if data == "resolved":
        await query.answer(
            "⚠️ This proposal has already been resolved.",
            show_alert=False,
        )
        return

    action, proposal_id = data.split(":")

    # 1️⃣ Load pending proposal from DB
    pending_rows = fetch_pending_proposals(proposal_id=proposal_id)

    if not pending_rows:
        await query.answer(
            "⚠️ Proposal not found or already resolved.",
            show_alert=True,
        )
        return

    proposal_row = pending_rows[0]

    # 2️⃣ Rebuild proposal object (domain logic)
    proposal = build_proposal_from_row(proposal_row)

    # 3️⃣ Apply decision using existing review handler
    decision = "approve" if action == "approve" else "reject"

    review_and_apply_proposal(
        proposal=proposal,
        decision=decision,
        rejection_reason=None,  # added later
    )

    # 4️⃣ Update buttons only (keep proposal text immutable)
    await query.edit_message_reply_markup(
        reply_markup=resolved_keyboard(
            "approved" if decision == "approve" else "rejected"
        )
    )

    # 5️⃣ Send confirmation message
    if decision == "approve":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Proposal approved and applied.",
        )
    else:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Proposal rejected.",
        )
