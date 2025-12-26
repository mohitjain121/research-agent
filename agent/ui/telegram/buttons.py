from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def proposal_action_keyboard(proposal_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"approve:{proposal_id}",
            ),
            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"reject:{proposal_id}",
            ),
        ]]
    )

def resolved_keyboard(status: str) -> InlineKeyboardMarkup:
    label = "☑️ Approved" if status == "approved" else "❌ Rejected"
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data="resolved")]]
    )
