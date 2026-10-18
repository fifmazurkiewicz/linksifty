# Rich X sources progress — 2026-10-18

Owner approved complete media/Article ingestion with “YUP LETS IMPLEMENT IT”.
Frame, research, decisions, plan and reviews are recorded here. Graft is
unavailable; focused repository reads used.

- T1 complete locally: full Article body parsing and recursively validated
  dependencies; bounded credential-free static image acquisition. Preview-only,
  unsupported and unavailable sources remain explicit manual fallbacks.
- T2 complete locally: one image-reading batch, durable admission, shared monthly
  budget, late generation IDs and known-cost settlement before source caching.
  Runtime tests cover adapter/extraction/accounting/cache order; SQL and budget
  races cover owner, lease, expiry, duplicate attempts and deletion recovery.
- T3 complete locally: progress/failure/cost UI, setup/architecture/roadmap,
  editable workflow and verification evidence. Fresh review reports no actionable
  findings. Diagram browser QA and agent-toolkit remain unavailable, not passed.

See evidence.md for exact commands/results and acceptance limits. No live paid
request, credentials or hosted mutation was made. Do not archive as hosted
complete. Migration 000016 is now owner-confirmed applied and dd52ffd is published/deployed.
Approved real-post schema/quality acceptance remains pending. Existing main-push
authorization is retained for this ongoing diagnostic fix.

## Hosted diagnosis follow-up

Owner confirms migration 000016 is applied; main was published and Render shows
successful dd52ffd deployment. Existing hosted retries fail at the Article body/
dependency check, before image reading. The old combined check is insufficient
for root-cause diagnosis. A small diagnostics follow-up preserves every rejection
and separates missing/invalid/preview/truncated body, title, block and dependency
checks. Nine new privacy/diagnostic cases fail before the change, pass afterward;
reverting the body diagnostic deliberately makes the protected test fail.
No additional hosted Retry or paid request was made. Exact Article payload/body
availability still needs one explicitly authorized hosted fetch.

## Authorized retry and media-reference fix

The owner authorized one retry. It was run once and failed with
`article_media_invalid` at 20:48:49, before image/assessment inference. The parser
also has a reproducible compatibility gap: scalar media-key references are
rejected rather than resolved from includes.media. Normalize bounded string
references through existing validation/resolution; missing expansions still fail
closed and do not trigger extra API calls. Four new cases fail before the fix
and pass afterward, including both cover/body media and missing expansion paths.
Deliberately removing normalization makes all four fail again. No further live
retry is included in the one-attempt authorization or local verification.


## Approved opt-in X wire diagnostics

The owner approved the in-chat logger design and explicitly requested preparation
and push to main. Completed locally: server-only X_API_DEBUG (default false),
paired request/response IDs, GET URL/parameters, response status/body including
provider and Article-validation failures, redacted transport-error types, bounded
chunked log output. Existing telemetry redaction is reused from a shared module;
configured secrets are passed by the entrypoint even with Langfuse disabled.
Headers are never logged. Opt-in source text/IDs/query visibility is documented.
No additional request, retry, source acceptance, schema or frontend change.

Acceptance: focused red/green and secret-redaction mutation evidence, all 423
backend tests, strict mypy (45 files), Ruff lint/format and whitespace pass.
agent-toolkit remains unavailable (attempted exit 127); Graft unavailable.
Local implementation review approves this bounded diagnostic maintenance.
Existing T1–T3 local completion and pending hosted acceptance board statuses
remain accurate; no new milestone or architecture change. No live paid request
or hosted environment change was made. Activation requires X_API_DEBUG=true
on Render and a new separately authorized Retry. Publishing to main is authorized.


## Approved compatibility execution

T4 in progress: the owner approved code-block support, bounded direct quoted-post
media resolution, twelve images and a dedicated gpt-4.1-mini image reader. The
assessment model stays unchanged. The in-chat bounded design is the approval
artifact; this amendment reuses the active change rather than starting a second
plan store. Research/decisions/plan updated before derived board changes.


### T4 complete locally

Code entities are validated/preserved with original-position limits disclosed.
Quoted Article media are completed by one direct lookup when necessary; known
invalid media are validated first. A local per-fetch hook caps all X calls at
12. Download/reader support is aligned at twelve images for the independently
configured default gpt-4.1-mini. One generation, USD 0.16896 reservation, existing
price/output limits, settlement and complete-source cache are retained. Legacy
four-image gpt-4o-mini is explicit; unknown image models make no paid request.
The assessment model remains gpt-4o-mini. Article fallback wording is corrected.

Offline replay of the actual captured response succeeds with mocked missing
expansions and image bytes: eleven images and all three real code snippets.
No live X/OpenRouter request was made; actual media expansion and vision quality
still require separately authorized hosted acceptance. No new migration.

Final checks: 444 backend tests, 66 frontend tests, strict mypy (45 files), Ruff
lint/format, oxlint and TypeScript/Vite build pass. Deliberate removal of retained
code makes the regression fail and was restored. Diagram specification, delivery
and strict artifact checks pass; browser-check is skipped (Chrome unavailable).
agent-toolkit check was attempted and is unavailable (exit 127). No archive or
hosted-success claim. T1–T4 complete locally; hosted acceptance remains planned.
