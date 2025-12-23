from typing import List, Optional, Tuple
from langchain_core.messages import SystemMessage, HumanMessage


SECTION_SELECTION_PROMPT = """
You are a research analyst responsible for maintaining a structured knowledge base.

Below is:
1) The current understanding of a topic, organized into fixed schema sections
2) A new article or research excerpt
3) A list of candidate schema sections identified by heuristics

Your task:
- From the candidate schema sections, choose EXACTLY ONE section that is most impacted by the new information
- If none are meaningfully impacted, respond with NO_UPDATE

Rules:
- You may ONLY choose from the provided candidate sections
- Do NOT invent new sections
- Do NOT summarize the article
- Do NOT propose memory updates
- Your justification must be 1–2 sentences and explain why this section is most impacted

Output format (follow exactly):

SECTION: <one_candidate_section_or_NO_UPDATE>
REASON: <brief justification>
"""


def parse_llm_section_response(
    llm_text: str,
    candidate_sections: List[str],
) -> Tuple[Optional[str], str]:
    section = None
    reason = None

    for line in llm_text.strip().splitlines():
        if line.startswith("SECTION:"):
            section = line.replace("SECTION:", "").strip()
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    if section is None or reason is None:
        return None, "Invalid format."

    if section != "NO_UPDATE" and section not in candidate_sections:
        return None, "Invalid section selected."

    return section, reason


def chosen_schema_section(
    article_text: str,
    candidate_sections: List[str],
    topic_memory_text: str,
    model,
    max_retries: int = 3,
) -> Tuple[Optional[str], str]:

    if not candidate_sections:
        return None, "No candidate sections."

    base_prompt = SECTION_SELECTION_PROMPT + f"""

Current Topic Understanding:
{topic_memory_text}

Candidate Schema Sections:
{candidate_sections}

Article Text:
{article_text}
"""

    for attempt in range(max_retries):
        prompt = base_prompt
        if attempt > 0:
            prompt += "\nIMPORTANT: Follow the output format exactly."

        response = model.invoke([
            SystemMessage(content="You are a careful research analyst."),
            HumanMessage(content=prompt),
        ])

        section, reason = parse_llm_section_response(
            response.content,
            candidate_sections,
        )

        if section is not None:
            return section, reason

    return None, "LLM failed to select a valid section."
