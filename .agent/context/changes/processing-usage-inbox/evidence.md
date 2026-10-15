# Specification evidence — 2026-10-15

Product code is unchanged. Written specification self-review checked accepted scope, edge cases, ownership, actual costs, retention, threshold timing and dependencies. No placeholders or undisclosed simulation of processing remain.

## Checks

- `git diff --check`: pass.
- `uv run --offline --package linksifty pytest backend/tests`: 94 passed; one installed FastAPI/Starlette dependency deprecation warning.
- `uv run --offline --package linksifty mypy --strict backend/src`: pass, 23 files.
- `uv run --offline --package linksifty ruff check .`: pass.
- `uv run --offline --package linksifty ruff format --check .`: pass, 65 files.
- Initial uv attempts could not access the default cache under the sandbox. Checks reran successfully with `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache` and the existing environment, without installation.
- `agent-toolkit check`: unavailable, command not found. Not reported as passing.
- No frontend product changes, so frontend behavior/build gates were not rerun for this documentation-only stage.

## Target lifecycle artifact

Generated with Archify lifecycle v2, showcase profile. This is a proposed lifecycle, not evidence of runtime implementation. Labels are Polish; fixed viewer controls retain the English fallback.

- Candidate: `lifecycle.json`.
- HTML: `lifecycle.html`.
- Specification SHA-256: `b6aaafe9654ecbba3b7af821dc991c8d633f51c0736a8b51021b2778bff72880`.
- Artifact SHA-256: `0571b75f9b5b465dd8be569d850da6d34e14c026dc1a696addbd25714474809b`.
- Finalize summary: `lifecycle.finalize-summary.json`; validation, delivery and strict artifact check pass.
- Finalize exit 2: browser-check skipped (`viewer/chrome-unavailable`). No full finalize success is claimed.
- Visual review: not requested; no screenshots or perceptual inspection claimed.
- Correction rounds: 0. Update notice not required (cache unavailable).

## Remaining

Owner correction on 2026-10-15: detailed cost records retained for 30 days rather than the proposed 90. Current UTC-month totals and unresolved reservations must not be reduced by history cleanup. Specification, decisions and progress synchronized; documentation-only correction verified with `git diff --check`.

Written-spec owner review, verified provider/hosting contracts, implementation plan and its approval, product implementation and live activation remain. No provider call, deployment or email was performed.

## Implementation checkpoint and explicit pause — 2026-10-15

Code implementation started under the owner's “CODE this” instruction. Later the owner explicitly requested stopping and saving remaining/not-started tasks. No further product-code changes or test runs after that request.

Verified checkpoints, rather than final verification of the current tree:
- Full backend at an earlier implementation checkpoint: 101 passed.
- Focused fetch/repository: 42 passed; OpenRouter: 3 passed; runner: 4 passed; API including scoped SSE snapshot: 6 passed.
- Deliberate regression: removing the exact-excerpt check made `test_invalid_citations_still_account_for_the_paid_call` fail. Original code restored in a `finally` block.
- Strict mypy passed on the then-current 29 source files.
- Frontend passed 13 tests, lint and build at a prior checkpoint. Later auth/admin/aria changes and a new session-expiry test have not received the final full check.
- Latest appended repository test for original-reservation binding and the newly added orphan-reconciliation code have not been run as a full suite.
- SQL migration/pgTAP not executed: no PostgreSQL, Docker or Supabase CLI available. The pgTAP file contains sequential budget checks, not proof of concurrent correctness.
- Agent-toolkit and Graft runtimes unavailable. No hosted integration/cost test performed.

UI QA used the real React components with fake account/content/usage and intercepted network calls, not production authentication/data. Keyboard threshold save 75%, administrator cap 0 and queue filters/actions were inspected. Mobile DOM measurement at 390×844 reported pageWidth=390. Opening assessment was observed at its loading state; final rendered detail remains to verify.

Retained QA artifacts: `qa/preview.html`, `qa/queue-desktop.jpg`, `qa/queue-mobile.jpg`. The harness was moved out of frontend so it is not a product entry. Local Vite was stopped. The temporary tab was already unavailable when closing it; no further browser activity was attempted.

Resume source: `progress.md`, `plan.md` and `tasks.md`. No archive, merge, deployment, paid API call, email or push is claimed. Working-tree code is not included in the earlier documentation commit `1ad8fff`.

## Resume — final local verification (2026-10-15)

The owner explicitly resumed saved tasks. This checkpoint supersedes the paused implementation counts above.

- `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --offline --package linksifty pytest backend/tests`: **124 passed**, one pre-existing FastAPI/Starlette httpx deprecation warning.
- Same uv prefix, `mypy --strict backend/src`: **PASS, 29 files**.
- Same uv prefix, `ruff check .`: PASS; `ruff format --check .`: **PASS, 77 files**.
- In frontend: `npm test -- --run`: **19 passed, 4 files**; `npm run lint`: PASS; `npm run build`: PASS (73 modules, JS 244.78 kB / gzip 75.91 kB).
- `git diff --check`: PASS.
- `agent-toolkit check`: **127, command not found**; mandatory gate remains open.
- Database integration gate: **77, UNAVAILABLE** (psql/runtime absent). Prepared 24 pgTAP assertions plus real overlapping transactions; neither executed. No PostgreSQL, Docker, Supabase CLI or pgTAP runtime found. Owner question about preparing/providing a disposable local runtime remains pending.
- Behavioral red/green evidence: verified model bound and unknown-model rejection, stale-worker UI, recovery of saved actual cost, unexpected compression/disguised binary rejection, and database runner PG-environment sanitation each failed before the corresponding fix and passed afterward. Full suite above includes fixes.
- No remote provider calls, paid tests, installations, migrations, deployment, email or push.

