from typing import List, Optional


def identify_schema_sections(article_text: str) -> Optional[List[str]]:
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
