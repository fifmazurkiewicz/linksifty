# Decisions

- 2026-10-18 — Owner requires analysis/topic investigation, conditional web search and at most one search per query; “finish task” authorizes completing the work without further design/plan handoff pauses.
- Use structured answer-or-search generation and one final answer after research. This needs at most two model calls and one search, avoiding a general agent/tool framework.
- Persist one owner-scoped turn per request UUID, with separate unique reservation slots; uncertain work is not retried automatically.
- Use the existing model, fetcher, Brave integration and monthly ledger. Keep the completed assessment immutable.
