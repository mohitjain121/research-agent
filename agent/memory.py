"""
Memory update logic.
Handles heuristic section detection, LLM section selection, and memory rewriting.
"""
from typing import List, Optional, Tuple
from langchain_core.messages import SystemMessage, HumanMessage

from agent.models import SchemaSection, TopicMemory, MemoryUpdateProposal


# =============================================================================
# PROMPTS
# =============================================================================

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


# =============================================================================
# HEURISTIC SECTION DETECTION
# =============================================================================

def identify_candidate_sections(article_text: str) -> Optional[List[str]]:
    """
    Heuristically identify which schema sections may be impacted.
    Returns a list of candidate section names or None.
    """
    text = article_text.lower()
    matched_sections = []

    if "previous models" in text or "prior approaches" in text:
        matched_sections.append("predecessors_limitations")

    if "we propose" in text or "this paper introduces" in text:
        matched_sections.append("core_proposal")

    if "scales better" in text or "solves prior limitations" in text:
        matched_sections.append("problems_solved")

    if (
        "market unlocked" in text
        or "novel product" in text
        or "multiple business usecases" in text
        or "model works like this" in text
    ):
        matched_sections.append("operational_understanding")

    if not matched_sections:
        return None

    return matched_sections


# =============================================================================
# LLM SECTION SELECTION
# =============================================================================

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


def select_schema_section(
    article_text: str,
    candidate_sections: List[str],
    topic_memory_text: str,
    model,
    max_retries: int = 3,
) -> Tuple[Optional[str], str]:
    """LLM selects the most impacted section from candidates."""
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


# =============================================================================
# MEMORY REWRITING
# =============================================================================

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
    """Build a memory update proposal by rewriting the chosen section."""
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
