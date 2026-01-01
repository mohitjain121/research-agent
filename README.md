# Research Agent

An autonomous AI agent that continuously discovers new information, proposes structured knowledge updates, and incorporates human-in-the-loop review via Telegram.

> **Project Status:** This project is being archived. It served as a proof-of-concept for autonomous knowledge discovery with human oversight. Future exploration will continue in a forked repository with modified use cases.

---

## What this agent does

This agent runs as a background knowledge worker:

1. **Discovers new content**
   - Pulls articles from curated RSS feeds across verticals (AI, tech, crypto, business, finance, startups)
   - Deduplicates previously seen sources

2. **Analyzes and reasons**
   - Routes content to existing topics or proposes new ones
   - Generates structured proposals (topic creation, memory updates)
   - Explains *why* each proposal should exist

3. **Human-in-the-loop review**
   - Sends proposals to Telegram in real time
   - Allows Approve / Reject directly from chat
   - Captures rejection reasons for future learning

4. **Applies accepted updates**
   - Approved proposals are persisted
   - Rejected proposals are logged with rationale
   - Pending proposals are tracked explicitly

The result is a system that **learns with oversight**, instead of blindly updating memory.

---

## Project Structure

```
research-agent/
├── run_discovery.py              # Entry point - fetches feeds & triggers pipeline
├── agent/
│   ├── config.py                 # Environment config, LLM setup, Supabase client
│   ├── db.py                     # Database operations (topics, proposals, memory)
│   ├── models.py                 # Pydantic models for proposals
│   ├── routing.py                # Topic routing & new topic proposal logic
│   ├── memory.py                 # Memory section detection & update building
│   ├── pipeline.py               # Main article ingestion orchestration
│   ├── discovery/
│   │   ├── dispatcher.py         # Deduplicates & dispatches items to pipeline
│   │   └── sources/
│   │       ├── feeds.py          # Curated RSS feed configuration by vertical
│   │       └── rss.py            # RSS feed fetcher
│   └── ui/
│       └── telegram/
│           ├── bot.py            # Telegram bot setup
│           └── handlers.py       # Approval/rejection handlers
└── .github/
    └── workflows/
        └── run-agent.yml         # GitHub Actions scheduled runner
```

---

## Feed Verticals

The discovery layer pulls from curated sources across these verticals:

| Vertical | Focus Areas |
|----------|-------------|
| **ai** | arXiv papers, OpenAI, DeepMind, Google AI, Berkeley AI Research |
| **tech** | Hacker News, Lobsters, Pragmatic Engineer, engineering blogs |
| **crypto** | Vitalik, Paradigm, a16z Crypto, Messari, The Block |
| **business** | HBR, Stratechery, Benedict Evans, McKinsey |
| **finance** | a16z, Bloomberg, macro/market analysis |
| **startups** | Paul Graham, YC, First Round Review, Lenny's Newsletter |

Feed configuration: `agent/discovery/sources/feeds.py`

---

## How it works

```
run_discovery.py
      │
      ▼
┌─────────────────┐
│  RSS Fetcher    │  Pulls from curated feeds by vertical
│  (sources/rss)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dispatcher    │  Deduplicates, skips seen sources
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Pipeline     │  Routes → Memory update → Proposal
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Telegram Bot   │  Notifies, handles approve/reject
└─────────────────┘
```

---

## Setup

### Requirements

- Python 3.11+
- Supabase account (for persistence)
- Telegram bot token
- Groq API key (or swap LLM provider in `config.py`)

### Environment Variables

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Installation

```bash
pip install -r requirements.txt
```

### Running

```bash
# Run discovery for all verticals
python run_discovery.py

# Or run for specific verticals (in code)
# run_discovery(["ai", "startups"])
```

---

## Architecture Decisions

- **Flat module structure** - Consolidated from nested folders for simplicity
- **Hard vertical assignment** - RSS feeds are pre-tagged by vertical, no classification needed
- **Human-in-the-loop by default** - All proposals require explicit approval
- **Supabase for persistence** - Topics, proposals, and memory stored externally
- **Telegram as primary UI** - Lightweight, mobile-friendly review interface

---

## Why this exists

Most "AI agents" either:
- Fully automate memory updates (unsafe), or
- Require constant manual intervention (unscalable)

This project explores a **middle ground**:
> Autonomous discovery + structured reasoning + lightweight human control

It is designed to evolve toward higher autonomy over time, grounded in feedback.

---

## Limitations & Future Work

This proof-of-concept demonstrated the core loop but has known limitations:

- **Feed quality varies** - Some RSS feeds may be stale or low-signal, training this agent for my usecases will take lot of time via Human in the Loop learning.
- **Research is not linear accumulation** - It’s branching, contradictory, contextual, and often non-improving. Memory updates aren't serving that purpose. It could come in useful for fields like finance, legal, regulations, internal work documentation etc where things evolve / update linearly over time. This works for facts and perhaps I will come back to this later to explore other usecases.


Future iterations (in forked repo) may explore:
- Multi-source discovery (Twitter/X, newsletters, APIs)
- Nodes and edges - ideas, claims, hypotheses, observations; supports, contradicts, extends, reframes
- Rejection-based prompt tuning
- Simpler schema for better learning
---

## Notes

This served as a great project to ship an agent incorporating a varied amount of tools and resources. Its good for learning. The new fork will experiment with usecases that might come in handy, perhaps.
