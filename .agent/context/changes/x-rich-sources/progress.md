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
