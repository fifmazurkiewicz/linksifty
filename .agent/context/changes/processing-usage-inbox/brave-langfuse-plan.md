# Brave + Langfuse — approved extension

Owner approved both scopes and explicitly requested code, documentation, diagrams, merge and push to main. This extends the existing active change; no second lifecycle or lessons store. Current client date 2026-10-16 (work began 2026-10-15).

## Scope and decisions

- Official Langfuse SDK 5 (bounded <6), optional metadata-only server tracing. Explicit opt-in environment flag; no prompts, outputs, article text, URLs, search queries, emails or bearer/API secrets exported. SDK problems do not stop or repeat business operations.
- Official Brave Web Search via existing HTTPX. Server key plus positive operator-verified per-request rate required before enabling capability. Search is opt-in per public-link submission; pasted content never enters search by default.
- One query per item, up to ten transient URL candidates, no more than five additional fetch attempts; one host per candidate and normalized exact-content dedup. These are heuristics, not a guarantee of independent publishers. Search snippets are neither evidence nor persisted.
- Durable search reservation independent of model reservation; same owner settings lock and shared USD cap. Configured plan rate charged on confirmed successful HTTP response, not claimed to be an invoice-reported actual. Uncertain request remains reserved and is never repeated automatically. Model actual cost stays provider-reported.
- Fetch additional pages through existing DNS/redirect/size/MIME/completeness guards. Store bounded passages (12K characters/source), source IDs and URLs under owner-scoped job, expiring with item (30 days). Existing primary completeness guard unchanged.
- Assessment cites exact source ID/text/offset; SQL checks stored passage again. No external evidence means independent corroboration cannot receive a higher score based only on primary claims.
- UI: informed search checkbox and rate, real search/check stages, external source list/status, actionable rejection categories. No chat/X implementation in this extension.

## Execution

- [x] Establish RED tests for provider diagnostics/source attribution and missing SQL contract.
- [x] Implement telemetry, Brave adapter, durable search orchestration, source citation validation and migration 000007.
- [x] Implement informed opt-in, cost wording, status and source provenance UI.
- [x] Test mock providers and real disposable PostgreSQL. Deliberately disable source attribution/SQL fence to demonstrate failures, then restore.
- [x] Complete final available quality checks and implementation review, synchronize documentation and diagrams.
- [x] Commit approved changes, fast-forward main and push origin/main. Verified push 314c600..e39d5e8; no force-push.

Diagram browser check and agent-toolkit unavailable; neither is claimed passed.

No real Brave/OpenRouter/Langfuse key or paid call used. Hosted activation and actual provider acceptance require operator configuration after migration 000007.

## Superseding observability decision — 2026-10-16

Owner explicitly requested all relevant logs and article content by default. The earlier metadata-only scope is historical: enabled Langfuse now exports bounded/redacted article/model content and complete relevant analysis events. No additional content toggle, new provider call, migration or blanket HTTP logging. See decisions.md and deployment/setup.md for the current privacy/retention contract.
