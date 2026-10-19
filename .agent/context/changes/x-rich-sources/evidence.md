# Rich X sources verification — 2026-10-18

## Behavior and test-first evidence

- Before implementation, acquisition tests exposed missing Article/media result
  fields, preview fallback and blanket media/Article rejection. Provider/service
  tests established all-image completeness, admission and no partial assessment.
- The new SQL suite failed before migration 000016 because
  `reserve_image_reading(uuid,uuid,uuid,numeric)` did not exist. Migration then
  passed the same admission/owner/lease/expiry/settlement/retry expectations.
- Queue tests failed before image progress/failure/cost copy was implemented.
- Deliberately removed the image reader's `complete=false` rejection. The
  incomplete-image case failed on returned source text (1 failed, 7 passed).
  Restored the guard; all eight provider tests passed. No weakened assertion.
- Added actual decoded-pixel, multi-frame PNG and five-image bounds tests;
  27 acquisition cases pass, including URL/credential/redirect isolation,
  full-body versus preview, quoted Article/dependencies and missing embeds.

## Final verification

- Backend: all 398 tests passed, including 27 rich-acquisition cases. One existing
  Starlette/httpx TestClient deprecation warning remains.
- Strict mypy: 44 source files passed.
- Ruff lint: passed. Ruff format: 115 files already formatted.
- Frontend: 66 tests passed; oxlint and TypeScript/Vite production build passed.
- Disposable local PostgreSQL 17: all 13 processing SQL suites pass, including
  24 image-reading assertions. Eight processing concurrency checks pass,
  including one-admission and shared-budget image races.
- Chat ledger regression: 39 SQL assertions and five concurrency checks pass.
- Fresh read-only review: no actionable correctness/security/billing findings;
  reviewer independently ran 38 focused tests before the three extra bounds cases.
- Staged whitespace check: handwritten files pass; generated Archify HTML has
  renderer-produced whitespace-only lines. The full staged check passes with
  blank-at-EOL ignored, preserving the validated artifact bytes and receipts.

## Diagram and unavailable tools

Archify editable contract JSON and HTML are retained. Showcase specification,
artifact delivery and strict artifact checks pass. Finalize exits 2 because
Chrome/Chromium is unavailable; browser-check is skipped, with no screenshots
or perceptual review claimed. See diagram-check/rich-source-workflow.finalize-summary.json.
The diagram describes the approved processing contract, not a pinned code snapshot.
Graft is unavailable, so focused repository reads were used. `agent-toolkit check`
was attempted and exits 127 (command not found); it is not counted as a pass.

## Hosted acceptance and approval boundary

No X/OpenRouter request, provider cost, credential read or hosted database change
was performed for local verification. Apply migration 000016 after 000015 and
before deploying this backend/frontend. Hosted DDL needs owner approval under
AGENTS.md. Existing push-main authorization covers publication, but deploying
before the schema is ready would break reconciliation. Keep this change local
until migration activation is approved/completed.

The exact official Article response schema and full-body availability for the
reported post remain unverified live. Supported bodies/dependencies fail closed;
preview-only output still requires paste. Model transcription/diagram accuracy
needs explicit hosted paid acceptance. No production success is inferred.

## Precise Article diagnostic follow-up

Read-only Render inspection identified the current Article parser failure, not
an access-token denial or image inference error. Migration 000016 application is
owner-confirmed; deployment dd52ffd is shown successful. No paid read was repeated.
Nine new cases first failed because distinct malformed/missing source shapes all
logged the combined check. After fixed branch diagnostics, all 128 X adapter/rich
source tests pass. Replacing `article_body_missing` with the former combined label
caused the targeted test to fail; restoring it preserves the source rejection.
Privacy assertions ensure source text, title, arbitrary metadata and secret-like
fixture values never enter logs. No acquisition acceptance rules, API requests,
budget behavior, schema or frontend changes are part of this follow-up.
Final follow-up gate: 407 backend tests, strict mypy (44 source files), Ruff lint
and format all pass. Existing Starlette/httpx deprecation warning remains.
`agent-toolkit check` again exits 127 (unavailable). Frontend/SQL were not changed;
their prior evidence remains applicable. No live retry was made.

