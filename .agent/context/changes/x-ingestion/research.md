# Verified context

- Current X URLs are rejected in infrastructure/http_fetcher.py. main.py injects
  that fetcher into ProcessingService for primary and additional sources.
- ProcessingService saves only complete content, then reserves model spend.
  Existing SQL job writes require owner and current lease. Credentials are
  server-only and redacted from telemetry.
- Official docs checked 2026-10-18:
  https://docs.x.com/x-api/posts/get-post-by-id and
  https://docs.x.com/x-api/posts/search-all-posts document fixed api.x.com
  /2/tweets endpoints. The reference uses renamed post.fields/note_post while
  https://docs.x.com/x-api/posts/lookup/quickstart and its SDK examples still
  document tweet.fields. Use those established wire names, explicitly requesting
  author_id, conversation_id, note_tweet and referenced_tweets; no expansions
  or extra included resources are needed. Accept note_post/referenced_posts
  response aliases, without retrying a rejected request under another dialect.
  https://docs.x.com/x-api/posts/search/integrate/build-a-query describes
  conversation_id and from operators. Full archive pagination is bounded.
- No real provider calls or credentials were used. Graft runtime unavailable.

## Reference support follow-up — 2026-10-18

The original no-expansion choice above is superseded for quote/repost support.
Owner-provided hosted logs identify `unsupported_references`; the guard rejects
quotes/reposts and multiple references without inspecting their type separately.

Official [expansions documentation](https://docs.x.com/x-api/fundamentals/expansions)
documents `referenced_tweets.id`, related objects in `includes`, and combining
expansions with requested fields. The [lookup reference](https://docs.x.com/x-api/posts/get-post-by-id)
also shows renamed `referenced_posts`, `includes.posts` and type `retweeted`.
Use the established wire parameter from the expansion guide, accept both payload
dialects and require complete expanded dependencies. No undocumented scraping,
follow-up lookup of missing context or live paid experiment is needed.

## Rich-source diagnosis — 2026-10-18

Observations (no implementation decision or additional paid request):

- Owner's latest Render log changes the failing check to `attachments_present`.
  The X usage screenshot shows four reads and USD 0.01 total, without proving
  that all four reads belong to this item or that the acquired source is complete.
- Inspected the submitted post in the owner's Safari session. It contains a
  text-bearing screenshot/diagram and quotes an X Article; the visible Article
  card is a truncated preview. This inspection did not use the billed API.
- `_Post.content` rejects any nonempty attachments object and any non-null
  article object before extracting text. The current provider-independent
  FetchResult and assessment passage pipeline carry text only; no image content
  or OCR/vision acquisition is implemented. Source is saved before model spend
  is reserved, so adding paid extraction requires explicit accounting design.
- Official [data dictionary](https://docs.x.com/x-api/fundamentals/data-dictionary)
  says the `article` field can provide Article text and entities. The
  [lookup reference](https://docs.x.com/x-api/posts/get-post-by-id) leaves its
  nested object schema unspecified. The exact full-body shape/completeness and
  nested-media handling for this Article remain unverified; metadata/preview
  alone must not be promoted to complete source.
- Official media docs describe image URLs, type and alt text through expansions.
  Alt text is an accessibility description and cannot be assumed to transcribe
  the image completely. Full image/diagram ingestion is a separate missing
  capability; external text-only or manual complete source remain alternatives.
- The [Articles endpoints guide](https://docs.x.com/x-api/articles/introduction)
  documents draft creation and publication, not an independently documented
  full-body GET endpoint. This does not establish that Article text is absent
  from post lookup; the data dictionary explicitly mentions it.

Unknowns: actual article/body payload shape, media types/availability in the
selected and quoted sources, and an approved acquisition/accounting approach
for complete rich sources. No guard was weakened and no retry was triggered.
