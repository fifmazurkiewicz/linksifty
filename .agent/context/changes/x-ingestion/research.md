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
