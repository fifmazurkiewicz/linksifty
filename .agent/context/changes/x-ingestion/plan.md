# X ingestion implementation

## Intent and design

Submitting a public X post, including a post within a thread, acquires the
author's connected thread through official X API v2. Reuse HTTPX, FetchResult,
the existing completeness check and owner-scoped source/assessment persistence.
No new dependency, scraper, worker, or model call on incomplete content.

1. Add bounded lookup and paginated full-archive search, long-post text, strict
   post identity/author/conversation/parent validation, and explicit failures.
2. Wire only primary X acquisition to the adapter. Additional-source discovery
   retains the ordinary fetcher and cannot trigger X charges. Add a server-only,
   lease/owner-scoped atomic one-attempt marker before X requests. Existing cached
   source content is reused. A crashed attempt requests paste, never auto-retries.
3. Explain X-specific fallback states in the existing queue. Explicit operator
   approval is X_API_READS_ENABLED=true plus the server-only token. X billing
   remains in the operator's X account, separate from the model/Brave ledger;
   document this clearly. No token alone activates billing.
4. Update setup, roadmap and derived boards, plus an English editable workflow
   diagram. Run mocked adapter/orchestration/SQL/UI tests and required checks.

## Acceptance and limits

- x.com/twitter.com normal, www/mobile and /i/web/status URLs supported; numeric
  IDs only, no credentials or custom ports; tokens sent only to api.x.com.
- One selected lookup, optional root lookup, at most ten search pages, at most
  100 unique posts including expanded context; 100 KB final UTF-8 text and 1 MB response bodies.
- Full archive search is required: never silently substitute a seven-day search.
- Parent-linked author posts ordered from root, each with its own canonical URL.
  A missing parent, missing selected post, partial API error, missing long text,
  multimedia, unavailable quote/repost dependency or X Article requests manual paste.
- Completeness means all accessible matching results returned by X pagination;
  X cannot prove the existence of hidden/deleted descendants. No completeness
  claim about undisclosed content or future additions.
- Mock 401/402/403/404/429/5xx, malformed/partial responses, redirects, limits,
  long text, thread order/pagination/gaps, credential isolation, crash recovery,
  cross-owner/stale-lease attempts and model-not-called failures.

## Trade-offs

Full-archive reads avoid silently omitting old thread posts, but require that
endpoint's access and may incur operator charges. Bounded failures request a
paste instead of producing a misleading partial assessment. A durable attempt
marker may require paste even when a process crashed before sending its first
request; this conservative behavior avoids duplicate charges.

## Reference handling fix — 2026-10-18

Observed hosted blocker: `unsupported_references`. The initial adapter rejected
every quote/repost and any multi-reference reply. Resolve text dependencies via
`expansions=referenced_tweets.id` on the existing lookup/search requests. Accept
`includes.tweets` and `includes.posts`. Preserve the existing wire dialect without
retrying another parameter spelling after rejection.

- Separate `replied_to` parent selection from `quoted`/`retweeted` dependencies.
  Allow one reply parent plus one quote; reject duplicate/unknown reference types
  and reposts combined with another relation.
- Resolve a submitted repost to its expanded original before selecting the
  conversation root/author. Use original text/thread, never the RT preview.
- Require each referenced post and recursively needed context to be present and
  complete. Include canonical URLs, author IDs and explicit reference links;
  deduplicate sources and reject cycles/conflicting versions. Quoted context is
  the expanded post/context, not an independently searched second author's thread.
- Keep at most two lookups and ten archive pages. No extra HTTP calls, automatic
  retry or network fallback for missing expanded posts. Expanded posts may incur
  additional resource-based X charges; operator opt-in and explicit Retry remain.
- Count all collected thread/context posts toward 100, and retain the response,
  source-size and time limits. Only actual source text counts toward the minimum.
- Mock successful quotes, quoting replies, reposts, nested/deduplicated context,
  missing/partial dependencies, cycles, version changes and size/count guards.
  Update canonical docs/diagram and run required verification before publication.
