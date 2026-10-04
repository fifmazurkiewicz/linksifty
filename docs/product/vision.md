# Linksifty vision

## Product promise

Linksifty turns an unread backlog of articles and X posts into short, source-grounded notes and a repeatable judgement of what deserves attention. It separates evidence from hype through an explicit assessment and deterministic verdict.

## Primary user and problem

The primary user saves more IT/AI and finance links than they can read. Links are scattered across devices and feeds, so valuable material gets buried beside promotional claims. The product must let that user submit up to five links, return later, and see a clear inbox rather than another research task.

## MVP contract

- Authenticated users submit up to five links; each becomes a separate item.
- Articles and individual X posts are fetched. A failed, partial, paywalled, or inaccessible fetch stops and requests pasted content; it never invents a note.
- Each completed item has a concise source-grounded note and eight 1–5 assessments: novelty, evidence, practicality, source credibility, replicability, independent corroboration, absence of conflict of interest, and concreteness.
- Evidence, replicability, source credibility, and absence of conflict of interest receive double weight. The pure score determines `valuable`, `to_review`, or `hype`; the default valuable threshold is 60% and users can change it.
- The inbox is responsive, ordered by unread then score, and supports verdict filtering, read state, deletion, and per-item chat.
- Accounts start pending. Admins approve or reject accounts, but cannot see other users’ items. Pending users have only the agreed bounded trial allowance.
- Processing is capped at 10 USD per user per month and stops clearly at the limit.

## Success measures

- Twenty real backlog links each reach a completed inbox item or an explicit manual-content request.
- On a twenty-link sample, the verdict matches the primary user's judgement at least 60% of the time.
- The core submit, review, filter, and read flow is comfortable on a phone.

## Non-goals

No bookmark import, Telegram bot, public sharing, BYOK, automatic re-assessment, manual verdict override, topic categorization, Reddit fetching, video/podcast/PDF/newsletter fetching, or deep research beyond the submitted content and up to 20 referenced links.

## Delivery boundary

The MVP deadline is 2026-11-04. If the schedule must be reduced, referenced-link analysis and per-item chat are the first candidates to defer; this does not change the current committed scope.
