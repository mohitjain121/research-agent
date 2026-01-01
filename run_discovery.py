"""
Discovery entry point.
Fetches RSS feeds and dispatches items to the processing pipeline.
Run this as a scheduled job (cron, GitHub Actions, etc.)
"""
from agent.discovery.sources.feeds import FEED_MAP
from agent.discovery.sources.rss import fetch_rss_by_vertical
from agent.discovery.dispatcher import dispatch_items


def run_discovery(verticals: list[str] | None = None):
    """
    Fetch and process RSS feeds.

    Args:
        verticals: Optional list of verticals to process.
                   If None, processes all verticals in FEED_MAP.
    """
    if verticals:
        feed_map = {v: FEED_MAP[v] for v in verticals if v in FEED_MAP}
    else:
        feed_map = FEED_MAP

    print(f"[DISCOVERY] Fetching feeds for: {list(feed_map.keys())}")

    items = fetch_rss_by_vertical(feed_map)
    print(f"[DISCOVERY] Found {len(items)} items across all feeds")

    dispatch_items(items)
    print("[DISCOVERY] Complete")


if __name__ == "__main__":
    # Run for all verticals
    run_discovery()

    # Or run for specific verticals:
    # run_discovery(["ai", "startups"])
