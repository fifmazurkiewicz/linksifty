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


## Approved captured-payload compatibility amendment

The owner approved the short in-chat design and dedicated image-model change.
- Support validated entities.code; preserve exact supplied snippets/content and
  language. Where no offsets exist, label appended code as position unspecified;
  never invent insertion offsets. Invalid/unknown entities still fail closed.
- When a quoted Article lacks media URLs, directly look up that post once with
  existing expansions, preserving version/identity checks. Already-looked-up
  posts are never retried. Cap all X calls, including searches, at twelve within
  the existing 60-second acquisition deadline; no arbitrary media-key URL guessing.
- Raise the shared unique-image ceiling to twelve, keeping 5MB/image, 10MB total,
  static decoding, allowlist, credential isolation and all-image completeness.
- Add OPENROUTER_IMAGE_MODEL default openai/gpt-4.1-mini, independent of the
  assessment model. Keep the existing 0.16896 USD reservation, one generation,
  8192 output bound, max_price ceilings and no fallback/retry. Legacy explicitly
  selected gpt-4o-mini retains its four-image reader cap. Unknown models fail
  before a provider call. No schema or budget-ledger migration is needed.
- Correct the broad Article fallback wording; run frontend tests and build.
- Keep current assessment model. Stronger evaluation needs evidence after input
  completeness is fixed. Mock all integrations; no live paid test or environment
  mutation. Existing main-push authorization covers this ongoing ingestion fix.
