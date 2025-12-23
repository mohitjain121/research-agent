from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from agent.models.proposals import TopicRoutingProposal


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

Output format (follow exactly):

DECISION: <NO_NEW_TOPIC or NEW_TOPIC>
TOPIC_NAME: <only if NEW_TOPIC>
REASON: <1–2 sentence justification>
"""


def build_topic_update(
    article_text: str,
    vertical: str,
    existing_topics: List[str],
    source_link: str,
    model,
) -> Optional[TopicRoutingProposal]:

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
