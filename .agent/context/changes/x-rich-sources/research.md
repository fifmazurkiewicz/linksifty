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
