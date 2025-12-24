from agent.config.env import supabase


def log_accepted_proposal(proposal) -> None:
    payload = proposal.to_log_payload()
    supabase.table("accepted_proposals").insert(payload).execute()


def log_rejected_proposal(proposal, rejection_reason: str) -> None:
    base_payload = proposal.to_log_payload()

    # Normalize for rejected_proposals schema
    payload = {
        "proposal_type": base_payload.get("proposal_type"),
        "topic_id": base_payload.get("topic_id"),
        "schema_section": base_payload.get("schema_section"),
        "proposed_belief": base_payload.get("new_belief"),
        "why_this_matters": base_payload.get("why_this_matters"),
        "source_link": base_payload.get("source_link"),
        "rejection_reason": rejection_reason,
    }

    # Remove None values (important)
    payload = {k: v for k, v in payload.items() if v is not None}

    supabase.table("rejected_proposals").insert(payload).execute()
