# Implementation review — 2026-10-15

Outcome: local implementation reviewed; **revise / release gates still open** until
the required agent-toolkit gate runs. PostgreSQL/RLS/concurrency now pass locally. No risk Skip,
archive, hosted readiness or independent-agent review is claimed.

## Resolved findings

### REV-001 — reservation used an unverified token estimate (high)

The source-byte heuristic could not establish a hard bound for configurable
models/framing. Replaced with a full verified 128K context reservation at enforced
provider ceilings and bounded output; unsupported model IDs fail before inference.
Tests prove the exact bound and absence of any request for an unsupported model.
Disposition: `review-decisions.md#rev-001`.

### REV-002 — durable stage could claim a crashed worker was active (medium)

A stage alone does not prove execution. Added fenced 15-second heartbeats,
60-second leases, a separate 45-second freshness flag and paused UI copy. Unit/UI
tests cover heartbeat cancellation and stale presentation. SQL freshness/fencing assertions also pass in
the disposable database gate. Disposition: `review-decisions.md#rev-002`.

### REV-003 — recovery ignored a saved actual cost (high)

A crash after response persistence but before settlement could keep a known cost
reserved indefinitely if the generation ID was absent or lookup unavailable.
Recovery now settles the saved actual amount first, without another provider call.
The behavioral test failed before the fix and passes after it.
Disposition: `review-decisions.md#rev-003`.

## Database verification

### REV-004 — database semantics (high, now verified locally)

SQL defines monetary locking, lease fencing, owner isolation, direct-write denial
and retention. HTTP mocks cannot validate PostgreSQL behavior. pgTAP plus a
loopback-only disposable-database harness now test sequential rules and overlapping
reservations, and the owner approved preparing a local runtime. PostgreSQL 17.11 / pgTAP 1.3.4
now pass all five migrations, 57 assertions and overlapping reservations. A new
recovery suite exercises service-role RPCs, original-reservation binding, expired
leases, orphaned generation metadata and RLS against actual foreign rows. Controlled
budget/RLS mutations fail as expected, then all checks pass after restoration.
Minimal auth fixtures do not certify hosted GoTrue/JWT/configuration; that remains E1. Disposition: `review-decisions.md#rev-004`.

## Open release gate

### REV-005 — required toolkit check unavailable (medium)

`agent-toolkit check` is required by AGENTS.md; no executable is available. Keep
this gate open, not silently passed. Disposition: `review-decisions.md#rev-005`.

## Coverage and conventions

- Existing package root and dependency direction preserved: transport -> application
  -> pure domain; concrete Supabase/OpenRouter adapters composed in `main.py`.
- Provider output is schema/excerpt validated and deterministic scoring remains one
  source of truth. Partial acquisition does not reserve or call the model.
- Every content/settings/event operation uses verified owner scope. Administrators
  manage account cost metadata only. Client write privileges are revoked in SQL;
  Local SQL/RLS proof now passes; hosted auth/configuration remains E1.
- Current-month totals survive 30-day detail cleanup; unknown reservations remain
  counted. Retention schedule is supplied for explicit activation, not executed.
- Frontend preserves the established visual language, semantic controls, keyboard
  focus, loading/error states and aborts old sessions/streams. Tests exercise the
  saved eight-criterion detail, paste, threshold and cap edits, expiry, submission
  preservation and actionable recovery.
- No new runtime dependencies, paid worker, broker, source enrichment or chat scope.
- Local browser QA retry was denied by the tool URL policy; no circumvention was
  attempted. Component tests are current; prior screenshots are historical fixture
  evidence, not a new visual acceptance. Archify deterministic gates pass, automated
  browser evidence skipped (Chrome unavailable).
- Hosted migration, retention schedule, provider activation, SSE/cold-start and
  paid acceptance remain explicit E1 work. They were not performed.

Canonical execution/check evidence: `../progress.md`, `../evidence.md`. Local code
may be committed for review with these gates visible; it is not release approval.

### REV-006 — compressed/disguised content bypassed the raw body bound (high, fixed)

HTTPX decompression can allocate decoded content before the application's length
check. The fetcher now requests identity encoding and rejects a server that ignores
it before reading the body. PDF/ZIP magic and NUL text also require manual content;
paste rejects NUL at the request boundary. The focused test failed before the fix
and all acquisition tests pass afterward. This intentionally uses manual fallback
rather than a custom decompression implementation. Disposition:
`review-decisions.md#rev-006`.

### REV-007 — source hash portability (high, fixed)

Supabase installs pgcrypto under extensions; public-only RPC search paths cannot resolve unqualified digest. A matching fixture reproduces SQLSTATE 42883 for fetched and pasted source writes. Additive migration 000006 replaces the extension-dependent hash with native SHA256 over explicit UTF8. Owner/lease guards and service-role-only grants preserved. Fresh matching schema plus six migrations, 63 assertions and concurrency pass; reverting old function bodies deliberately fails the new tests. Hosted application remains owner work. See canonical REV-007 disposition; overall revise remains due unavailable toolkit.

## Brave / Langfuse extension review — 2026-10-16

Local code meets approved integration scope. No new general orchestration framework; HTTPX reused for Brave and paid provider; Langfuse SDK stays in infrastructure, injected scopes depend on an application Protocol. Credentials repr-hidden/server-only; default telemetry off and search unavailable without an explicit key and positive verified rate. Browser checkbox authorizes the short public-article query and disclosed plan charge. Pasted text does not opt into search.

Search request is reserved before side effect; persisted pointer prevents automatic resend after crash/timeout. Search snippets never enter assessment or storage; fetched evidence bounded to five sources with source identity/position checks both adapter and SQL. Partial primary acquisition still stops before inference. Existing owner/RLS/fencing and UTC month accounting preserved. Same-host and exact-body dedup are heuristic; do not describe them as proof of independence or a complete fact-checker. Model rejection is categorized; costs still accounted when output is rejected.

Current code findings REV-008/009 are locally addressed by this extension; actual provider behavior still needs authorized hosted acceptance. No raw prompt/response/source/query/user email sent in tracing; exceptions reduced to class name only. SDK errors do not rerun body or stop processing. Required agent-toolkit remains unavailable; overall release outcome stays revise. Diagram browser check has its own evidence and must not be inferred from code tests.

## Duplicate/citation maintenance review — 2026-10-16

REV-010 (high): missing submit dedup allowed unnecessary jobs and spending. Fixed with owner-profile serialized SQL guard in both ordinary and Brave paths, whole-batch rejection, preserved trial accounting and 409 UI handling. Legacy duplicate resume cannot start parallel work alongside an active/completed equivalent link. Existing records/charges unchanged; root/path/query normalization documented. Twelve pgTAP assertions and actual overlapping duplicate transactions pass; guard removal intentionally fails concurrency proof.

REV-011 (medium): strict byte substring rejected whitespace-equivalent valid quotations. Pure helper resolves only whitespace variants back to exact source text; strict source ID and SQL offset checks remain. Unknown IDs get a separate redacted diagnostic. Changed words/case and other-source evidence remain rejected. Behavioral red/green and deliberate regression verified. This fixes a demonstrated category, not a proven diagnosis of the user's inaccessible hosted response. No paid retry is added.

Canonical dispositions in review-decisions.md. Local correction accepted with evidence; overall release checks still retain agent-toolkit and hosted activation limitations. No new complex flow/topology: guards remain inside existing submission and source-validation steps; no diagram graph change required.
