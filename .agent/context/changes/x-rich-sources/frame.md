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


## Captured Article compatibility follow-up

Owner-supplied logs at 2026-10-18 20:11:52 UTC show a successful post lookup,
followed by article_entities_invalid. The quoted Article has 6,831 characters
of plain_text and three entities.code snippets absent from that text, ten Article
media references with no matching includes.media (only the outer post image).
Current download and vision schemas both cap images at four. Success requires
retaining code, resolving quoted Article media, and processing eleven total
images without omitting sources, bypassing budgets or adding automatic retries.
The owner approved the bounded design, including a dedicated image model and
up to twelve images, then asked whether assessment needs a stronger LLM.


## Hosted image-reading failure — 2026-10-19

Owner reports image_reading_failed after the thread fix. Screenshot and supplied
08:54:33–08:54:58 UTC logs concern post 2111867588405862713. X lookup/search
return successfully with two photo dependencies; the comment-branch GIF is not
a required primary image. The application reaches image reading and a known-cost
failure; the existing parser discards its exact rejection cause. Logs contain no
OpenRouter response or rejection check. Model output/finish/coverage/legibility
remain competing explanations; none is established as this attempt's root cause.

Public CDN inspection finds the first bare image URL serves 849×1200, while the
same URL with name=orig serves 1055×1491, matching API dimensions. Fine text is
dense. Prefer original bytes under existing bounds, and expose safe fixed
rejection checks before proposing another model or weakening source completeness.
This improves input quality but does not prove resolution caused the failure.


## Owner-directed text-only scope — 2026-10-19

New logs establish T7: two-image reading ends with finish_length (truncated
model output), while the Wooden video is explicitly unsupported. The owner now
asks to omit images/videos/GIFs and analyze text, with visible media availability.
This intentionally supersedes the earlier requirement that every media artifact
be read before assessment. Text completeness, owner isolation, explicit paid
reads and uncertain-charge fencing remain required. Success is complete readable
text analysis with durable honest scope, zero media downloads/vision calls and
manual fallback for short/truncated/missing text, including media-only posts.
