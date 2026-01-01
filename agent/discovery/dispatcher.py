from typing import Dict, List

from agent.pipeline import run_article_ingestion
from agent.db import has_seen_source


def dispatch_items(items: List[Dict]) -> None:
    """
     Dispatch discovery items into the main agent pipeline,
    skipping already-seen sources.
    """
    for item in items:
        source_link = item["source_link"]

        if has_seen_source(source_link):
            print(f"[DISPATCH] Skipping already seen: {source_link}")
            continue

        try:
            run_article_ingestion(
                article_text=item["text"],
                vertical=item["vertical"],
                source_link=source_link,
            )
        except Exception as e:
            print(f"[DISPATCH] Failed for {source_link}: {e}")
