from agent.db.proposals import (
    log_accepted_proposal,
    log_rejected_proposal,
)
from agent.db.pending import delete_pending_proposal


def review_and_apply_proposal(proposal, pending_id: str) -> None:
    print(proposal.summary())

    while True:
        choice = input("Choose 1 (Approve) or 2 (Reject): ").strip()
        if choice in ("1", "2"):
            break

    if choice == "1":
        proposal.apply()
        log_accepted_proposal(proposal)
    else:
        reason = input("Why are you rejecting this proposal? ").strip()
        log_rejected_proposal(proposal, reason)

    delete_pending_proposal(pending_id)

def apply_review_decision(proposal, pending_id: str, decision: str, reason: str | None):
    if decision == "approve":
        proposal.apply()
        log_accepted_proposal(proposal)
    else:
        log_rejected_proposal(proposal, reason or "")

    delete_pending_proposal(pending_id)
