# Implementation review — 2026-10-15

Outcome: local implementation reviewed; **revise / release gates still open** until
PostgreSQL/RLS/concurrency and the required agent-toolkit gate run. No risk Skip,
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
tests cover heartbeat cancellation and stale presentation. SQL assertions are in
the pending database gate. Disposition: `review-decisions.md#rev-002`.

### REV-003 — recovery ignored a saved actual cost (high)

A crash after response persistence but before settlement could keep a known cost
reserved indefinitely if the generation ID was absent or lookup unavailable.
Recovery now settles the saved actual amount first, without another provider call.
The behavioral test failed before the fix and passes after it.
Disposition: `review-decisions.md#rev-003`.

## Open release gates

### REV-004 — database semantics not executed (high)

SQL defines monetary locking, lease fencing, owner isolation, direct-write denial
and retention. HTTP mocks cannot validate PostgreSQL behavior. pgTAP plus a
loopback-only disposable-database harness now test sequential rules and overlapping
reservations, but the gate exited 77 because psql/runtime is unavailable. Owner was
asked whether to prepare a local runtime or provide a disposable instance. Until
then, do not merge/release as database-verified. Disposition: `review-decisions.md#rev-004`.

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
  SQL/RLS proof remains the gate above.
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
