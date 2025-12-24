from agent.config.env import supabase


def log_pending_proposal(proposal) -> None:
    payload = proposal.to_log_payload()
    supabase.table("pending_proposals").insert(payload).execute()


def fetch_pending_proposals():
    res = (
        supabase
        .table("pending_proposals")
        .select("*")
        .order("created_at")
        .execute()
    )
    return res.data or []


def delete_pending_proposal(pending_id: str) -> None:
    supabase.table("pending_proposals").delete().eq("id", pending_id).execute()