## Authorized hosted retry / media-key compatibility

One authorized Retry was clicked for the reported Akshay post. Existing Render
logs show its terminal result at 20:48:49: article_media_invalid. No second Retry
was clicked. Acquisition stops before model extraction/assessment. X account
invoice cost was not inspected or inferred. The exact returned media value is
not retained, so the observed check cannot prove which media branch failed.

Four reference-expansion cases first failed with article_media_invalid. After
two-line normalization, 132 focused X acquisition tests pass. Missing expansions
remain unavailable, with no media request; supported expanded references acquire
validated bytes. Removing normalization deliberately makes all four cases fail;
it was restored. No extra API lookups, URL acceptance or completeness relaxation.
Final media-reference gate: all 411 backend tests pass, strict mypy (44 files),
Ruff lint and format pass. Existing Starlette/httpx warning remains. Toolkit is
still unavailable (attempted, exit 127). Frontend/SQL unchanged; prior evidence
applies. Hosted success after this fix is not claimed.


## Opt-in request/response logger follow-up

- Initial test-first run: six failures from absent debug constructor/settings,
  four existing/default checks passed. Logging includes HTTP 200 schema rejection
  and HTTP 403 error bodies, with configured and common credential/email redaction.
- Focused green run: 149 X acquisition/config/telemetry cases passed. Added success
  and thread-query logging, long JSON redaction/chunking, startup wiring without
  Langfuse, and interrupted stream checks. The interrupted 403 body initially
  exposed duplicate response entries; one response entry now preserves status
  and no-retry behavior for both 200 and 403 interruptions.
- Deliberately bypassing redaction makes both paired-response privacy tests fail
  (2 failed, 8 deselected); implementation restored before final verification.
- Final: UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty
  pytest backend/tests -q --tb=short: 423 passed, one existing TestClient warning.
- Strict mypy backend/src: success, 45 source files. Ruff check .: passed;
  Ruff format --check .: 117 files already formatted. git diff --check: passed.
- agent-toolkit check: attempted, exit 127 (not installed). Graft unavailable.
  Frontend and SQL unchanged; no new frontend, SQL or diagram validation claimed.
- Shared redaction code is moved unchanged from telemetry. Default warning logs
  retain their privacy guarantees; detailed logs require explicit X_API_DEBUG.
  Event payloads redact before a 32K-character cap and 4K-character chunking;
  truncation is explicit. Headers are excluded. Stream reads retain a 1MB limit.
- Setup documentation and .env.example describe activation, content visibility,
  chunk reconstruction and disabling afterward. No credentials were read, no
  actual X request was made, and Render's environment was not modified.


## Captured Article compatibility verification

Initial red: 18 failures, 53 passes across acquisition/image/config suites. The
frontend fallback test was red (1 failed, 14 passed). Green implementation handles
validated code entities, once-only quoted Article lookup, malformed/missing/
denied/changed responses, thirteen-image rejection and aggregate API request cap.
A further red/green security case proves a known unsafe media URL stops before
another potentially billed quoted-post lookup.

- Focused acquisition/provider/config/service regression: 172 passed; later
  expanded runtime test covers one and eleven image inputs under gpt-4.1-mini.
- Offline captured-response replay: all three actual supplied code snippets
  retained; eleven image artifacts; three mocked X calls; quoted expansions and
  valid PNG bytes were explicitly synthetic. No network and no retained raw
  article/fixture content. This does not prove real missing expansions are available.
- Deliberately removing *extra_code from final Article text makes the targeted
  eleven-image/code test fail (1 failed, 53 deselected); restored before final run.
