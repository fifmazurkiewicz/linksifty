# Decisions — 2026-10-18

- Extend FetchResult with immutable in-memory images. X acquisition parses full
  Article bodies and their dependencies; it never treats a preview as the body.
  Support text/plain_text plus validated content_state text blocks where supplied.
  Unknown body shapes, unsupported embeds and missing media remain explicit errors.
- Expand media in existing X calls. Fetch HTTPS images only from pbs.twimg.com,
  without credentials, redirects or proxies; at most four unique static JPEG,
  PNG or WebP images, 5 MB each/10 MB total and 20 million pixels each. Validate
  declared length, decoded format and complete image data. Preserve 60-second X
  acquisition deadline, 12 X API requests and 100 unique collected posts.
- Reuse the configured gpt-4o-mini client for one image-reading batch with strict
  schema, all-image ID coverage and explicit completeness. Transcription and
  observed diagram descriptions are labeled model-extracted, not verbatim article
  text. No summary or assessment is produced by extraction.
- Reserve 0.16896 USD maximum before image inference: full 128k input at existing
  $1/M ceiling plus 8192 output at $5/M. Settle reported actual cost separately
  before assessment. Unknown cost keeps the reservation and requests manual text.
- Migration 000016 adds a per-job extraction pointer and ledger purpose, two
  server-only RPCs for lease-fenced budget admission and late generation IDs.
  The slot cannot repeat until explicit fetch Retry after a known terminal result.
  Reconciliation reuses the existing generation lookup. Deletion retains charges.
- Keep image bytes ephemeral; cache only the final complete source text with
  image provenance/transcription before existing research/assessment. Crashes
  before caching request manual text rather than automatically rebilling.
- Existing operator opt-in and user submission/Retry remain the spend approvals;
  clarify image-reading cost copy. No live calls, credential changes or hosted
  migrations are part of local verification. Existing main-push authorization
  covers publication of this ongoing fix after verification; wait for migration
  activation approval before publishing an auto-deploying backend.
