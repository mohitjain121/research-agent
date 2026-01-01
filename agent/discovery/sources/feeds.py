"""
Curated RSS feed sources by vertical.
Focus: Research papers, product launches, industry analysis - not generic news.
"""

FEED_MAP = {
    # ─────────────────────────────────────────────────────────────
    # AI & Machine Learning
    # ─────────────────────────────────────────────────────────────
    "ai": [
        # Research
        "https://arxiv.org/rss/cs.AI",              # arXiv AI papers
        "https://arxiv.org/rss/cs.LG",              # arXiv Machine Learning
        "https://arxiv.org/rss/cs.CL",              # arXiv NLP/Computational Linguistics
        "https://bair.berkeley.edu/blog/feed.xml",  # Berkeley AI Research
        "https://openai.com/blog/rss/",             # OpenAI blog
        "https://deepmind.google/blog/rss.xml",     # DeepMind
        "https://ai.googleblog.com/feeds/posts/default",  # Google AI Blog

        # Industry & Products
        "https://www.techmeme.com/feed.xml",        # Techmeme (curated tech)
        "https://simonwillison.net/atom/everything/",  # Simon Willison (LLM insights)
        "https://lilianweng.github.io/index.xml",   # Lilian Weng (OpenAI, deep dives)
    ],

    # ─────────────────────────────────────────────────────────────
    # Tech & Software
    # ─────────────────────────────────────────────────────────────
    "tech": [
        "https://news.ycombinator.com/rss",         # Hacker News
        "https://lobste.rs/rss",                    # Lobsters (dev-focused)
        "https://blog.pragmaticengineer.com/rss/",  # Pragmatic Engineer
        "https://martinfowler.com/feed.atom",       # Martin Fowler
        "https://www.joelonsoftware.com/feed/",     # Joel on Software
        "https://rachelbythebay.com/w/atom.xml",    # Rachel by the Bay
        "https://danluu.com/atom.xml",              # Dan Luu
        "https://brandur.org/articles.atom",        # Brandur (infra/systems)
    ],

    # ─────────────────────────────────────────────────────────────
    # Crypto & Web3
    # ─────────────────────────────────────────────────────────────
    "crypto": [
        "https://vitalik.eth.limo/feed.xml",        # Vitalik Buterin
        "https://www.paradigm.xyz/feed.xml",        # Paradigm Research
        "https://a16zcrypto.com/feed/",             # a16z Crypto
        "https://research.ethereum.org/feed.xml",   # Ethereum Research (if available)
        "https://messari.io/rss",                   # Messari
        "https://decrypt.co/feed",                  # Decrypt
        "https://www.theblock.co/rss.xml",          # The Block
        "https://banklesshq.com/feed/",             # Bankless
    ],

    # ─────────────────────────────────────────────────────────────
    # Business & Strategy
    # ─────────────────────────────────────────────────────────────
    "business": [
        "https://hbr.org/feed",                     # Harvard Business Review
        "https://stratechery.com/feed/",            # Stratechery (Ben Thompson)
        "https://www.ben-evans.com/benedictevans/rss.xml",  # Benedict Evans
        "https://every.to/feeds/chain-of-thought.atom",     # Every.to Chain of Thought
        "https://seths.blog/feed/",                 # Seth Godin
        "https://www.mckinsey.com/feeds/insights",  # McKinsey Insights
    ],

    # ─────────────────────────────────────────────────────────────
    # Finance & Markets
    # ─────────────────────────────────────────────────────────────
    "finance": [
        "https://www.bloomberg.com/feeds/podcasts/odd_lots.xml",  # Bloomberg Odd Lots
        "https://feeds.a16z.com/a16z",              # Andreessen Horowitz
        "https://mattstoller.substack.com/feed",    # Matt Stoller (antitrust/monopoly)
        "https://www.bridgewater.com/feed",         # Bridgewater (if available)
        "https://www.yieldcurve.com/feed/",         # Yield curve analysis
        "https://ritholtz.com/feed/",               # Barry Ritholtz
    ],

    # ─────────────────────────────────────────────────────────────
    # Startups & VC
    # ─────────────────────────────────────────────────────────────
    "startups": [
        "https://paulgraham.com/rss.html",          # Paul Graham
        "https://www.ycombinator.com/blog/rss/",    # Y Combinator Blog
        "https://a16z.com/feed/",                   # a16z
        "https://www.nfx.com/feed.xml",             # NFX (network effects)
        "https://www.sequoiacap.com/feed/",         # Sequoia
        "https://firstround.com/review/feed.xml",  # First Round Review
        "https://techcrunch.com/feed/",             # TechCrunch
        "https://saastr.com/feed/",                 # SaaStr
        "https://www.lennysnewsletter.com/feed",    # Lenny's Newsletter
    ],
}
