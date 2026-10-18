# Complete rich X sources

2026-10-18. Owner explicitly requests implementation after diagnosis of the same
submitted post failing first reference handling, then `attachments_present`.
The post has text-bearing imagery and a quoted X Article. Ordinary quote/repost
handling is already implemented; neither image acquisition nor full Article
parsing is implemented. The current pipeline is text-only.

Success: obtain complete supplied Article bodies and required images, extract
readable image text/diagram observations under the user's existing monthly
budget, cache complete text before assessment, and expose meaningful failure
reasons. Partial or uncertain acquisition must never produce an assessment.

Preserve owner/lease/account/expiry guards, explicit X operator opt-in, provider
credential isolation and interrupted-call fencing. Mock all paid integrations.
No video/audio ingestion, browser-session scraping or new external service.
Exact hosted Article body shape remains unverified; absent body is a manual
fallback rather than an invented or title-only source.
