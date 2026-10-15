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

## Retrieval coverage review — 2026-10-15

Focused code review against MVP specification and completion plan C2/C3/C7; Graft unavailable. `pytest backend/tests/unit/test_http_fetcher.py backend/tests/unit/test_content_policy.py backend/tests/unit/test_openrouter.py backend/tests/unit/test_processing_service.py backend/tests/unit/test_scoring.py` (usual offline uv prefix): **62 passed**. No paid fetch/model tests or hosted inspection. Screenshot supplied by owner shows spent 0.00251 USD, reserved 0, two Needs action rows and Ready 0. It establishes displayed failure, not raw provider cause or per-attempt cost. Canonical audit and dispositions recorded; no acceptance-validation relaxation or automatic paid retry.

## Brave/Langfuse extension checkpoints — 2026-10-15/16

RED: new research tests initially failed on missing capability/import; pgTAP Brave test failed on absent submit_search_items before 000007. After implementation, adapter/schema/source tests green. Behavioral regression proof: disabling per-source excerpt attribution makes external-to-primary misattribution test fail; original code restored in finally. Removing SQL stored-source excerpt fence in disposable DB makes pgTAP fail; original function restored in finally, then all suites PASS.

Local PostgreSQL 17.11 migration 000007 applied successfully after existing six; pgTAP suites 13+24+20+6+14 = 77 assertions PASS, plus two overlapping 0.60 USD reservations admit exactly one under 1 USD. No real provider calls. Frontend informed-consent test verifies unchecked default, displayed rate, and explicit web_search submission; 20 frontend tests PASS, lint/build PASS. Final counts/checks recorded below after final review.

Final code checks for approved extension: backend **131 passed**, strict mypy **32 files PASS**, Ruff check PASS / format **81 files PASS**; frontend **20 passed**, lint/build PASS (73 modules, JS 247.26 kB, gzip 76.60 kB). `git diff --check` PASS. `agent-toolkit check` attempted: 127 command not found, not waived or reported passed. PostgreSQL gate **77 assertions PASS** plus overlapping reservations. Diagram checks follow in subsequent receipt. No real provider/telemetry traffic.

Additional accepted-external-citation and primary-only corroboration invariants checked: **132 backend tests passed**. Ruff check/format rerun after formatting additional test. Local PostgreSQL stopped cleanly. No additional frontend/product change since its 20-test/lint/build checkpoint.

Brave/Langfuse workflow generated from committed source 0c43a8c6f6453932e7c285538018475aba5c50fe, retaining fixed source references. Specification SHA-256 cedd6eb05b65a1e3f45dff6b04ba4d21eb341c9ee6b071529d408973a81b8914; artifact SHA-256 283a25d7e9d62138d02efd81a4b913847393e22298975223eccde34886013be7. Finalize: validate/deliver/strict check PASS, exit 2 because browser-check skipped (Chrome unavailable). Layout/schema issues repaired using explicit gate diagnostics; final diagram has no deterministic validation error. No fresh screenshot/perceptual verification. Receipts brave-langfuse.finalize-summary.json and brave-langfuse.browser-check.json. Update notice not required, cache unavailable.

Generated Archify HTML contains template trailing spaces. Preserve its receipt-bound bytes; a path-specific .gitattributes rule disables only blank-at-EOL checks for that generated artifact. Source files retain normal whitespace checks. Full change diff check rerun with this explicit generated-file rule.

Git delivery: fetched origin/main (314c600), fast-forward merged codex/brave-langfuse into main, push returned 314c600..e39d5e8 main -> main, exit 0. Follow-up metadata-only commit records completion. No force, PR, real key or paid-provider test.

## English diagrams — 2026-10-16

Owner requested English diagrams. Translated both editable lifecycle/workflow JSON files and regenerated HTML without changing graph IDs, relationships, sources or runtime code. Set meta.locale=en. Active change/review/roadmap Kanban text also translated; project AGENTS.md records English for future diagrams.

