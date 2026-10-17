# Review decisions — 2026-10-17

## REV-001 — Late-result lock order

- Finding: Late-result persistence locks reservations before jobs; deletion must follow that order.
- Severity: high
- Impact: correctness and operations
- Decision: Fix now
- Owner: implementation agent
- Rationale: Prevent avoidable deadlocks without changing late-charge reconciliation.
- Status: verified
- Follow-up: [Database/API step](../progress.md)
- Evidence: [Deletion/result concurrency gate](../evidence.md)

## REV-002 — Legacy inconsistent child ownership

- Finding: Existing foreign keys do not enforce composite owner relationships; cascades could affect a malformed foreign child or billing reference.
- Severity: high
- Impact: security/privacy
- Decision: Fix now
- Owner: implementation agent
- Rationale: Reject the whole batch if any child owner differs, avoiding unrelated schema/data repair.
- Status: verified
- Follow-up: [Database/API step](../progress.md)
- Evidence: [Malformed source/billing owner SQL cases](../evidence.md)

## REV-003 — Stale snapshot after successful deletion

- Finding: An in-flight snapshot can still contain successfully deleted IDs.
- Severity: medium
- Impact: user and correctness
- Decision: Fix now
- Owner: implementation agent
- Rationale: Keep only deleted IDs in session memory and filter later item snapshots.
- Status: verified
- Follow-up: [Queue UI step](../progress.md)
- Evidence: [Authenticated app stale-snapshot test](../evidence.md)
