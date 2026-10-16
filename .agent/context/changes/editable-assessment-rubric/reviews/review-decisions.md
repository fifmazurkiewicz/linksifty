# Review decisions

## REV-001 — Preserve the corrected source hashing function

- Finding: Regression verification initially found copied pre-000006 digest usage
  in the new migration's paste function; see ../evidence.md#database.
- Severity: high
- Impact: correctness; pasted content would fail on Supabase installations with
  pgcrypto under extensions rather than public.
- Decision: Fix now
- Owner: implementation agent
- Rationale: Extend the latest paste behavior, retaining the built-in SHA256 fix.
- Status: verified
- Follow-up: Task 2 in ../plan.md; corrected migration 000009.
- Evidence: All existing SQL suites including processing_hash and the new rubric
  suite pass in the fresh synthetic local DB; fresh legacy-upgrade run also passes.
