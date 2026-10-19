# Verified research — 2026-10-18

## Embedded Article compatibility — 2026-10-19

Owner-supplied logs at 16:20:39 UTC show HTTP 200 for the Argona0x submission,
then `x_article_incomplete/article_entities_invalid`. Reassembling five complete
response chunks yields a quoted Article with 7,387 body characters, nine code
snippets and two `entities.tweets` IDs, without expanded embedded bodies.
Current parser accepts only `posts`; an in-memory alias probe then reaches
`partial_content/missing_referenced_post`. Existing tests use `posts` and fully
supplied expansion bodies, missing both actual shape and completion behavior.

Graft unavailable; focused adapter/parser/tests and active text-only contract
read. Existing `_lookup` validates returned identity and remembers all expanded
posts/media with conflict and post-count guards. Reusing it inside the dependency
walk preserves response/access checks and the fetch-local twelve-request hook
and sixty-second timeout. No provider SDK, endpoint or schema assumption is new.
Only missing Article embedded edges are completed; ordinary quote/repost missing
expansions retain their established failure behavior. Raw Article text remains
uncommitted, and every verification call is mocked.

Graft is unavailable. Focused reads cover XAdapter, ProcessingService,
ProcessingRepository, OpenRouterClient, migrations 000005–000015 and queue UI.
Prior investigation: ../x-ingestion/research.md#rich-source-diagnosis--2026-10-18.

- FetchResult carries only text/failure; no media artifacts are persisted.
- XAdapter already bounds archive reads, checks quoted dependencies and uses an
  atomic durable X-attempt guard. Media/Article objects are rejected wholesale.
- Source is saved before assessment reservation. Ledger supports provider costs,
  lease-fenced admission and late generation-ID recording. Unresolved calls
  consume monthly capacity. Retry checks every unresolved job reservation.
- Image extraction is a distinct use case and needs a separate durable slot.
  Existing claim recovery cannot safely repeat an interrupted X read.
- https://docs.x.com/x-api/fundamentals/data-dictionary documents Article text
  and entities, media URLs/types and accessibility alt text. The precise nested
  Article schema is unspecified by the lookup reference; no hosted fixture is
  available. https://docs.x.com/x-api/articles/introduction covers publishing.
- https://openrouter.ai/openai/gpt-4o-mini documents image input, structured
  output and 128k context. Existing enforced provider ceilings are $1/M input,
  $5/M output and $0/request. Reuse those ceilings and disable fallbacks.
- https://openrouter.ai/blog/tutorials/send-image-to-llm/ describes mixed content
  arrays and image_url input. Download images ourselves; send bounded base64
  data URLs so a provider never follows an unvalidated source URL.
- https://pillow.readthedocs.io/en/stable/reference/Image.html documents bounded
  image identification/verification. Pillow is justified for valid-image,
  frame/dimension/decompression checks; image resizing is unnecessary.

Alternatives: unbudgeted OCR violates accounting; omitting images violates the
source contract; local OCR alone cannot read diagram relationships; scraping
private browser endpoints changes the credential/deployment model. Exact API
Article shape and live vision accuracy remain hosted acceptance questions.

## Hosted follow-up — 2026-10-18

Owner confirms migration 000016 applied. Read-only Safari inspection shows the
Supabase migration query reports success, Render lists dd52ffd as deployed, and
existing Render failures at 19:47:09, 19:47:52 and 19:48:07 local time are
`x_article_incomplete / article_body_or_dependencies_missing`. This confirms
Article parsing stops acquisition before image inference. It does not identify
which branch failed or prove X returned only a preview. No new Retry was made.

Official data dictionary still describes Article text/entities, while the lookup
reference does not specify the complete nested body shape. No parser broadening
is justified by the current evidence. Replace the combined diagnostic with fixed
branch names; never log source values, arbitrary field names or credentials.

## Authorized retry and media compatibility — 2026-10-18

User explicitly authorized a retry with “u can run”; the agent clicked Retry
exactly once on the reported Akshay post. Render at 20:48:49 local time returned
`x_article_incomplete / article_media_invalid`, matching the user's earlier
20:48:06 failure. This occurs while parsing Article media, before body completion
or image inference. The earlier UI wording did not prove the body was absent.

