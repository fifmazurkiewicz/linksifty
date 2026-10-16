# Linksifty vision

## Product promise

Linksifty turns a personal backlog of unread web links into concise, source-grounded notes and a repeatable judgment of what deserves attention. It is domain-agnostic: IT, AI, finance, or any other subject are examples of Filip's interests, not product limits.

The product is not a generic summarizer or an open-ended fact-checker. Its main job is to help Filip decide whether a source is **valuable**, **to review**, or **hype**, using visible evidence and an explainable deterministic rule.

## Primary user and problem

Filip saves more links than he can read. Valuable material becomes mixed with promotional claims, superficial takes, and items that cannot be opened later. He needs a phone-friendly place to submit a small batch, return later, and see which items merit time.

## Personal MVP contract

- Filip signs in with one normal account. Public signup, trials, roles, and administration are deferred.
- The default input is any ordinary web URL. X is a dedicated source adapter using the official X API; all other standard web pages use the generic web fetcher.
- A submission accepts up to five links. Filip can instead choose to paste content immediately.
- Paywalls, login walls, JavaScript-only pages, PDFs, videos, newsletters, partial retrieval, and unsupported pages never produce an assessment. They explain the problem and offer pasted content.
- A completed item has a concise note, eight criterion scores from 1–5 with rationales, supporting source excerpts, a deterministic weighted score, and one verdict: `valuable`, `to_review`, or `hype`.
- The assessment can inspect up to five cited sources. It does not claim research beyond the provided source material and those cited links.
- The inbox opens first. It orders unread items before read items, then by score, and filters by verdict. Each item shows a truthful processing status.
- The item detail includes the note, criteria, source excerpts, and a chat limited to that item's saved source material.
- A user can permanently delete an item. All item content, assessments, citations, and chat history are automatically deleted after 30 days.
- The monthly paid-processing budget has a hard 10 USD cap.

## Assessment and verdict

The eight criteria are novelty, evidence, practicality, source credibility, replicability, independent corroboration, absence of conflict of interest, and concreteness versus superlatives.

By default, evidence, replicability, source credibility, and absence of conflict of interest have weight `×2`; the other four criteria have weight `×1`. Settings shows all eight fixed criteria and lets each account edit descriptions (1–1000 nonblank characters) and integer weights (1–10). All criteria and source citations remain required. The model receives the saved descriptions; pure scoring uses the same reserved weights. The percentage is `sum(points × weight) / (5 × sum(weights)) × 100`, with points from 1–5:

- `≥ 60%`: valuable
- `40–59%`: to review
- `< 40%`: hype

The default valuable threshold is 60%. When Filip changes the threshold, the change applies only to links assessed afterwards. Existing stored scores and verdicts stay unchanged. Threshold, descriptions and weights are captured together at the first model reservation. Interrupted attempts reuse those rules; an explicitly requested fresh analysis takes current settings. The detail view displays the original descriptions and weights. Legacy results retain the original default rubric.

## Success measures

- Twenty real links reach either a completed inbox item or an explicit manual-content request.
- On those twenty links, the verdict matches Filip's own judgment at least 60% of the time.
- Submit, review, filter, mark-read, and delete flows are comfortable on a phone.

## Operating constraints

- The static frontend is deployed on Vercel; the FastAPI API runs on Render Free.
- A Render cold start after idle time is acceptable. There is no paid always-on worker.
- Job state is persisted in Supabase. The API executes queued work while it is awake; interrupted work remains queued and resumes on a later application visit.
- Supabase Free is acceptable, including its low-activity project pausing behavior.

## Non-goals

- Public signup, pending-user trials, account approval, admin views, and social sharing.
- Bookmark import, Telegram, topic categorization, manual verdict override, automatic reassessment, and bring-your-own-key.
- Automatic fetching for video, podcasts, PDFs, newsletters, Reddit, or any blocked/unsupported page.
- Full-text inbox search, a dedicated analytics platform, a paid background worker, and System One/Jev classification.
