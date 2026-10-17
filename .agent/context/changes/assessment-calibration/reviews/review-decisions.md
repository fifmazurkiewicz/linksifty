# Review decisions

## REV-001 — Isolate the low-total hype regression

- Finding: [Implementation review](implementation-review.md#rev-001)
- Severity: medium
- Impact: correctness / verification
- Decision: Fix now
- Owner: implementation agent
- Rationale: the all-ones case exercises the key-criterion guard and cannot alone detect restoration of the automatic below-40 hype rule.
- Status: verified
- Follow-up: T5 in [progress](../progress.md); add a below-40 case with all key criteria at 3.
- Evidence: [Deliberate-break check](../evidence.md#deliberate-break-check): 38.46% fixture fails under the restored old rule, passes with the calibrated rule.