Current browser QA was denied by browser URL security policy; no alternate surface/protocol workaround attempted. Current component tests cover eight-criterion detail/citations, paste, explicit resume, settings/admin edits, session expiry and submission preservation. Prior screenshots remain historical fixture evidence only. Vite stopped; temporary frontend harness removed.

Lifecycle updated to the local contract (not deployed runtime evidence). Latest finalize receipts are in `lifecycle.review-2/`, superseding old root receipts. Candidate SHA-256 `4401fdb6b094051bcc9951909183e9f3c277715a8d34a8e11ff511bca0b4c5a2`; HTML SHA-256 `a7d02bd720aadf6f8330030481a827ec0f28ee30a38d694d25b81331d79056b0`. Validate/deliver/strict check PASS; finalize exit 2, browser check skipped (Chrome unavailable). No fresh perceptual validation claimed.

Review outcome is revise until REV-004/005 close; four code findings fixed. Canonical dispositions: `reviews/review-decisions.md`. No archive or production readiness approval.

## Owner-approved local PostgreSQL gate — 2026-10-15

Owner answered “Przygotuj lokalny runtime testowy”. Installed Homebrew PostgreSQL 17.11 (formula 17.11_1) and its package dependencies; Homebrew also created its unused default cluster. No brew service enabled. pgTAP 1.3.4 obtained from https://api.pgxn.org/dist/pgtap/1.3.4/pgtap-1.3.4.zip; SHA-1 `8bfb8e2cd5ad399ebc4f2e63f0e45e7c45480751` matches official PGXN metadata. Built with PostgreSQL's pg_config and installed extension files. Sources: https://pgtap.org/documentation.html and https://www.postgresql.org/docs/17/app-pg-ctl.html.

Created dedicated `/private/tmp/linksifty-processing-pg17` cluster, database `linksifty_processing_test`, synthetic runner `linksifty_test_runner`; loopback only 127.0.0.1:55439. Initial sandbox initdb failed on shared-memory access; approved escalated initdb/start succeeded. The committed `backend/tests/integration/bootstrap_local_auth.sql` supplies minimal auth.users/auth.uid, Supabase roles and initial grants in a fresh test database only. It is not GoTrue/JWT verification. No real credentials or user data read.

- All five project migrations applied from disk in sorted order, with ON_ERROR_STOP and one transaction each: PASS.
- `check_processing_database.py`: exit 0; account approval **13**, usage **24**, recovery **20** pgTAP assertions PASS (**57 total**).
- Recovery tests exercise RPCs as service_role, owner checks, original late-generation binding across retries, no completion before settlement, saved publication/citations, expired lease fencing, orphaned reservation survival and RLS against a seeded foreign row.
- Two real overlapping 0.60 USD reservations under a 1 USD cap: exactly one admitted, reserved summary 0.60 USD, PASS.
- Deliberately replaced budget condition with false in test DB only: pgTAP produced `not ok`. Restored function in finally. Deliberately disabled reservation RLS: seeded-foreign-row pgTAP produced `not ok`. Restored RLS in finally. Full gate then PASS. No production migration was edited or applied.
- After test-runner edit: full backend **124 passed**, strict mypy **29 files PASS**, Ruff check and format **77 files PASS**. Frontend unchanged since prior 19-test/lint/build checkpoint.
- Server shut down cleanly with pg_ctl fast/wait. Runtime remains installed; test data remains only in temporary cluster, without a running service. No Supabase/hosting or paid integration touched.

REV-004 verified locally. REV-005 (agent-toolkit unavailable), fresh visual acceptance and hosted E1 gates remain open.

## Source hash portability correction — 2026-10-15

User confirmed hosted migrations applied and Settings working, then supplied stuck checking-content screenshot and Render warning processing_interrupted. That warning alone does not establish the hosted SQL exception. Focused code inspection found unqualified digest in save_job_source and paste_item_content, both restricted to search_path public. Official Supabase PostgreSQL schema installs pgcrypto under extensions: https://github.com/supabase/postgres/blob/develop/migrations/schema-17.sql. PostgreSQL built-in SHA256 documented at https://www.postgresql.org/docs/17/functions-binarystring.html.

- RED: with pgcrypto moved to extensions, new processing_hash.test.sql failed five of six assertions; both RPCs raised SQLSTATE 42883, function digest(text, unknown) does not exist. Reproduces the stage interruption without any provider call. Prior public-schema-only fixture missed this compatibility issue.
- GREEN: additive migration 20261015_000006_source_hash.sql replaces only the two functions, preserving guards and explicit service-role permissions; hashes UTF8 through pg_catalog.sha256 instead of extension lookup. Six focused assertions pass (paste, fetched source, correct Unicode hash, counts, client denial).
- Updated fresh bootstrap preinstalls pgcrypto in extensions. Second dedicated cluster /private/tmp/linksifty-processing-hash-pg17 on loopback 55440, database linksifty_hash_test: exact fixture and all SIX migrations from disk applied successfully. Complete gate: 63 pgTAP assertions plus overlapping reservations PASS.
- Deliberate regression: reinstalling both old function bodies in the disposable DB makes hash test fail; restoring 000006 in finally makes all six assertions green again.
- Full backend 124 passed; strict mypy 29 files PASS; Ruff check/format 77 files PASS. Frontend unchanged. agent-toolkit still unavailable (127). Both temporary servers stopped cleanly.
- No hosted SQL, deployment, paid request or push performed for this correction. Hosted error matching remains inferred pending owner application/confirmation. Applying 000006 then reopening queue should permit lease recovery for a pre-inference interruption; no duplicate submission or reservation clearing required.
