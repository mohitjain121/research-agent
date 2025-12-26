from telegram import Update
from telegram.ext import ContextTypes

from agent.ui.telegram.buttons import resolved_keyboard

from agent.db.pending import fetch_pending_proposals
from agent.proposals.factory import build_proposal_from_row
from agent.review.handler import review_and_apply_proposal

# chat_id -> proposal_id awaiting rejection reason
AWAITING_REJECTION_REASON: dict[int, str] = {}

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

    # APPROVE: immediate
    if action == "approve":
        review_and_apply_proposal(
            proposal=proposal,
            decision="approve",
            rejection_reason=None,
        )

        await query.edit_message_reply_markup(
            reply_markup=resolved_keyboard("approved")
        )

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Proposal approved and applied.",
        )
        return


    # REJECT: ask for reason
    chat_id = query.message.chat_id
    AWAITING_REJECTION_REASON[chat_id] = proposal_id

    await query.edit_message_reply_markup(
        reply_markup=resolved_keyboard("rejected")
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "❌ Proposal rejected.\n\n"
            "Please reply with a short reason.\n\n"
            "Examples:\n"
            "- wrong schema section\n"
            "- weak source\n"
            "- already known\n"
            "- speculative"
        ),
    )


async def handle_rejection_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if chat_id not in AWAITING_REJECTION_REASON:
        return  # normal message, ignore

    proposal_id = AWAITING_REJECTION_REASON.pop(chat_id)

    pending_rows = fetch_pending_proposals(proposal_id=proposal_id)
    if not pending_rows:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Proposal no longer pending.",
        )
        return

    proposal_row = pending_rows[0]
    proposal = build_proposal_from_row(proposal_row)

    review_and_apply_proposal(
        proposal=proposal,
        decision="reject",
        rejection_reason=text,
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text="📝 Rejection reason recorded. Proposal closed.",
    )
