"""
Main article ingestion pipeline.
Orchestrates routing, memory updates, and proposal notifications.
"""
from agent.config import model
from agent.db import (
    fetch_topics_by_vertical,
    load_topic_memory,
    log_pending_proposal,
    get_pending_id_for_proposal,
)
from agent.routing import route_article_to_topic, build_topic_proposal
from agent.memory import identify_candidate_sections, select_schema_section, build_memory_update
from agent.ui.telegram.handlers import send_proposal_notification


def run_article_ingestion(
    article_text: str,
    vertical: str,
    source_link: str,
) -> None:
    """End-to-end ingestion for a single article."""

    # 1. Route to existing topic
    topic_id, _ = route_article_to_topic(
        article_text=article_text,
        vertical=vertical,
        model=model,
    )

    # 2. If no topic match, consider new topic proposal
    if topic_id is None:
        existing_topics = [t["name"] for t in fetch_topics_by_vertical(vertical)]

        topic_proposal = build_topic_proposal(
            article_text=article_text,
            vertical=vertical,
            existing_topics=existing_topics,
            source_link=source_link,
            model=model,
        )

        if topic_proposal:
            log_pending_proposal(topic_proposal)
            pending_id = get_pending_id_for_proposal(topic_proposal)

            if pending_id is None:
                print(f"Error: Could not find pending_id for source_link: {topic_proposal.source_link}")
                return

            send_proposal_notification(topic_proposal, pending_id)

        return

    # 3. Load topic memory
    topic_memory = load_topic_memory(topic_id)
    if topic_memory is None:
        print("Topic exists but topic memory missing.")
        return

    # 4. Heuristic section detection
    candidate_sections = identify_candidate_sections(article_text)

    if not candidate_sections:
        # No sections matched → try proposing a NEW TOPIC instead
        existing_topics = [t["name"] for t in fetch_topics_by_vertical(vertical)]

        topic_proposal = build_topic_proposal(
            article_text=article_text,
            vertical=vertical,
            existing_topics=existing_topics,
            source_link=source_link,
            model=model,
        )

        if topic_proposal:
            log_pending_proposal(topic_proposal)
            pending_id = get_pending_id_for_proposal(topic_proposal)

            if pending_id is None:
                print("Error: Could not find pending_id for topic proposal")
                return

            send_proposal_notification(topic_proposal, pending_id)

        return

    # 5. LLM selects exact section
    chosen_section, justification = select_schema_section(
        article_text=article_text,
        candidate_sections=candidate_sections,
        topic_memory_text=str(topic_memory),
        model=model,
    )

    if chosen_section is None or chosen_section == "NO_UPDATE":
        print("No meaningful memory update detected.")
        return

    # 6. Build memory update proposal
    proposal = build_memory_update(
        topic_memory=topic_memory,
        chosen_section=chosen_section,
        justification=justification,
        article_text=article_text,
        source_link=source_link,
        model=model,
    )

    # 7. Log and notify
    log_pending_proposal(proposal)
    pending_id = get_pending_id_for_proposal(proposal)

    if pending_id is None:
        print(f"Error: Could not find pending_id for source_link: {proposal.source_link}")
        return

    send_proposal_notification(proposal, pending_id)
