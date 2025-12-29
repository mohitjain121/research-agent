# Research Agent

An autonomous AI agent that continuously discovers new information, proposes structured knowledge updates, and incorporates human-in-the-loop review via Telegram.

## What this agent does

This agent runs as a background knowledge worker:

1. **Discovers new content**
   - Pulls articles from RSS feeds by vertical (AI, startups, etc.)
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

## Architecture overview

- **Discovery layer**  
  Fetches and dispatches new content (RSS, feeds).

- **Routing & proposal layer**  
  Decides whether content maps to an existing topic or requires a new one.

- **Persistence layer (Supabase)**  
  Stores topics, pending proposals, accepted updates, and rejections.

- **Review layer**  
  Clean separation between:
  - CLI review (legacy / manual)
  - Telegram-based review (current primary UI)

- **UI layer (Telegram bot)**  
  Acts as the primary interface for reviewing and applying proposals.

---

## Why this exists

Most “AI agents” either:
- fully automate memory updates (unsafe), or
- require constant manual intervention (unscalable).

This project explores a **middle ground**:
> autonomous discovery + structured reasoning + lightweight human control.

It is designed to evolve toward higher autonomy over time, grounded in feedback.

---

## Current status

- ✅ End-to-end pipeline working
- ✅ Telegram-based approval flow
- ✅ Explicit proposal lifecycle (pending → accepted / rejected)
- ✅ Clean separation of concerns (discovery, routing, review, UI)

---

## Work in progress / next steps

This is an active project. Planned improvements include:

- **Learning from rejection**
  - Aggregate rejection reasons
  - Detect patterns by proposal type, schema section, and source
  - Feed signals back into prompts and heuristics

- **Improved routing heuristics**
  - Reduce unnecessary new-topic proposals
  - Stronger schema matching before LLM invocation

- **Discovery quality control**
  - Source-level quality scoring
  - Feed fatigue detection
  - Gradual exploration instead of blind breadth

- **Additional review surfaces**
  - GitHub Issues as an audit trail
  - Digest-style notifications

- **Observability**
  - Proposal metrics
  - Review latency
  - Acceptance / rejection ratios

Autonomy modes (auto-apply, per-source trust) will only be introduced **after** learning loops are in place.