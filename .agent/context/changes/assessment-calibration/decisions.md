# Decisions
- Keep eight stable criterion IDs and weights; new descriptions include 1/3/5 anchors, freshness, purpose-relative utility and learning value. No assumed personal knowledge.
- Version rubric data: absent version = legacy v1; default future settings = v2. Migrate only old default descriptions, preserve custom descriptions/weights. Do not rewrite reserved jobs or assessments.
- assessed requires score 1–5; not_applicable only for replicability; not_verified denotes uncertainty. Both unscored states have null score and are excluded from denominator. Empty denominator -> null percentage / to_review.
- v2 hype requires at least one primary-source passage plus rationale identifying exaggeration or unsupported promises. Otherwise low score -> to_review. Missing/low (1–2) evidence, credibility, usefulness or concreteness prevents valuable; missing corroboration alone does not. v1 recovery retains old formula and guards.
- Hype citations are separate from eight metrics, checked with same exact-offset fences. URL metadata provided to model, never trusted as instructions or automatic 5/5.
- Up to 20 candidates/fetches; keep deduplication and one search charge. Bound each stored additional excerpt and aggregate prompt bytes. Never truncate the primary source; reject oversized prompts before HTTP. No Reddit/X adapters or crawling introduced.
- Local implementation authorized in chat. Hosted migration/deployment, paid calibration and live reassessment remain separate external actions.
