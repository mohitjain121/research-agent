from typing import Optional, Tuple, Set
from langchain_core.messages import SystemMessage, HumanMessage

from agent.db.topics import fetch_topics_by_vertical


EXISTING_TOPIC_ROUTING_PROMPT = """
You are a research router.

You will be given:
1) A list of topics (ALL from the same vertical)
2) A new article

Your task:
- Choose the SINGLE most relevant topic
- If none are clearly relevant, respond with NO_TOPIC

Rules:
- You MUST return at most one topic
- Be conservative — only choose if relevance is strong
- Do NOT invent topics
- Do NOT explain the article

Output format (follow exactly):

TOPIC_ID: <topic_id_or_NO_TOPIC>
REASON: <1 sentence justification>
"""


def parse_topic_routing_response(
    llm_text: str,
    valid_topic_ids: Set[str],
) -> Tuple[Optional[str], str]:
    topic_id = None
    reason = None

    for line in llm_text.strip().splitlines():
        if line.startswith("TOPIC_ID:"):
            topic_id = line.replace("TOPIC_ID:", "").strip()
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    if topic_id is None or reason is None:
        return None, "Invalid routing format."

    if topic_id == "NO_TOPIC":
        return None, reason

    if topic_id not in valid_topic_ids:
        return None, "Invalid topic selected."

    return topic_id, reason


def route_article_to_topic(
    article_text: str,
    vertical: str,
    model,
) -> Tuple[Optional[str], str]:
    topics = fetch_topics_by_vertical(vertical)

    if not topics:
        return None, "No topics available for this vertical."

    topics_block = "\n".join([
        f"- {t['id']}: {t['name']}"
        for t in topics
    ])

    prompt = EXISTING_TOPIC_ROUTING_PROMPT + f"""

Topics:
{topics_block}

Article:
{article_text}
"""

    response = model.invoke([
        SystemMessage(content="You are a careful research router."),
        HumanMessage(content=prompt),
    ])

    topic_id, reason = parse_topic_routing_response(
        response.content,
        valid_topic_ids={t["id"] for t in topics},
    )

    return topic_id, reason
