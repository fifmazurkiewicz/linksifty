# Analysis chat implementation review

2026-10-18 — Native self-review, not an independent reviewer.

## Outcome

Approve local implementation with the verification limitations in `../evidence.md`.
All non-informational findings have verified Fix-now dispositions in
`review-decisions.md`. No risk acceptance/Skip is inferred. Hosted activation,
paid provider quality and unavailable toolkit/browser checks remain separate.

## Plan fidelity

The feature covers analysis and topic questions; saved source/history context;
conditional, at-most-one search; citation restoration; shared atomic budget;
durable UUID claims; interruption/deletion fencing; and accessible saved chat.
No dependency or general agent framework was added. Historical scores are immutable.
Migration 000013 follows concurrently developed X-ingestion migration 000012.

## Findings resolved before final review

### CHAT-001

Browser RLS cannot query a revoked account table. The corrected owner/item policy
passes real pgTAP checks; server paths separately enforce account status.

### CHAT-002

First-page-only truncation would omit relevant late passages. Selection now ranks
exact chunks across the source and fits byte bounds. The long-source test passes.
Word overlap remains heuristic; the UI/contract make no exhaustive-source claim.

### CHAT-003

Search reservation rejection cannot lead to an untracked final generation.
The application returns insufficient evidence and the budget status without a
search or another model call. The focused behavioral test passes.

### CHAT-004

GET/POST private chat responses now set no-store; API coverage verifies it.

## Security, reliability and conventions

Owner filters apply to every content query. SQL composite references prevent
foreign-owned turns/billing attachments; RLS and server-only mutation privileges
are tested. UUID claims and unique call slots prevent duplicate paid execution
across concurrent connections. Paid errors are not retried. Unknown costs remain
reserved and generation IDs can settle after content deletion. Only fetched,
readable sources become evidence; invalid IDs/output fail closed. Plain text and
HTTP(S)-only source links prevent model HTML/link injection. Pending questions
disable double-send and preserve drafts on error; unmount aborts client requests.
Domain scoring remains isolated; HTTP/provider adapters stay at the edge.

## Evidence and remaining limits

See `../evidence.md`: 283 backend/57 frontend tests, strict mypy, Ruff, production
frontend build, real SQL/concurrency gates. The workflow HTML passes artifact
validation. Missing toolkit and browser runtimes are informational limitations,
not successful checks. Runtime model entailment/research-necessity accuracy needs
explicitly authorized paid acceptance. No hosted operations were executed.
