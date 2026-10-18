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
