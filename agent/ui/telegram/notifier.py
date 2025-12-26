from agent.ui.telegram.client import send_message
from agent.ui.telegram.buttons import proposal_action_keyboard

def format_proposal_for_telegram(proposal) -> str:
    text = (
        proposal.ui_summary()
        if hasattr(proposal, "ui_summary")
        else proposal.summary()
    )

    return (
        "🧠 PROPOSAL\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{text}"
    )


async def notify_new_proposal(proposal, pending_id: str):
    await send_message(
        text=format_proposal_for_telegram(proposal),
        reply_markup=proposal_action_keyboard(pending_id),
    )

