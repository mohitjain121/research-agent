from langchain_core.messages import SystemMessage, HumanMessage

from models.memory import SchemaSection, TopicMemory
from models.proposals import MemoryUpdateProposal


SECTION_REWRITE_PROMPT = """
You are a research editor responsible for updating ONE section of a structured knowledge base.

Below is:
1) The name of the schema section to update
2) The current belief text for that section (old_belief)
3) A new article or research excerpt

Your task:
- Rewrite the section text to reflect the most accurate current understanding
- Integrate relevant new information from the article
- Preserve useful prior context unless it is contradicted or outdated

Rules:
- Output ONLY the updated section text
- Do NOT explain your reasoning
- Do NOT justify why the update matters
- Do NOT summarize the entire article
- Do NOT introduce information not present in the old belief or the article
- Keep the result concise (1–2 short paragraphs)

Output format (follow exactly):

NEW_BELIEF: <updated_section_text>
"""


def parse_new_belief(llm_text: str) -> str:
    if "NEW_BELIEF:" not in llm_text:
        raise ValueError("Invalid rewrite format")

    return llm_text.split("NEW_BELIEF:", 1)[1].strip()


def build_memory_update(
    topic_memory: TopicMemory,
    chosen_section: str,
    justification: str,
    article_text: str,
    source_link: str,
    model,
) -> MemoryUpdateProposal:

    old_belief = getattr(topic_memory, chosen_section)

    prompt = SECTION_REWRITE_PROMPT + f"""

Schema Section Name:
{chosen_section}

Current Belief:
{old_belief}

Article Text:
{article_text}
"""

    response = model.invoke([
        SystemMessage(content="You are a careful research editor."),
        HumanMessage(content=prompt),
    ])

    new_belief = parse_new_belief(response.content)

    return MemoryUpdateProposal(
        topic_id=topic_memory.topic_id,
        schema_section=SchemaSection(chosen_section),
        old_belief=old_belief,
        new_belief=new_belief,
        why_this_matters=justification,
        source_link=source_link,
    )
