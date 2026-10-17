# Informative summaries

2026-10-18: User requested topic basics and why they matter in the Summary.
Approved the bounded design with the refinement that structure should flow
naturally depending on the topic, theme and article.

## Scope and decisions

- Generate a self-contained explanation of the primary source's topic, concrete
  facts and practical relevance. Explain unfamiliar terms when the source allows.
- Adapt length and structure to the material. Fluent paragraphs are welcome;
  bullets or short sections are optional, with no mandatory headings or padding.
- Keep opinion/forecast attribution and important conditions/dates/uncertainties.
  Do not invent missing background, benefits, current figures or personalized advice.
- Keep rubric judgments in the criterion explanations, rather than filling the
  summary with generic statements about source quality.
- Reuse the existing `note` field and the existing single, bounded model request
  for both rubric versions. Preserve historical saved/cached text and scoring.
- No schema migration, new endpoint, model dependency, automatic regeneration or
  paid validation request. This changes future generated results after deployment.

## Execution

| Task | Status | Evidence |
| --- | --- | --- |
| T1 Request contract and storage checks | Done | Four request cases failed before implementation; 30 focused tests pass; service completion checks multiline summary preservation |
| T2 Generation guidance and product docs | Done | Shared source-grounded guidance across rubric versions; existing note field, token/price caps and single call retained |
| T3 Verification and review | Done locally | 30 relevant mocked tests, strict mypy, Ruff lint/format and whitespace checks pass; deliberate removal fails all four request cases; implementation review approves |

Graft is unavailable; focused source and existing documentation supplied context.
Tests verify the request contract and text preservation, not live model quality.

Implementation is complete locally. Required toolkit verification is unavailable;
no live model sample, deployment or automatic reassessment was performed.
See [evidence](evidence.md) and [implementation review](reviews/implementation-review.md).

2026-10-18: User explicitly requested pushing this change to `main`. Pre-push
tests (30), strict mypy, Ruff lint/format and whitespace checks passed again.
Fetched `origin/main` matches local HEAD before the implementation commit.
Toolkit remains unavailable; no live model call or automatic reassessment is included.
