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

## REV-007 — extension-schema-dependent source hash

- Finding: `implementation-review.md#rev-007--source-hash-portability-high-fixed`
- Severity: high
- Impact: correctness / hosted compatibility
- Decision: Fix now
- Owner: implementation
- Rationale: Source writes must work with Supabase pgcrypto in extensions without broadening a security-definer search path. Use native SHA256 and preserve the hash format.
- Status: verified
- Follow-up: owner applies additive migration 000006 in Supabase, refreshes queue, confirms recovery; hosted application not performed here.
- Evidence: `../evidence.md` source-hash red/green and deliberate regression; fresh six-migration chain, 63 assertions and concurrency PASS.

## REV-008 — external source checking absent

- Finding: `information-retrieval-audit.md#rev-008--broad-source-checking-scope-remains-absent-high`
- Severity: high
- Impact: plan fidelity / correctness
- Decision: Fix now
- Owner: implementation; scope/provider decisions require product owner
- Rationale: Full product retrieval is incomplete; latest narrow scope explicitly excluded it, so preserve M6/C7.2 as planned rather than claim success.
- Status: verified
- Follow-up: owner subsequently approved Brave/Langfuse implementation. Local max-five discovery/fetch, dedup/provenance and shared budget implemented; hosted key/plan activation and real acceptance remain E1.
- Evidence: `information-retrieval-audit.md`; prompt forbids browse, no search adapter/service, C7.2 planned.

## REV-009 — opaque model output rejection

- Finding: `information-retrieval-audit.md#rev-009--unusable-provider-output-has-no-diagnostic-category-medium`
- Severity: medium
- Impact: correctness / user / operations
- Decision: Fix now
- Owner: implementation
- Rationale: Distinguish safe rejection categories before spending on repeated attempts; preserve exact-source validation.
- Status: verified
- Follow-up: redacted failure codes and explicit Langfuse metadata tracing implemented/tested; use next authorized hosted trace to diagnose the actual rejection. Exact evidence acceptance is preserved.
- Evidence: `information-retrieval-audit.md`; screenshot has Ready 0 and spent amount, adapter returns assessment=None for multiple causes.

Brave/Langfuse follow-up evidence: `../brave-langfuse-plan.md`, `../evidence.md`; local verification is not hosted provider acceptance.

## REV-010 — duplicate URL submission

- Finding: `implementation-review.md#duplicatecitation-maintenance-review--2026-10-16`
- Severity: high
- Impact: user / spending correctness
- Decision: Fix now
- Owner: implementation
- Rationale: Block duplicate jobs before side effects, including racing requests and legacy resumes.
- Status: verified
- Follow-up: release code and apply migration 000008; retain legacy records and paid reservations.
- Evidence: `../evidence.md` duplicate/citation checkpoint; 12 pgTAP cases and actual concurrent submits with guard-removal regression proof.

## REV-011 — whitespace-only citation mismatch

- Finding: `implementation-review.md#duplicatecitation-maintenance-review--2026-10-16`
- Severity: medium
- Impact: correctness / user
- Decision: Fix now
- Owner: implementation
- Rationale: Resolve formatting-only variations to exact stored text without fuzzy or cross-source matching.
- Status: verified
- Follow-up: actual hosted cause requires an authorized trace; no claim all invalid quotations are repairable.
- Evidence: `../evidence.md`; whitespace RED/GREEN, deliberate regression, invalid-word/case and cross-source rejection tests.