The parser rejected every scalar media entry before expansion resolution. A
bounded media-key string can safely normalize to the existing XMedia reference:
only the already returned includes.media can supply its URL/type. No additional
lookup is introduced. The official https://docs.x.com/openapi.json lists the
article.cover_media and article.media_entities expansions but leaves Post.article
an untyped object; it does not establish the failing post's exact media value.
This compatibility fix is tested with synthetic references, not a retained real
payload. If the real rejection is a different media shape, further diagnosis is
still required. No second retry, scraping or private API was used.


## Captured Article compatibility — verified 2026-10-18

Graft remains unavailable; focused source reads used. The user supplied logs,
not a credential or authorization for another live X request. Reassembling four
untruncated response chunks reproduced article_entities_invalid locally.
entities.code contains three code/content/language objects; all snippets are
absent from plain_text. Ten Article media keys are missing from includes.media.
Only the outer post photo is expanded. No fetched fixture content will be
committed; synthetic fixtures preserve the shapes and dependencies.

Repository: parse_article forbids entities.code; _Post.media validates unresolved
keys as unavailable. XAdapter has a 60-second deadline and ten search pages but
no explicit aggregate request counter. OpenRouterImageReader has four-image
input/output guards, one generation/reservation, 8192 output tokens and 128K
conservative input reservation at provider price ceilings $1/$5 per million.
Existing migration 000016 accepts the reservation amount and needs no change.

Official sources read on 2026-10-18:
- https://docs.x.com/x-api/posts/get-post-by-id lists article.cover_media and
  article.media_entities for direct post lookups. Nested Article media expansion
  is not promised for quoted posts. Direct lookup is bounded completion, not a
  retry of a failed request; hosted expansion success remains unverified.
- https://developers.openai.com/api/docs/guides/images-vision documents
  gpt-4.1-mini high-detail patch sizing with a 6144-patch budget and 1.62 multiplier.
  Twelve images need at most 119448 image tokens under that conservative budget;
  fixed system/ID text fits the existing 128K input reservation. gpt-4o-mini uses
  far more tokens per tile, so simply raising its image count is insufficient.
- https://openrouter.ai/openai/gpt-4.1-mini lists image input, structured output,
  1M context and $0.40/$1.60 per million, within existing enforced $1/$5 ceilings.

Alternative multi-call batches would require durable per-batch accounting and
recovery changes. One dedicated image call preserves the existing ledger and
uncertain-outcome fencing. No evidence currently warrants a stronger text
assessment model; the observed failure happens before inference.

## Thread/comment diagnosis — 2026-10-19

Graft is unavailable; focused source/documentation reads were used. The new
owner-supplied payload reproduces partial_content/disconnected_thread offline:
archive search returns nine author replies to other commenters, with the foreign
parent posts present in includes. One reply has an animated GIF without a URL.
These are conversation branches, rather than the author's self-reply thread.
A probe filtering those known comment branches succeeds with the root's two
images and synthetic valid image bytes. The original replay makes three mocked
X requests, no media request, and stops at disconnected_thread.

Separately, known video and animated_gif media without URLs reproduce
x_media_unavailable/missing_article_media_expansion: _Post.media checks URL
absence before validating type. validate_media already rejects both types as
x_media_unsupported. FetchResult failures are handled per job into manual paste;
this result does not terminate the queue loop. No live API request was made.

The existing assessment response includes research source IDs/URLs, criterion
rationales and citations with source IDs. The current Source checking disclosure
shows source links but no per-source analysis notes. No published reader-comment
collection or stored per-source standalone commentary is evidenced.

## Clarified X reply display — 2026-10-19

The owner requests actual replies from X users on the submitted link or X links
found in additional search, and Reddit only if already supported. Focused source
reads show no Reddit integration. Current ordinary fetcher explicitly rejects X
URLs; selected social candidates must be retained separately for optional reply
display rather than misrepresented as fetched comparison evidence. Research JSON
already supports bounded additional metadata; no research SQL signature changes
are necessary. Existing X admission authorizes primary acquisition only and cannot
be reused for independent paid comment requests.

Use separate once-only item/source admission with explicit product consent. Existing
Supabase profile/item owner/expiry guards and cascade conventions apply. Comments
are a display snapshot, not complete source acquisition or assessment evidence.
Official X conversation/search documentation (read 2026-10-19):
https://docs.x.com/x-api/fundamentals/conversation-id and
https://docs.x.com/x-api/posts/search/integrate/build-a-query describe using the
conversation ID to search replies. Lookup resolves the conversation for a submitted
middle post; one bounded search page is explicitly incomplete. No live X request
or credential read is needed for implementation/testing. Graft remains unavailable.
