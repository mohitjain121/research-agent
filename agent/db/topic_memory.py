from typing import Optional, List
from datetime import datetime, timezone

from agent.config.env import supabase
from agent.models.memory import TopicMemory
from agent.models.proposals import MemoryUpdateProposal


SECTION_TO_COLUMN = {
    "predecessors_limitations": "predecessors_limitations",
    "core_proposal": "core_proposal",
    "enabling_conditions": "enabling_conditions",
    "problems_solved": "problems_solved",
    "operational_understanding": "operational_understanding",
}


def load_topic_memory(topic_id: str) -> Optional[TopicMemory]:
    response = (
        supabase
        .table("topic_memory")
        .select("*")
        .eq("topic_id", topic_id)
        .maybe_single()
        .execute()
    )

    if response is None or response.data is None:
        return None

    data = response.data

    return TopicMemory(
        topic_id=data["topic_id"],
        topic_name=None,
        predecessors_limitations=data["predecessors_limitations"],
        core_proposal=data["core_proposal"],
        enabling_conditions=data["enabling_conditions"],
        problems_solved=data["problems_solved"],
        operational_understanding=data["operational_understanding"],
        progress_history=data.get("progress_history") or [],
        last_updated_ts=data.get("last_updated_ts"),
    )


def initialize_topic_memory(topic_id: str) -> None:
    base_row = {
        "topic_id": topic_id,
        "predecessors_limitations": "Not yet researched",
        "core_proposal": "Not yet researched",
        "enabling_conditions": "Not yet researched",
        "problems_solved": "Not yet researched",
        "operational_understanding": "Not yet researched",
        "progress_history": [],
        "last_updated_ts": datetime.now(timezone.utc).isoformat(),
    }

    supabase.table("topic_memory").insert(base_row).execute()


def append_progress_entry(
    progress_history: List[dict],
    proposed_update: MemoryUpdateProposal,
) -> List[dict]:
    new_entry = {
        "section": proposed_update.schema_section.value,
        "source": proposed_update.source_link,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return progress_history + [new_entry]


def apply_memory_update_to_db(
    topic_id: str,
    proposed_update: MemoryUpdateProposal,
) -> None:
    column = SECTION_TO_COLUMN.get(proposed_update.schema_section.value)
    if not column:
        raise ValueError("Invalid schema section")

    existing_memory = load_topic_memory(topic_id)
    if not existing_memory:
        raise ValueError("No Topic exists")

    updated_progress = append_progress_entry(
        existing_memory.progress_history,
        proposed_update,
    )

    update_payload = {
        column: proposed_update.new_belief,
        "progress_history": updated_progress,
        "last_updated_ts": datetime.now(timezone.utc).isoformat(),
    }

    supabase.table("topic_memory") \
        .update(update_payload) \
        .eq("topic_id", topic_id) \
        .execute()
