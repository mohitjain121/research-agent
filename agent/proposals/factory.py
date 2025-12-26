from agent.models.memory import SchemaSection
from agent.models.proposals import TopicRoutingProposal
from agent.models.proposals import MemoryUpdateProposal


def build_proposal_from_row(row):
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
