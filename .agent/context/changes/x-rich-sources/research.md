# Verified research — 2026-10-18

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
