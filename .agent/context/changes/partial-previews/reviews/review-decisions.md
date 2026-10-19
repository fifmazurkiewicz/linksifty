# Partial preview review decisions

## PP1 — Hide Retry while preview cost is unknown

- Finding: [Implementation review](implementation-review.md#pp1--unknown-preview-charge).
- Severity: medium (P2).
- Impact: users could click Retry while the database correctly refused an unresolved preview charge.
- Decision: Fix now.
- Owner: Codex.
- Rationale: expose the owner-scoped pending charge and retain Paste without suggesting another fetch.
- Status: verified.
- Follow-up: [canonical execution](../progress.md), unknown-charge queue behavior.
- Evidence: [verification](../evidence.md); new UI assertion failed before implementation and passes; SQL pending/settled fields and Retry fences pass.

## PP2 — Atomically save Submit/Retry preview consent

- Finding: [Implementation review](implementation-review.md#pp2--consent-admission-race).
- Severity: medium (P2).
- Impact: a worker could claim a newly committed job before a separate consent RPC, missing the approved automatic preview.
- Decision: Fix now.
- Owner: Codex.
- Rationale: forward the typed flag through existing services/repositories to three-argument RPC overloads; reuse existing submission/retry operations and enable consent in one transaction.
- Status: verified.
- Follow-up: [canonical progress](../progress.md), atomic consent publication.
- Evidence: [verification](../evidence.md); API forwarding regression fails before correction; 31 SQL assertions include atomic fetch/search/retry consent, with all existing budget/ownership races passing.