Workflow: specification fde5123659ec9b8793a8b4f6493381af92a7c8983686fe2ec3e129632affa1d2; artifact 3bab3dfb9c6b611717f9e6448e5afdb6c19db237cbb2df6c822004a476bffbe5. Lifecycle: specification b99aedf890b704f7a62eabe0ce70236af3a3f8f915e364ce1f8ffc1b2fdcca8b; artifact 20bade5a200d4f1269e8f3d98127ac660fdd68a2325ef90cbec534f9e97802f3. Latest receipts: brave-langfuse.english/ and lifecycle.english/. Both validate/deliver/strict artifact checks PASS. Finalize exit 2: browser check skipped (Chrome unavailable), no new perceptual inspection. No update notice required. Prior receipt hashes remain historical. No product changes, migrations or paid calls; code tests were not unnecessarily rerun for translation only.

## Duplicate/citation maintenance verification — 2026-10-16

RED: duplicate_links.test.sql initially failed nine of twelve assertions (duplicates created rows/trials; legacy resume allowed concurrent work). Unit whitespace citation test rejected the valid passage with invalid_citation. GREEN after 000008/pure whitespace re-anchoring. Deliberate regression: remove only duplicate guard from test DB function; real concurrent submits create two items/jobs and fail. Restored original function in finally, full gate PASS. Disable whitespace re-anchoring in pure helper; behavioral tests fail, then restore in finally and full backend green.

- Backend **138 passed** (one existing FastAPI/httpx deprecation warning); strict mypy **33 files PASS**.
- Ruff check PASS; format **84 files PASS**.
- Frontend **21 passed**, lint PASS, production build PASS (74 modules; JS 247.76 kB, gzip 76.78 kB).
- PostgreSQL upgrade migration 000008 PASS; **89 pgTAP assertions PASS** plus real overlapping budget reservations and duplicate URL submissions. Duplicate race admits exactly one item/job, same-owner only. Fixtures test batch atomicity, no trial charge, fragments/host/default port normalization, query distinction, expiry, cross-owner use, legacy resume and client RPC denial.
- Adapter tests verify duplicate error translation for normal, Brave and resume paths. HTTP returns 409 and does not wake worker. UI blocks known duplicate before submitting and preserves form; server remains authoritative for unloaded items.
- Exact/whitespace quotations resolve to actual saved bytes; changed words/case and wrong-source attribution still fail. Stored-source SQL fence remains unchanged. No raw provider response or Langfuse trace read; actual production cause remains unconfirmed.
- Required agent-toolkit attempted: unavailable (127). Local PostgreSQL stopped. No real provider traffic, hosted migration, cleanup/deletion, external billing or push in this maintenance checkpoint.

## Complete relevant Langfuse traces — 2026-10-16

- Initial three behavioral tests RED: missing model input, absent event API, missing skip/recovery events. Recovery article reuse assertion also RED before adding source.reused.
- GREEN: six focused tests cover rejected output with retained input/content/reason, credential/identity scrubbing and offline SDK failure isolation, no repeated paid recovery, actual SDK in-memory export with shared parent/trace and token/cost fields, Brave HTTP rejection diagnostics, and full primary+supporting article/search/citation/save flow.
- Deliberate regression: suppress event export, focused event test fails (exit 1, absent search.result); restored implementation then six focused tests PASS. First probe lacked the task's UV cache env and exited 2 before test execution; it is not regression evidence.
- Full backend: 144 passed (one existing FastAPI/httpx deprecation warning). Strict mypy: 33 files PASS. Ruff check PASS; format check: 85 files PASS. No frontend, schema or dependency changes, so no frontend/SQL rerun required for this slice.
- agent-toolkit check remains unavailable (127); Graft unavailable. No paid provider calls. Real SDK uses an in-memory exporter and mocked HTTP only, not hosted ingestion.
- Existing LANGFUSE_ENABLED controls content-inclusive traces by owner request. Configured credentials are redacted from payload text; no authentication headers/account identity/lease tokens are supplied. Generic masking is defense in depth, not complete personal-data anonymization. Traces are bounded/best effort; Langfuse retention is separate from Supabase.

Diagram: brave-langfuse.json/HTML regenerated for local code c844819; spec e7e7dd94f0e19e1a76ff6f8282526b17edf36fb9e892c9decd141f3302e64b79, artifact 701f94d33d68f3aa6b6b098baf041fb28a3cbe93f13005f57bdb56e1f617fbbc. validate/deliver/check pass; finalize exit 2 solely because Chrome unavailable (browser-check skipped, visual review not requested). Receipts: brave-langfuse.content-tracing/. No update notice required.
