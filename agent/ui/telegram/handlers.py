"""
Telegram bot handlers, notifications, and UI components.
"""
import os
import asyncio
from dotenv import load_dotenv

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from agent.db import (
    fetch_pending_proposals,
    delete_pending_proposal,
    log_accepted_proposal,
    log_rejected_proposal,
)
from agent.models import build_proposal_from_row

load_dotenv()

_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
_bot = Bot(token=_TOKEN)


# =============================================================================
# KEYBOARDS
# =============================================================================

def proposal_action_keyboard(proposal_id: str) -> InlineKeyboardMarkup:
    """Create approve/reject inline keyboard for a proposal."""
    if proposal_id is None:
        raise ValueError("proposal_id cannot be None when creating keyboard")

    proposal_id_str = str(proposal_id)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve:{proposal_id_str}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject:{proposal_id_str}"),
    ]])


def resolved_keyboard(status: str) -> InlineKeyboardMarkup:
    """Create a resolved (disabled) keyboard."""
    label = "☑️ Approved" if status == "approved" else "❌ Rejected"
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data="resolved")]])


# =============================================================================
# NOTIFICATIONS
# =============================================================================

async def send_message(text: str, reply_markup=None):
    """Send a message to the configured chat."""
    await _bot.send_message(chat_id=_CHAT_ID, text=text, reply_markup=reply_markup)


def format_proposal_for_telegram(proposal) -> str:
    return (
        "🧠 PROPOSAL\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{proposal.ui_summary()}"
    )


async def notify_new_proposal(proposal, pending_id: str):
    """Send a proposal notification with action buttons."""
    await send_message(
        text=format_proposal_for_telegram(proposal),
        reply_markup=proposal_action_keyboard(pending_id),
    )


_notification_loop = None

def send_proposal_notification(proposal, pending_id: str) -> None:
    """Send notification, handling event loop context automatically."""
    global _notification_loop

    try:
        loop = asyncio.get_running_loop()
        # Already in an async context - schedule as task
        loop.create_task(notify_new_proposal(proposal, pending_id))
        return
    except RuntimeError:
        pass

    # Not in async context - use persistent loop to avoid Windows "Event loop is closed" errors
    if _notification_loop is None or _notification_loop.is_closed():
        _notification_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_notification_loop)

    _notification_loop.run_until_complete(notify_new_proposal(proposal, pending_id))


# =============================================================================
# REVIEW LOGIC
# =============================================================================

def apply_review_decision(proposal, pending_id: str, decision: str, reason: str | None):
    """Apply an approval or rejection decision to a proposal."""
    if decision == "approve":
        proposal.apply()
        log_accepted_proposal(proposal)
    else:
        log_rejected_proposal(proposal, reason or "")

    delete_pending_proposal(pending_id)


# =============================================================================
# BUTTON & MESSAGE HANDLERS
# =============================================================================

AWAITING_REJECTION_REASON: dict[int, str] = {}


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approve/reject button clicks."""
    query = update.callback_query
    data = query.data

    print("BUTTON HANDLER HIT:", data)

    if data is None:
        await query.answer("⚠️ Invalid button data.", show_alert=True)
        return

    await query.answer()

    if data == "resolved":
        await query.answer("⚠️ This proposal has already been resolved.", show_alert=False)
        return

    try:
        action, proposal_id = data.split(":")
    except ValueError:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"⚠️ Invalid button data format: {data}",
        )
        return

    # Load pending proposal from DB
    try:
        pending_rows = fetch_pending_proposals()
    except Exception as e:
        print(f"ERROR fetching pending proposals: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"⚠️ Database error fetching proposals: {e}",
        )
        return

    pending_rows = [row for row in pending_rows if row["id"] == proposal_id]

    if not pending_rows:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⚠️ Proposal not found or already resolved.",
        )
        return

    proposal_row = pending_rows[0]

    # Rebuild proposal object
    try:
        proposal = build_proposal_from_row(proposal_row)
    except Exception as e:
        print(f"ERROR building proposal from row: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"⚠️ Error parsing proposal: {e}",
        )
        return

    # APPROVE
    if action == "approve":
        try:
            await asyncio.to_thread(
                apply_review_decision,
                proposal=proposal,
                pending_id=proposal_id,
                decision="approve",
                reason=None,
            )
        except Exception as e:
            print(f"ERROR applying approval: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"⚠️ Error applying approval: {e}",
            )
            return

        await query.edit_message_reply_markup(reply_markup=resolved_keyboard("approved"))
        await context.bot.send_message(chat_id=query.message.chat_id, text="✅ Proposal approved and applied.")
        return

    # REJECT: ask for reason
    chat_id = query.message.chat_id
    AWAITING_REJECTION_REASON[chat_id] = proposal_id

    await query.edit_message_reply_markup(reply_markup=resolved_keyboard("rejected"))
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
    """Handle rejection reason text input."""
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if chat_id not in AWAITING_REJECTION_REASON:
        return

    proposal_id = AWAITING_REJECTION_REASON.pop(chat_id)

    try:
        pending_rows = fetch_pending_proposals()
    except Exception as e:
        print(f"ERROR fetching pending proposals: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Database error fetching proposals: {e}",
        )
        return

    pending_rows = [row for row in pending_rows if row["id"] == proposal_id]
    if not pending_rows:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Proposal no longer pending.")
        return

    proposal_row = pending_rows[0]

    try:
        proposal = build_proposal_from_row(proposal_row)
    except Exception as e:
        print(f"ERROR building proposal from row: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Error parsing proposal: {e}",
        )
        return

    try:
        await asyncio.to_thread(
            apply_review_decision,
            proposal=proposal,
            pending_id=proposal_id,
            decision="reject",
            reason=text,
        )
    except Exception as e:
        print(f"ERROR applying rejection: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Error applying rejection: {e}",
        )
        return

    await context.bot.send_message(chat_id=chat_id, text="📝 Rejection reason recorded. Proposal closed.")
