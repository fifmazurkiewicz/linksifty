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
- A completed item has a concise note, eight explained criteria, scored 1–5 where verifiable, with explicit unscored states, supporting source excerpts, a deterministic weighted score, and one verdict: `valuable`, `to_review`, or `hype`.
- With opt-in source checking, the assessment can inspect the submitted source and bounded excerpts from up to 20 additional pages. It does not claim research beyond the provided source material and those cited links.
- The inbox opens first. It orders unread items before read items, then by score, and filters by verdict. Each item shows a truthful processing status.
- The item detail includes the note, criteria, source excerpts, and a chat limited to that item's saved source material.
- A user can permanently delete an item. All item content, assessments, citations, and chat history are automatically deleted after 30 days.
- The monthly paid-processing budget has a hard 10 USD cap.

## Assessment and verdict

The reading view leads with the saved article title and source, a compact verdict
and score, and a prominent Summary containing the saved assessment note. Analysis
and Source checking are independently expandable and initially closed. Their
headers retain criterion coverage and research status; fetched pages alone never
mean verified claims. Criterion explanations precede expandable exact quotations
and saved scoring rules. Hype warnings remain visible above the disclosures.
The layout uses the existing light/dark palette and native keyboard controls.
Sidebar budget details are expandable, with available funds and reservations
visible in the collapsed summary. This presentation does not regenerate notes
or recalculate saved assessments.

For new model calls, the summary teaches the topic basics, concrete facts or
arguments and why they matter. It explains unfamiliar terms when supported by
the supplied primary source, preserves meaningful conditions/dates and attributes
opinions or forecasts. Its length and structure follow the article: fluent
paragraphs, optional short sections or bullets, with no mandatory template.
Substantive articles generally merit about 150–250 words; thin material must not
be padded with invented background. Rubric judgments belong in the criterion
explanations. The same bounded model call produces the summary and assessment;
the existing `note` field and 6000-character ceiling are retained. Saved/cached
notes remain historical until an explicitly authorized fresh analysis.

The eight stable criterion IDs now represent learning value, support for claims,
usefulness, topic-specific credibility, replicability, cross-source confirmation,
fair presentation and interests, and specificity/completeness for the material's
purpose. Established information can teach the reader; an official explainer is
not expected to supply an investment strategy. Source authority is topic-specific,
not an automatic perfect score. Evidence and completeness include currency where
it matters. No personal knowledge profile is inferred.

Version 2 descriptions define anchors: 1 identifies a substantive weakness,
3 means partial fulfilment with named gaps, and 5 means strong fulfilment for
the purpose. Scores 2 and 4 are intermediate. Positive reasoning must explain
any low score. All eight criteria receive an explanation and an inspected source
passage. `assessed` requires integer points 1–5. `not_verified` has null points
and means missing verification, not a negative judgment. `not_applicable` also
has null points and is allowed only for replicability when the material claims
no reproducible method or result. Missing disclosure alone does not prove a
conflict. Cross-source confirmation compares specific claims; additional URLs
alone and differences in detail do not establish corroboration or contradiction.

Default weights stay 2 for support, credibility, replicability and interests,
and 1 for the other four. Settings permits descriptions of 1–1000 nonblank
characters and integer weights 1–10. The percentage is
`sum(points × weight) / (5 × sum(weights of scored criteria)) × 100`.
Unscored criteria are excluded; no scored criteria means a null percentage.
Detail displays coverage and explains that the percentage is not a probability
of truth.

Version 2 verdicts are deterministic:

- `hype`: at least one explicit, explained primary-source passage demonstrating
  an exaggerated promise, sensational claim or conclusion beyond the evidence.
  Low score, lack of novelty or missing verification alone never imply hype.
- `valuable`: no hype signals, percentage at or above the saved threshold (60%
  by default), and support, credibility, usefulness and completeness each scored
  at least 3. Unknown or weak key criteria require review even with a high total.
- `to_review`: every other case. Missing corroboration alone does not disqualify
  otherwise sufficiently supported useful material.

Threshold, descriptions, weights and rubric version are captured together at
model reservation. Missing version means historical version 1, with the original
all-scored formula and below-40% hype rule. Completed and reserved analyses are
not rewritten or recalculated by migration 000010. Future settings move to v2;
only default descriptions are replaced, preserving custom descriptions and all
weights. Explicit fresh analysis uses current settings and existing paid-call
approval/budget semantics.

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