- Final backend: UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package
  linksifty pytest backend/tests -q --tb=short -> 444 passed. Existing Starlette/
  httpx TestClient deprecation warning remains.
- mypy --strict backend/src -> 45 source files pass; ruff check . passes;
  ruff format --check . -> 117 files already formatted.
- frontend/: npm test -- --run -> 66 passed; npm run lint -> pass;
  npm run build -> TypeScript/Vite pass. No dependency or lockfile changes.
- agent-toolkit check attempted -> exit 127, unavailable. Graft unavailable.
- Archify finalize -> exit 2 because Chrome is absent: validate/deliver/check
  pass, browser-check skipped. Receipts are in compatibility-diagram-check/.
  No screenshot or perceptual-review claim. Editable JSON and rendered HTML kept.
- Change Kanban passes diagram-design self_check.py. Boards are derived after
  canonical plan/progress updates; roadmap milestone statuses are unchanged.
- New limits retain 60 seconds, twelve total X calls, 100 collected posts,
  5MB/image, 10MB total, static decoded images, 20MP/image, 8192 output tokens,
  USD 0.16896 reservation and provider price caps. No accounting/schema change.
  All incomplete/uncertain responses remain ineligible for analysis.

## Thread/media fixes and additional-source notes — 2026-10-19

The analysis-note UI evidence below is historical and superseded: the owner
later clarified actual X-user reader comments. The draft UI/types/tests and
source-notes screenshots were removed. Current retained implementation is T5;
the last frontend baseline without the discarded panel was 69 passing tests.
Do not interpret the historical UI checks as T6 acceptance.

- Red: focused adapter/rich-source suites -> 4 failed, 149 passed. Two cases
  reproduce comment-branch disconnected_thread; two reproduce URL-less video/GIF
  media misclassified as unavailable. Green X adapter/rich-source/debug suites
  -> 163 passed. New guards also reject an excluded submitted post, a missing
  same-author parent and an unrelated foreign-parent conversation.
- Deliberately invert foreign-parent exclusion -> 2 focused failures; restored.
  Deliberately bypass early media-type check -> 2 focused failures, 2 passes;
  restored. Both changes were restored before the full backend run.
- Actual captured responses replay through the updated adapter unchanged: the
  new log returns two images over 3 mocked X/2 mocked CDN calls; the earlier
  Article returns eleven images over 4 mocked X/11 mocked CDN calls. All image
  bytes are synthetic PNGs; source content is neither committed nor printed.
  No live paid call or real CDN verification is claimed.
- UI red: new source grouping/disclosure test fails because the panel is absent
  (1 failed, 14 passed). Green -> 15 assessment tests pass. Existing broad heading
  and source-link assertions are scoped to their owning panels because the new
  panel introduces additional headings/links. Assertions retain eight criteria
  and the original checked-source link.
- UI covers collapsed/independent expansion, source-ID attribution, URL-only
  legacy citation attribution, primary-ID exclusion even when URLs match,
  precise evidence, safe external links, uncited-page state and no panel for
  failed/uncertain/empty or unsafe research. Removing the panel deliberately ->
  1 focused failure, 14 skipped; restored before the final run.
- Final commands (uv uses UV_CACHE_DIR=/private/tmp/linksifty-uv-cache and
  UV_OFFLINE=true to avoid the sandbox-blocked default cache):
  `uv run --package linksifty pytest backend/tests -q` -> 470 passed, existing
  Starlette/httpx TestClient deprecation warning;
  `uv run --package linksifty mypy --strict backend/src` -> 47 files pass;
  `uv run --package linksifty ruff check .` -> pass;
  `uv run --package linksifty ruff format --check .` -> 120 files formatted.
  `frontend/: npm test -- --run` -> 75 passed;
  `npm run lint` -> pass; `npm run build` -> TypeScript/Vite pass.
- `agent-toolkit check` attempted -> exit 127, executable unavailable. Graft
  unavailable; focused source/documentation reads replace code-map orientation.
