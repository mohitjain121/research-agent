from typing import List, Dict
import feedparser


def fetch_rss_by_vertical(
    feed_map: Dict[str, List[str]]
) -> List[Dict]:
    """
    Fetch RSS feeds grouped by vertical.
    Returns normalized discovery items with hard vertical assignment.
    """
    all_items: List[Dict] = []

    for vertical, feed_urls in feed_map.items():
        for feed_url in feed_urls:
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries:
                    item = {
                        "title": entry.get("title", ""),
                        "text": (
                            entry.get("summary")
                            or entry.get("description")
                            or ""
                        ),
                        "source": "rss",
                        "source_link": entry.get("link", ""),
                        "published_at": entry.get("published", None),
                        "vertical": vertical,
                    }

                    # hard filter: only keep usable content
                    if item["text"] and item["source_link"]:
                        all_items.append(item)

            except Exception as e:
                print(f"[RSS] Failed for {feed_url}: {e}")

    return all_items
