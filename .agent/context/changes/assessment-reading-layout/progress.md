# Assessment reading layout

2026-10-17: User approved the in-chat design with “lets do it”. This bounded
change follows the existing assessment flow and preserves saved assessments.

## Approved scope and decisions

- Show the saved article title/source and a compact verdict, then a prominent
  summary with a comfortable reading width.
- Use independent native disclosures for Analysis and Source checking, closed
  initially. Keep coverage and research status visible in their summaries.
- Lead each criterion with its explanation. Reveal exact source evidence inline;
  keep historical rubric descriptions and weights under Scoring rules.
- Preserve unscored/legacy states, hype evidence, source-checking uncertainty,
  safe external links, loading/error states, and existing light/dark tokens.
- Compact sidebar usage into an expandable budget summary so content is easier
  to reach on mobile. Keep the detailed budget on administrative screens.
- No new dependencies, paid analysis, score recalculation, or API/schema change.
  The saved note remains the summary content; factual takeaways need a later
  generation change. Native disclosures avoid custom interaction state.

## Acceptance and execution

| Task | Status | Acceptance / evidence |
| --- | --- | --- |
| T1 Behavior checks | Done | Initial red: 8 assessment failures and 1 budget failure; green suite: 47 tests; deliberate open-by-default mutation caused 2 failures |
| T2 Reading layout | Done | Summary hierarchy, responsive width, native keyboard controls, safe links and budget disclosure implemented |
| T3 Verification and review | Done locally | 47 frontend tests, lint/build, mypy/Ruff and desktop/mobile/light/dark checks pass; implementation review approves; toolkit executable and module unavailable |

Graft is unavailable; focused repository and documentation searches were used.
Canonical execution record: this file. Verification: [evidence.md](evidence.md).

Local implementation is complete. Required toolkit verification remains
unavailable; no deployment or paid reassessment was performed. Review:
[implementation-review.md](reviews/implementation-review.md).

2026-10-18: User explicitly requested pushing this change directly to `main`.
Pre-push frontend tests/lint/build, strict mypy and Ruff checks pass again;
`agent-toolkit` remains unavailable. Fetched `origin/main` matches local HEAD
before the implementation commit. Email login was cancelled; authentication
changes are outside this release.
