from agent.ui.telegram.client import send_message
from agent.ui.telegram.buttons import proposal_action_keyboard

def format_proposal_for_telegram(proposal) -> str:
    """
    Keep this short. Human-readable. Mobile-friendly.
    """
    return (
        f"🧠 PROPOSAL: {proposal.proposal_type}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 Topic: {proposal.topic_name}\n"
        f"🧩 Section: {proposal.schema_section}\n"
        f"📰 Source: {proposal.source}\n\n"
        f"✍️ Summary:\n{proposal.summary}"
    )

async def notify_new_proposal(proposal):
    await send_message(
        text=format_proposal_for_telegram(proposal),
        reply_markup=proposal_action_keyboard(proposal.id),
    )