- Real in-app browser QA uses a temporary localhost Vite fixture, synthetic
  session/source/assessment data and a mocked fetch function. Enter opens the
  panel and its passage; Space opens/closes the panel at a 390px iframe viewport.
  Analysis/Source checking remain collapsed. Desktop dark/mobile light layout
  and visible focus inspected. Screenshots: source-notes-desktop.png and
  source-notes-mobile.png. No console errors. The sandbox initially prevented
  localhost binding; approved escalation allowed the preview. Temporary fixture
  files, tab and server were removed/stopped after QA.
- Existing API source IDs are reflected in the frontend type; no backend API,
  schema, dependency, model request or billing changes. Existing owner scope,
  unknown-cost fencing and no-partial-assessment guards remain. Hosted source
  acceptance remains separate. No unrelated dirty admin file was changed.


## Reader replies verification — 2026-10-19

This section is the current T6 evidence; the earlier analysis-note draft was
removed and its historical checks do not establish acceptance for this feature.

- Behavioral TDD covers explicit strict consent, verified ownership, persisted
  source membership, unsupported/unconfigured sources, cached/repeated/unknown
  attempts and persistence failure without repeated provider calls. Adapter cases
  cover bounded text replies, IDs/conversations/counts, unsafe URLs and provider
  errors. Research preserves selected discussion links separately from fetched
  evidence; UI covers disclosure, independent expansion, safe rendering/links,
  saved-only refresh, errors, empty and unsupported states.
- Mutation: bypassing the admitted-claim guard makes two service cases fail;
  changing browser consent to false makes one focused UI case fail. Restored
  both before final suites. RC1 focus assertion was red before the persistent
  status fix and green afterward (8 focused reader-comments tests).
- With UV_CACHE_DIR=/private/tmp/linksifty-uv-cache and UV_OFFLINE=true:
  `uv run --package linksifty pytest backend/tests -q` -> 487 passed; existing
  Starlette/httpx TestClient deprecation warning remains.
  `uv run --package linksifty mypy --strict backend/src` -> 50 files pass;
  `uv run --package linksifty ruff check .` -> pass;
  `uv run --package linksifty ruff format --check .` -> 127 formatted files.
- `frontend/: npm test -- --run` -> 77 passed; `npm run lint` -> pass;
  `npm run build` -> TypeScript/Vite pass, including after RC1 correction.
- Disposable local PostgreSQL 17 with synthetic auth/data: apply migrations
  1–17, new pgTAP test fails on missing discussion functions; apply 000018,
  all 23 reader-discussion assertions pass. Full processing database gate passes
  all 15 pgTAP files plus budget/deletion/source-selection races and concurrent
  discussion admission (one winner). Run twice; final run includes new race.
  Temporary cluster is stopped/deleted in finally. No hosted database connection,
  real data or credential access. Tests cover owner, rejected/expired account,
  source membership, alias dedup, immutable completion, deletion and client grants.
- Native in-app browser: synthetic assessment/session, mocked GET/POST only.
  Return expands the desktop panel; Space expands mobile at a 390px iframe.
  Load activation focuses “1 reader reply saved.” on both. Dark desktop/light
  mobile layouts and visible focus inspected; no horizontal clipping observed.
  [Desktop screenshot](reader-comments-desktop.png),
  [mobile screenshot](reader-comments-mobile.png). Temporary preview fixtures,
  tab and localhost server were removed/stopped. No live X or model calls.
- Archify editable reader-replies-workflow.json and standalone HTML are retained
  with receipts. Finalize exits 2: specification, delivery and strict artifact
  checks PASS; browser-check SKIPPED (Chrome unavailable). Native product QA does
  not substitute for that diagram-specific browser gate.
- `agent-toolkit check` attempted -> exit 127, unavailable; Graft unavailable.
  Focused source/docs reads were used. Neither unavailable tool is counted passed.
