# Chat query classification

2026-10-18 — Owner approved the bounded design and pinned
`typesafe/jev-1.13` through OpenRouter.

- Context and API research complete; Graft unavailable, focused source reads used.
- Implementing: classify before answer/search; refuse off-topic/unsafe requests;
  fail closed on classification errors; preserve per-owner budgeting/idempotency.
- Verification pending: behavioral red/green, provider validation, SQL/concurrency,
  required Python gates, workflow diagram and documentation.
- No paid calls, hosted migration or deployment authorized by this local change.
