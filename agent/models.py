"""
Data models for the agent.
Contains all dataclasses, enums, and the proposal factory.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class SchemaSection(str, Enum):
    PREDECESSORS_LIMITATIONS = "predecessors_limitations"
    CORE_PROPOSAL = "core_proposal"
    ENABLING_CONDITIONS = "enabling_conditions"
    PROBLEMS_SOLVED = "problems_solved"
    OPERATIONAL_UNDERSTANDING = "operational_understanding"


# =============================================================================
# TOPIC MEMORY
# =============================================================================

@dataclass
class TopicMemory:
    topic_id: str
    topic_name: Optional[str]

    predecessors_limitations: str
    core_proposal: str
    enabling_conditions: str
    problems_solved: str
    operational_understanding: str

    progress_history: List[dict] = field(default_factory=list)
    last_updated_ts: Optional[datetime] = None


# =============================================================================
# PROPOSALS
# =============================================================================

@dataclass
class TopicRoutingProposal:
    article_text: str
    suggested_topic_name: str
    vertical: str
    confidence_reason: str
    source_link: str

    def ui_summary(self) -> str:
        return (
            "📌 Proposal Type: Topic Routing\n"
            f"🆕 Suggested Topic: {self.suggested_topic_name}\n"
            f"📂 Vertical: {self.vertical}\n"
            f"🔗 Source: {self.source_link}\n"
            f"🧠 Rationale: {self.confidence_reason}"
        )

    def apply(self) -> None:
        from agent.db import create_topic
        import uuid

        topic_id = str(uuid.uuid4())
        create_topic(topic_id, self.suggested_topic_name, self.vertical)

    def to_log_payload(self) -> dict:
        return {
            "proposal_type": "topic_routing",
            "suggested_topic_name": self.suggested_topic_name,
            "vertical": self.vertical,
            "confidence_reason": self.confidence_reason,
            "source_link": self.source_link,
        }


@dataclass
class MemoryUpdateProposal:
    topic_id: str
    schema_section: SchemaSection
    old_belief: str
    new_belief: str
    why_this_matters: str
    source_link: str

    def ui_summary(self) -> str:
        return (
            "📌 Proposal Type: Memory Update\n"
            f"🗂️ Topic ID: {self.topic_id}\n"
            f"📑 Section: {self.schema_section.value}\n"
            f"🔗 Source: {self.source_link}\n\n"
            f"📜 Old Belief:\n{self.old_belief}\n\n"
            f"✨ New Belief:\n{self.new_belief}\n\n"
            f"💡 Why: {self.why_this_matters}"
        )

    def apply(self) -> None:
        from agent.db import apply_memory_update_to_db
        apply_memory_update_to_db(self.topic_id, self)

    def to_log_payload(self) -> dict:
        return {
            "proposal_type": "memory_update",
            "topic_id": self.topic_id,
            "schema_section": self.schema_section.value,
            "old_belief": self.old_belief,
            "new_belief": self.new_belief,
            "why_this_matters": self.why_this_matters,
            "source_link": self.source_link,
        }


# =============================================================================
# FACTORY
# =============================================================================

def build_proposal_from_row(row):
    """Reconstruct a proposal object from a database row."""
    if row["proposal_type"] == "topic_routing":
        return TopicRoutingProposal(
            article_text=None,
            suggested_topic_name=row["suggested_topic_name"],
            vertical=row["vertical"],
            confidence_reason=row["confidence_reason"],
            source_link=row["source_link"],
        )

    if row["proposal_type"] == "memory_update":
        return MemoryUpdateProposal(
            topic_id=row["topic_id"],
            schema_section=SchemaSection(row["schema_section"]),
            old_belief=row["old_belief"],
            new_belief=row["new_belief"],
            why_this_matters=row["why_this_matters"],
            source_link=row["source_link"],
        )

    raise ValueError(f"Unknown proposal_type: {row['proposal_type']}")
