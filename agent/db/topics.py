from typing import List, Dict
from agent.config.env import supabase


def fetch_topics_by_vertical(vertical: str) -> List[Dict]:
    response = (
        supabase
        .table("topics")
        .select("id, name")
        .eq("vertical", vertical)
        .execute()
    )

    if response.data is None:
        return []

    return response.data


def create_topic(topic_id: str, topic_name: str, vertical: str) -> str:
    supabase.table("topics").insert({
        "id": topic_id,
        "name": topic_name,
        "vertical": vertical
    }).execute()

    from agent.db.topic_memory import initialize_topic_memory
    initialize_topic_memory(topic_id)

    return topic_id
