from agent.config.env import supabase


def log_accepted_proposal(proposal) -> None:
    payload = proposal.to_log_payload()
    supabase.table("accepted_proposals").insert(payload).execute()


def log_rejected_proposal(proposal, rejection_reason: str) -> None:
    payload = proposal.to_log_payload()
    payload["proposed_belief"] = payload.pop("new_belief", None)
    payload["rejection_reason"] = rejection_reason
    supabase.table("rejected_proposals").insert(payload).execute()
