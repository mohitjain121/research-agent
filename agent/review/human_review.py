from db.proposals import log_accepted_proposal, log_rejected_proposal


def review_proposal(proposal) -> str:
    print(proposal.summary())

    while True:
        choice = input("Please choose 1 (Approve) or 2 (Reject): ").strip()
        if choice == "1":
            return "Approve"
        if choice == "2":
            return "Reject"


def handle_proposal(proposal) -> None:
    decision = review_proposal(proposal)

    if decision == "Approve":
        proposal.apply()
        log_accepted_proposal(proposal)
    else:
        rejection_reason = input("Why are you rejecting this proposal? ").strip()
        log_rejected_proposal(proposal, rejection_reason)
