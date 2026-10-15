# Review decisions — implementation round 1

No Skip decisions. Every remaining gate stays visible until verified.

## REV-001 — verified reservation bound

- Finding: [implementation review](implementation-review.md#rev-001--reservation-used-an-unverified-token-estimate-high)
- Severity: high
- Impact: correctness / spending safety
- Decision: Fix now
- Owner: implementation
- Rationale: Full context bounds framing/tokenization without another dependency; unknown models must not incur cost.
- Status: verified
- Follow-up: plan T2; `OpenRouterClient.estimate` and fail-closed adapter guard.
- Evidence: `../evidence.md` resume tests: exact bound and unknown-model red/green tests.

## REV-002 — worker liveness

- Finding: [implementation review](implementation-review.md#rev-002--durable-stage-could-claim-a-crashed-worker-was-active-medium)
- Severity: medium
- Impact: user / correctness
- Decision: Fix now
- Owner: implementation
- Rationale: A stored processing stage must not imply an active worker after interruption.
- Status: verified
- Follow-up: plan T3 locally fixed; SQL freshness/fencing assertions also passed under REV-004.
- Evidence: `../evidence.md`; heartbeat-loss service test, stale-worker Queue test, passing SQL freshness assertions.

## REV-003 — recover saved actual cost

- Finding: [implementation review](implementation-review.md#rev-003--recovery-ignored-a-saved-actual-cost-high)
- Severity: high
- Impact: correctness / recovery
- Decision: Fix now
- Owner: implementation
- Rationale: Persisted actual spend is authoritative; do not require another lookup or repeat inference.
- Status: verified
- Follow-up: plan T2; settle `model_result.cost` before generation lookup.
- Evidence: `../evidence.md`; saved-actual-cost regression red/green, existing uncertain-reservation tests.

## REV-004 — PostgreSQL / RLS / concurrent reservations

- Finding: [implementation review](implementation-review.md#rev-004--database-semantics-not-executed-high)
- Severity: high
- Impact: security/privacy / money / operations
- Decision: Fix now
- Owner: implementation, runtime access supplied/approved by owner
- Rationale: Mandatory proof cannot be inferred from mocked REST calls.
- Status: verified
- Follow-up: rerun the committed gate after schema changes; hosted Supabase/GoTrue and deployment acceptance remain E1.
- Evidence: `../evidence.md` owner-approved runtime checkpoint: five migrations, 57 pgTAP assertions and overlapping transactions PASS; controlled budget/RLS mutations detected, then restored and PASS.

## REV-005 — agent-toolkit gate

- Finding: [implementation review](implementation-review.md#rev-005--required-toolkit-check-unavailable-medium)
- Severity: medium
- Impact: project conventions / release verification
- Decision: Fix now
- Owner: implementation, available toolkit runtime required
- Rationale: AGENTS.md explicitly requires this check; unavailability is not acceptance.
- Status: open
- Follow-up: supply existing agent-toolkit executable and run `agent-toolkit check`; no automatic installation or Skip.
- Evidence: `../evidence.md`; command unavailable.

## REV-006 — bounded source bytes

- Finding: [implementation review](implementation-review.md#rev-006--compresseddisguised-content-bypassed-the-raw-body-bound-high-fixed)
- Severity: high
- Impact: security / resource availability / unsupported-source policy
- Decision: Fix now
- Owner: implementation
- Rationale: Request identity encoding and reject unexpected compression before body iteration; do not implement an unnecessary custom decompressor. Detect obvious binary formats and reject pasted NUL.
- Status: verified
- Follow-up: plan T2; manual fallback for unsupported responses.
- Evidence: `../evidence.md`; acquisition red/green test and 42 passing fetcher cases.
