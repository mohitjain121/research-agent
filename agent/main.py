from agent.config.env import model

from agent.routing.topic_router import route_article_to_topic
from agent.routing.new_topic import build_topic_update

from agent.db.topics import fetch_topics_by_vertical
from agent.db.topic_memory import load_topic_memory

from agent.memory_update.heuristics import identify_schema_sections
from agent.memory_update.section_select import chosen_schema_section
from agent.memory_update.rewrite import build_memory_update

from agent.db.pending import log_pending_proposal


def run_article_ingestion(
    article_text: str,
    vertical: str,
    source_link: str,
) -> None:
    """
    End-to-end ingestion for a single article.
    """

    # 1. Route to existing topic
    topic_id, _ = route_article_to_topic(
        article_text=article_text,
        vertical=vertical,
        model=model,
    )

    # 2. If no topic, consider new topic proposal
    if topic_id is None:
        existing_topics = [
            t["name"] for t in fetch_topics_by_vertical(vertical)
        ]

        topic_proposal = build_topic_update(
            article_text=article_text,
            vertical=vertical,
            existing_topics=existing_topics,
            source_link=source_link,
            model=model,
        )

        if topic_proposal:
            log_pending_proposal(topic_proposal)

        return

    # 3. Load topic memory
    topic_memory = load_topic_memory(topic_id)
    if topic_memory is None:
        print("Topic exists but topic memory missing.")
        return

    # 4. Heuristic section detection
    candidate_sections = identify_schema_sections(article_text)
    if not candidate_sections:
        print("No schema sections matched by heuristics.")
        return

    # 5. LLM selects exact section
    chosen_section, justification = chosen_schema_section(
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

    # 7. Human review
    log_pending_proposal(proposal)