- Rollout: migration 000018 precedes matching backend/frontend deployment.
  Existing X read flag and server bearer token control availability. No new
  provider/model/dependency; no automatic search, request retry or assessment
  ingestion of comments. Reddit remains unsupported. No push/deployment performed.


### Publication snapshot

Owner explicitly requested main push. Origin/main equals HEAD at 017e737 before
publication. A temporary index export containing the exact staged frontend
(without unrelated local admin changes) passes 74 tests, oxlint and TypeScript/
Vite build. Existing 77-test working-tree result includes three admin tests.
No dependency changes or unrelated edits are staged. Strict mypy (50 files),
Ruff lint and Ruff format (127 files) pass again; toolkit attempted, exit 127.
Staged source whitespace check passes excluding the preserved Archify-generated
HTML, whose generated blank lines contain spaces. Its original artifact bytes
and validation receipts are retained without postprocessing.


## Image-reading diagnosis — 2026-10-19

- Owner-provided logs show the Roman post lookup plus two archive pages returning
  200 with two required photos. Screenshot shows image_reading_failed after source
  acquisition. No image-reader response/check was logged. The exact hosted
  rejection is unknown; this is not evidence that the vision model is incapable.
- Read-only public CDN inspection in the in-app browser: the bare first photo URL
  https://pbs.twimg.com/media/HU7cALMXkAAattK.jpg reports 849×1200. Adding
  ?name=orig reports 1055×1491, matching API media dimensions. The photo contains
  dense fine text. Inspection did not call X API/OpenRouter, retain image bytes
  or alter remote content. Tab closed. Web tool could not open these images;
  direct browser inspection supplies the observation, not secondary search claims.
- Red diagnostic tests: 8 failed, 13 passed. Green image reader/processing: 28
  passed, including telemetry propagation, no assessment on failure, cost and
  generation preservation, one call and absence of source/key/provider payload
  in logs. Deliberately clearing failure_check -> 8 failures; restored.
- Red original-size tests: 3 failures. Green acquisition/reader/processing suites:
  87 passed. Cases cover bare, named small and format/query photos; fixed CDN,
  credential-free request, one call and original provenance are asserted. Existing
  unsafe-URL, redirect, byte, pixel and animation checks still run. Removing
  normalization -> 3 failures; restored. Existing URL expectations now explicitly
  expect name=orig; source identity and image byte assertions are retained.
- Final `uv run --package linksifty pytest backend/tests -q --tb=short`: 498
  passed, existing Starlette/httpx deprecation warning. `mypy --strict backend/src`:
  50 files pass; `ruff check .`: pass; `ruff format --check .`: 127 formatted files.
  Commands use UV_CACHE_DIR=/private/tmp/linksifty-uv-cache and UV_OFFLINE=true.
  `agent-toolkit check`: unavailable (exit 127). No frontend/database change.
- No live model call, automatic paid retry, secret access, push, deployment or
  migration was performed. Hosted success/root cause is not claimed.


## Text-only verification — 2026-10-19

The owner's new request explicitly narrows source scope to text. This supersedes
prior media-completeness acceptance criteria; incomplete text still fails closed.
The new supplied trace establishes `image.reading.check=finish_length` with two
images and known cost. Wooden is `x_media_unsupported/non_static_image`. No
speculative model replacement or higher output/token/cost bound is introduced.

- Initial focused text-only regressions: 6 failed, 1 passed. Green cases cover
  photos/video/GIFs/missing expansions, no media request, real text minimum and
  no image reservation. Known malformed/unsafe media URLs are never requested.
  Injecting a CDN GET deliberately -> 4 focused failures; restored before final
  runs. Full Article bodies/code, referenced text, withheld/partial/cycle/identity
  checks remain tested. Old byte-download/vision-execution expectations were
  removed/replaced because they assert behavior the owner explicitly disabled;
  legacy reader unit tests and billing SQL/races remain.
