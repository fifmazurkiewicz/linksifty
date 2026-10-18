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
  100 unique author posts; 100 KB final UTF-8 text and 1 MB response bodies.
- Full archive search is required: never silently substitute a seven-day search.
- Parent-linked author posts ordered from root, each with its own canonical URL.
  A missing parent, missing selected post, partial API error, missing long text,
  multimedia, quote/repost dependency or X Article requests manual paste.
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
