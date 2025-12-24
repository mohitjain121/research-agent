from agent.config.env import supabase


def has_seen_source(source_link: str) -> bool:
    """
    Returns True if this source_link has already been processed
    (accepted or rejected).
    """

    accepted = (
        supabase
        .table("accepted_proposals")
        .select("id")
        .eq("source_link", source_link)
        .limit(1)
        .execute()
    )

    if accepted.data:
        return True

    rejected = (
        supabase
        .table("rejected_proposals")
        .select("id")
        .eq("source_link", source_link)
        .limit(1)
        .execute()
    )

    return bool(rejected.data)