- UI red: new scope region assertion fails (1 failed, 9 passed). Green verifies
  always-visible scope/media labels, independent collapsed analysis, [] versus
  NULL/missing historical metadata. Historical/manual results are not relabeled.
  Research metadata is stored outside source passages. A malformed ignored HTML
  media URL initially caused a fetch error; its regression failed, then passed
  after metadata classification stopped parsing that URL as a fetch destination.
- Backend final: `uv run --package linksifty pytest backend/tests -q --tb=short`
  -> 481 passed, existing Starlette/httpx deprecation warning. Strict mypy -> 50
  files pass; Ruff check -> pass; Ruff format --check -> 128 formatted files.
  uv commands use UV_CACHE_DIR=/private/tmp/linksifty-uv-cache and UV_OFFLINE=true.
- `frontend/: npm test -- --run` -> 81 passed, including three pre-existing local
  admin tests; `npm run lint` passes; TypeScript/Vite build passes. No dependency
  or lockfile changes. Unrelated admin source/tests remain separate local work.
- Fresh disposable PostgreSQL 17: apply 1–18, new test fails on missing RPC; apply
  000019 -> 14 assertions pass. Full gate passes 16 pgTAP files and every existing
  budget/admission/deletion concurrency check, including legacy image accounting.
  Tests cover foreign owner, stale lease, rejected/expired account, unknown labels,
  atomic text/scope, [] semantics, owner RLS reads, forbidden client writes and
  deletion/late-write fencing. The first test incorrectly expected all browser
  reads revoked; corrected to existing owner RLS (foreign=0, owner=1), without
  changing permissions. Locale/UTF-8 startup fixes affect only the disposable
  test launcher. Final run passes and cluster is stopped/deleted in finally.
- Offline replays use actual captured JSON from the three owner attachments and
  mocked transport only. Roman: 1653 readable characters, image omission label,
  zero image bytes, three fully captured X calls. Wooden: actual lookup gives
  275 readable characters and video label, zero image bytes; the second call is
  a synthetic empty archive page because that response was never captured. This
  does not prove current live availability or complete live Wooden thread coverage.
  Raw source/body content is neither printed nor committed as fixtures.
- Native in-app browser with synthetic session/assessment and mocked fetch:
  desktop dark and 390px mobile light show a visible scope notice before Summary.
  Return opens Source checking and reveals the research-media note, preserving
  keyboard focus. Screenshots: [desktop](text-only-desktop.png),
  [mobile](text-only-mobile.png). Main notice wraps without clipping. Temporary
  fixtures, browser tab and localhost Vite server removed/stopped afterward.
- English Archify contract JSON/HTML retained with receipts. Finalize exits 2:
  validate/deliver/strict artifact check PASS; browser-check SKIPPED because Chrome
  is unavailable. Update check unavailable/cache unavailable; no notice required.
  Product browser QA is independent and is not a passing diagram browser gate.
- `agent-toolkit check` attempted -> unavailable, exit 127. Graft unavailable;
  focused source/documentation exploration used. Neither is counted passed.
- Rollout: migration 000019 after 000018, drain old workers, then matching backend/
  frontend. No live media/model/X request, migration, push or deployment performed.
  No automatic retry, refund, assessment rewrite or reclassification of old cache.


### T8 publication snapshot

Owner explicitly requested main push. Origin/main equals local base 87c9fea
before publication. Exact staged frontend export, excluding the three local
admin tests/changes, passes 78 tests, oxlint and TypeScript/Vite build. The earlier
81-test working tree includes those three unrelated admin tests. Only text-only
submission copy from App.tsx and the text-only README section are staged in
shared files. Other admin changes remain local. Staged source whitespace check
passes excluding preserved Archify-generated HTML blank-line spaces; original
artifact bytes and validation receipts are unchanged. No hosted migration or
paid retry is part of publication.
