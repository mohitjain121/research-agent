from dataclasses import dataclass
from agent.models.memory import SchemaSection


@dataclass
class TopicRoutingProposal:
    article_text: str
    suggested_topic_name: str
    vertical: str
    confidence_reason: str
    source_link: str

    def summary(self) -> str:
        return f"""
TOPIC ROUTING PROPOSAL
Suggested Topic: {self.suggested_topic_name}
Vertical: {self.vertical}

WHY:
{self.confidence_reason}
"""

    def apply(self) -> None:
        from agent.db.topics import create_topic
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

    def summary(self) -> str:
        return f"""
MEMORY UPDATE PROPOSAL
Topic ID: {self.topic_id}
Section: {self.schema_section.value}

OLD:
{self.old_belief}

NEW:
{self.new_belief}

WHY:
{self.why_this_matters}
"""

    def apply(self) -> None:
        from db.topic_memory import apply_memory_update_to_db
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
