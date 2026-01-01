"""
Database operations for the agent.
All Supabase interactions are centralized here.
"""
from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime, timezone

from agent.config import supabase

if TYPE_CHECKING:
    from agent.models import TopicMemory, MemoryUpdateProposal


# =============================================================================
# SECTION MAPPING
# =============================================================================

SECTION_TO_COLUMN = {
    "predecessors_limitations": "predecessors_limitations",
    "core_proposal": "core_proposal",
    "enabling_conditions": "enabling_conditions",
    "problems_solved": "problems_solved",
    "operational_understanding": "operational_understanding",
}


# =============================================================================
# DEDUPLICATION
# =============================================================================

def has_seen_source(source_link: str) -> bool:
    """Returns True if source_link has already been processed (accepted or rejected)."""
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


# =============================================================================
# PENDING PROPOSALS
# =============================================================================

def log_pending_proposal(proposal) -> None:
    payload = proposal.to_log_payload()
    supabase.table("pending_proposals").insert(payload).execute()


def get_pending_id_for_proposal(proposal) -> str | None:
    """Find the pending_id for a just-logged proposal by its source_link."""
    rows = fetch_pending_proposals()
    return next(
        (row["id"] for row in rows if row["source_link"] == proposal.source_link),
        None
    )


def fetch_pending_proposals() -> List[Dict]:
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


# =============================================================================
# ACCEPTED / REJECTED PROPOSALS
# =============================================================================

def log_accepted_proposal(proposal) -> None:
    payload = proposal.to_log_payload()
    supabase.table("accepted_proposals").insert(payload).execute()


def log_rejected_proposal(proposal, rejection_reason: str) -> None:
    base_payload = proposal.to_log_payload()

    payload = {
        "proposal_type": base_payload.get("proposal_type"),
        "topic_id": base_payload.get("topic_id"),
        "schema_section": base_payload.get("schema_section"),
        "proposed_belief": base_payload.get("new_belief"),
        "why_this_matters": base_payload.get("why_this_matters"),
        "source_link": base_payload.get("source_link"),
        "rejection_reason": rejection_reason,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    supabase.table("rejected_proposals").insert(payload).execute()


# =============================================================================
# TOPICS
# =============================================================================

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

    initialize_topic_memory(topic_id)
    return topic_id


# =============================================================================
# TOPIC MEMORY
# =============================================================================

def load_topic_memory(topic_id: str) -> Optional["TopicMemory"]:
    from agent.models import TopicMemory

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


def apply_memory_update_to_db(topic_id: str, proposed_update: "MemoryUpdateProposal") -> None:
    column = SECTION_TO_COLUMN.get(proposed_update.schema_section.value)
    if not column:
        raise ValueError("Invalid schema section")

    existing_memory = load_topic_memory(topic_id)
    if not existing_memory:
        raise ValueError("No Topic exists")

    new_entry = {
        "section": proposed_update.schema_section.value,
        "source": proposed_update.source_link,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    updated_progress = existing_memory.progress_history + [new_entry]

    update_payload = {
        column: proposed_update.new_belief,
        "progress_history": updated_progress,
        "last_updated_ts": datetime.now(timezone.utc).isoformat(),
    }

    supabase.table("topic_memory") \
        .update(update_payload) \
        .eq("topic_id", topic_id) \
        .execute()
