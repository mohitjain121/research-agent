from typing import Dict, List

from agent.main import run_article_ingestion


def dispatch_items(items: List[Dict]) -> None:
    """
    Dispatch discovery items into the main agent pipeline.
    """
    for item in items:
        try:
            run_article_ingestion(
                article_text=item["text"],
                vertical=item["vertical"],
                source_link=item["source_link"],
            )
        except Exception as e:
            print(f"[DISPATCH] Failed for {item['source_link']}: {e}")
