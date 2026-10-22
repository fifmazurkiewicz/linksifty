# Review decisions — documentation refresh

Canonical record; generated board derives from this file. Date: 2026-10-22.

## REV-001 — Current deployment troubleshooting

- Finding: [review](implementation-review.md#rev-001--p2-stale-active-troubleshooting)
- Severity: medium
- Impact: operations
- Decision: Fix now
- Owner: Codex implementer
- Rationale: Active instructions must match the full migration set and implemented X integration.
- Status: verified
- Follow-up: Updated setup troubleshooting; no code/deployment change.
- Evidence: Independent reviewer confirmed correction; [verification](../evidence.md).

## REV-002 — Unknown-cost processing stop

- Finding: [review](implementation-review.md#rev-002--p2-unknown-cost-gate-absent-from-diagram)
- Severity: medium
- Impact: correctness
- Decision: Fix now
- Owner: Codex implementer
- Rationale: The flow must preserve the runtime stop before final validation/publication when cost is unknown.
- Status: verified
- Follow-up: Added known-cost edge condition and recovery text; regenerated diagram.
- Evidence: Independent recheck and final Archify receipt linked in [verification](../evidence.md).

## REV-003 — Current diagram receipt link

- Finding: [review](implementation-review.md#rev-003--p3-diagram-index-pointed-at-superseded-receipt)
- Severity: low
- Impact: correctness
- Decision: Fix now
- Owner: Codex implementer
- Rationale: Readers need the receipt whose hash matches the delivered final artifact.
- Status: verified
- Follow-up: Index points to processing-review-2 and explains earlier reports.
- Evidence: Final relative-link and SHA256 checks recorded in [progress](../progress.md).
