from agent.db.pending import fetch_pending_proposals
from agent.review.handler import review_and_apply_proposal
from agent.proposals.factory import build_proposal_from_row


def main():
    pending = fetch_pending_proposals()

    if not pending:
        print("No pending proposals.")
        return

    for row in pending:
        proposal = build_proposal_from_row(row)
        review_and_apply_proposal(proposal, row["id"])


if __name__ == "__main__":
    main()
