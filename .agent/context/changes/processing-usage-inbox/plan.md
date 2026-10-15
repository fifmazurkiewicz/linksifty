# Processing, usage and inbox implementation plan

**Goal:** Deliver the approved queue-to-assessment flow, truthful live progress, USD metering/admin budgets and persisted threshold.
**Architecture:** Bounded asyncio execution in FastAPI, fenced PostgreSQL jobs and reservations; owner-scoped SSE snapshots. OpenRouter via existing HTTPX, strict source-grounded output and deterministic scoring. React components preserve existing styling.
**Stack:** Python 3.11+, Pydantic v2, PostgreSQL/Supabase, React/TypeScript. No new dependencies.
**Spec:** `docs/superpowers/specs/2026-10-15-processing-usage-inbox-design.md`.
**Authorization:** Owner instructed “CODE this” after approving scope and setting 30-day cost retention. Execute natively in this chat; no further design permission requested.

## Constraints

- All content/stream/settings calls use verified owner ID. Admin manages metadata/budget only.
- 30-day cost records; current UTC-month totals survive cleanup; unresolved reservations remain counted.
- No remote/paid calls in tests, credentials server-only. No external deployment in this task.
- Failed/partial acquisition stops before model. No automatic repeat of an uncertain paid request.
- Existing 40–100% threshold, 60% default; snapshot at analysis start.

## Review focus

1. Concurrent requests against same budget and lease; enforce in SQL, test under PostgreSQL when available.
2. Cost < one cent, missing cost, timeout, repeat settlement and month rollover.
3. User attempts direct settings/ledger writes and reads another user's content/events.
4. Cold start/disconnection/stale lease; completed provider call must not be sent again.
5. Redirect/partial/oversized/script-only content and invalid model citations.

## Tasks and interfaces

### 1. Durable settings, usage and processing

Files: new `supabase/migrations/20261015_000005_processing_usage.sql`, `supabase/tests/processing_usage.test.sql`, `application/processing_contracts.py`, `infrastructure/processing_repository.py`.
Interfaces: `UsageSummary` (decimal USD fields, UTC reset); `UserSettings`; `ProcessingJob` (lease token/source/threshold/reservation); `ProcessingRepository` owner-scoped operations. SQL locks owner settings for reservation/settlement, fences job writes, stores result before settlement, and uses server-only mutation functions.
- [x] Write failing repository/API tests verifying ownership, money precision and setting validation.
- [x] Add atomic reservation/settlement, scoped settings/budget functions, pasted-source transaction, job stage/result functions, result view and cleanup.
- [x] Run focused tests and SQL checks: all five migrations, 57 pgTAP assertions and overlapping reservations PASS on disposable PostgreSQL 17.11.

### 2. Safe acquisition and provider execution

Files: `http_fetcher.py`, new `openrouter_client.py`, `processing_service.py`, config/main wiring, provider/processing tests.
Interfaces: `OpenRouterClient.assess(text) -> ModelResult`, `.estimate(text) -> Decimal`, `.reconcile(generation_id) -> Decimal | None`; `ProcessingService.wake(owner)`, `.close()`.
- [x] Write failing tests for redirects/limits/content MIME, provider cost/citations, no model on blocked content and uncertain outcome retained.
- [x] Implement per-hop public DNS pinning/stream bounds; strict JSON criteria with exact source excerpts; verified full-context reservation and enforced provider price ceiling.
- [x] Execute bounded per-owner jobs independently from SSE lifetime. Save response before settlement; do not resend reserved attempts.
- [x] Verify tests green and demonstrate regression detection.

### 3. HTTP and live progress

Files: new `api/processing.py`, `main.py`, DTOs and API tests.
Interfaces: GET/PUT `/v1/settings`; GET `/v1/usage`; GET `/v1/activity` SSE (authenticated snapshots); POST `/v1/items/paste`; PUT `/v1/items/{id}/content`; POST `/v1/items/{id}/resume`; GET `/v1/items/{id}/assessment`; admin GET/PUT `/v1/admin/accounts/{id}/usage`.
- [x] Test unauthorized admin edits, invalid threshold, foreign content and SSE owner scope.
- [x] Add thin transport routes, safe mapped errors, short-lived reconnectable streams and wake-on-visit/submission.
- [x] Keep existing submission contract and listing, enriching response from persisted assessments.

### 4. Product UI

Files: `App.tsx`, `lib/api.ts`, new usage/settings/queue/detail components, admin panel, CSS and tests.
- [x] Write failing UI test for queued copy and persisted settings/budget admin edit.
- [x] Add authenticated SSE parser with abort/reconnect, snapshot merge, visible costs, real progress, groups/verdict filter, details and content forms.
- [x] Add admin budget save controls and loading/error/success states; preserve Google/account workflows.
- [x] Verify frontend tests/lint/build and component keyboard flows; historical narrow-layout QA passed, current visual retry blocked by browser URL policy.

### 5. Verify and document

- [ ] Run full backend suite, strict mypy, Ruff check/format, frontend tests/lint/build, `agent-toolkit check` and diff check.
- [x] Update README/deployment/architecture, progress/evidence/roadmap before derived boards.
- [x] Review final diff against spec and record remaining deployment/runtime limitations; no production readiness claim without hosted checks.

## Pause checkpoint — 2026-10-15

Owner requested stopping and recording remaining work. Checked boxes indicate authored code or individually checked behavior, not fully verified task completion. All five tasks remain incomplete until final checks/review; SQL gates have not run. See canonical `progress.md` and the detailed resume list `tasks.md`. No additional implementation action authorized until the owner resumes.

## Resume amendment — 2026-10-15

T2 replaces heuristic estimation with the verified full-context reservation and blocks other model IDs before inference. T3 adds a 15-second heartbeat, 60-second lease and a freshness flag in snapshots; stage labels remain durable rather than timer-driven. These changes implement existing cost-safety/truthful-progress requirements without adding services/dependencies. Test unknown model rejection, heartbeat loss and paused UI; retain SQL/live gate limitations.

## Resume outcome — 2026-10-15

T2–T4 complete locally. T1 database gate now passed after owner-approved local runtime preparation; T5 remains blocked on required agent-toolkit availability. All available final checks passed (124 backend / 19 frontend), documentation and review completed. Historical pause text above records the earlier checkpoint; the owner has since resumed work. See `progress.md`, `tasks.md` and review dispositions for current status. No release/hosted acceptance is claimed.

## Corrective follow-up — source hash portability

Owner reports migrations applied and Settings working, then provides stuck checking-content UI and processing_interrupted logs. Reproduce source writes with pgcrypto under extensions (Supabase layout); replace the schema-dependent digest call in both source-writing RPCs using built-in SHA256 in follow-up migration 000006. Preserve all lease/owner/permission guards. Add fetched/pasted Unicode hash and permission regression tests; test full migration chain on a fresh matching fixture. No new architecture, external activation or paid retry.
