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
