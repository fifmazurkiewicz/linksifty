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

## Approved thread/media correction — 2026-10-19

- Keep the primary source as the root and its author's connected self-replies.
  Exclude branches only when a returned parent is another author in the same
  conversation, or a descendant of an already excluded author reply. Unknown
  parents, cycles and identity failures remain errors. An explicitly submitted
  post must still be present in the accepted thread; never return only a root
  after excluding the submitted post.
- Identify unsupported media types before checking image URLs. Do not fetch,
  transcribe or silently omit videos/GIFs belonging to accepted source posts.
- The owner approved this in-chat design and requested an expandable comments
  panel, with permission to code. The owner subsequently clarified actual reader
  comments, specifically X users. The temporary analysis-note interpretation is
  superseded; the draft panel, tests and screenshots were removed. The owner
  clarified both submitted and searched X posts, plus Reddit only if supported.
- Reddit has no supported comments adapter. Show that state without scraping or
  new credentials. X replies load on explicit charge-disclosed button consent,
  using one lookup and one twenty-result search page. Cache one attempt per owned
  item/source, including uncertain attempts. Source membership is resolved from
  persisted primary/research records, never arbitrary browser URLs. Replies stay
  outside primary and comparison evidence; no model call or score change.


## Image input quality and rejection diagnostics

Retain the configured vision model (default openai/gpt-4.1-mini). Do not attribute
the hosted failure to the model or image quality without its response. Original
CDN resolution is a directly verified input-quality improvement: merge name=orig
for validated /media/ URLs, preserving format/query fields and deduplicating the
normalized download target. Existing credential isolation, fixed host, no
redirects/retries and byte/pixel/image limits continue to apply. Unavailable or
oversized originals stop; there is no lower-quality automatic fallback.

Expose only code-generated check labels, image count and whether cost is known.
Keep raw model/provider messages, image/base64 bytes, source text, keys and
generation IDs out of the new logs/events. Preserve known-cost settlement and
unknown-cost fencing before assessment/source caching. This is diagnostic
maintenance in the existing acquisition path, with no new integration or model.


## T8 approved scope: text only

The owner's explicit request authorizes assessment of complete text while
ignoring media. No runtime opt-in toggle or alternate model is introduced. Keep
full Article bodies/code, connected threads and quoted/embedded text validation.
Media metadata may identify image/video/GIF/audio/other attachments but cannot
block text because bytes/expansions are missing. Do not fetch CDN media or hydrate
a quoted post solely for media. Keep legacy image accounting/reconciliation for
already billed attempts; disable new vision admission in the active service.

Persist nullable omitted_media metadata alongside cached source text using a
server-only owner/lease/account/expiry-fenced RPC (migration 000019). NULL means
legacy or manual scope not recorded; [] marks new text-only fetch with no known
media. Save selected research media metadata in existing bounded JSON. Return
these fields through assessment DTOs and show a visible text-only scope notice
and media labels without hiding them in collapsed sections. No false complete
multimedia claim, backfill, automatic retry, model migration or content rewrite.

## T9 embedded Article text compatibility

Treat `entities.tweets` and `entities.posts` as validated embedded post lists;
merge and deduplicate their IDs, including DraftJS references. Never ignore an
unknown entity or a malformed alias. Missing embedded text receives one direct
lookup using the existing fixed endpoint and strict response validation. Cache
returned posts in the acquisition-local map, so shared references and the later
thread walk reuse them. A failed lookup ends acquisition without a retry.

Retain the existing missing-expansion failure for ordinary quote/repost edges;
this correction targets Article embeds rather than broadening every reference
read. Nested Article embeds use the same walk, cycle/version checks, request
budget, post cap and deadline. Known post-cap exhaustion stops before another
read. Media stay omission metadata. More official X reads can incur X charges
under existing submission/Retry consent; local verification mocks every call.
