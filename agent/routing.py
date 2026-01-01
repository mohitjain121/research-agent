"""
Topic routing logic.
Handles routing articles to existing topics or proposing new topics.
"""
from typing import Optional, Tuple, Set, List
from langchain_core.messages import SystemMessage, HumanMessage

from agent.db import fetch_topics_by_vertical
from agent.models import TopicRoutingProposal


# =============================================================================
# PROMPTS
# =============================================================================

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


NEW_TOPIC_PROMPT = """
You are organizing research topics within a single vertical.

Vertical:
{vertical}

Existing topics in this vertical:
{existing_topics}

New article:
{article_text}

Task:
- Decide whether this article clearly belongs to ONE existing topic
- If yes, respond with NO_NEW_TOPIC
- If not, propose ONE new topic name

Rules:
- Choose at most one topic
- Be conservative: only propose a new topic if necessary
- Do NOT propose multiple topics

Rules for a NEW topic, your explanation must:

- Explicitly name the closest existing topic(s)
- Explain why the article cannot reasonably be included there
- Describe the distinct conceptual boundary of the new topic

Output format (follow exactly):

DECISION: <NO_NEW_TOPIC or NEW_TOPIC>
TOPIC_NAME: <only if NEW_TOPIC>
REASON: <1–2 sentence justification>
"""


# =============================================================================
# ROUTE TO EXISTING TOPIC
# =============================================================================

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
    """Route an article to an existing topic, or return None if no match."""
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


# =============================================================================
# PROPOSE NEW TOPIC
# =============================================================================

def build_topic_proposal(
    article_text: str,
    vertical: str,
    existing_topics: List[str],
    source_link: str,
    model,
) -> Optional[TopicRoutingProposal]:
    """Propose a new topic if the article doesn't fit existing ones."""
    prompt = NEW_TOPIC_PROMPT.format(
        vertical=vertical,
        existing_topics=existing_topics,
        article_text=article_text,
    )

    response = model.invoke([
        SystemMessage(content="You are a careful research organizer."),
        HumanMessage(content=prompt),
    ])

    decision = None
    topic_name = None
    reason = None

    for line in response.content.strip().splitlines():
        if line.startswith("DECISION:"):
            decision = line.replace("DECISION:", "").strip()
        elif line.startswith("TOPIC_NAME:"):
            topic_name = line.replace("TOPIC_NAME:", "").strip()
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    if decision == "NO_NEW_TOPIC":
        return None

    if decision == "NEW_TOPIC" and topic_name and reason:
        return TopicRoutingProposal(
            article_text=article_text,
            suggested_topic_name=topic_name,
            vertical=vertical,
            confidence_reason=reason,
            source_link=source_link,
        )

    return None
