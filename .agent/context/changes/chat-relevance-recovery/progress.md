# Chat relevance recovery — 2026-10-21

Bounded repair of the existing chat flow, prompted by repeated failed questions
and the owner's instruction to search for missing facts. Canonical execution record.

- Diagnosis: the supplied trace chooses relevant with probability 0.86 but
  normalized confidence 0.79. The confidence cutoff of 0.8 rejects it. Classifier
  analysis input starts with rubric metadata and can omit the useful summary.
- Decision: use selected-choice probability >=0.8 for the existing scope gate;
  validate every distribution and language result as before. This intentionally
  supersedes the original provisional normalized-confidence cutoff. Official
  TypeSafe documentation distinguishes both measures; see evidence.md.
- Valid lower-probability choices return fixed PL/EN clarification; they never
  admit answer/search. Invalid responses and provider failures remain failures.
- Supply the saved summary directly to classification. Preserve full rubric
  passages for answering score questions; avoid duplicating the summary in the
  answer payload. Clear subjects lacking factual evidence must request available
  search, bounded by existing consent, budgets and two-search admission.
- Preserve generation/cost settlement, owner scope, once-only execution and
  failed historical rows. Show a specific explanation for historical uncertainty.
- Tests written first: reproduced metadata displacement and blocked research
  using the screenshot's exact distribution. Implementation complete locally.
- Required available gates pass: 595 backend tests, strict mypy, Ruff lint/format;
  91 frontend tests, lint/build. Deliberate confidence-gate regression fails the
  replay, then restored implementation passes all 93 focused tests.
- Independent reviewer approves, no actionable findings; independently reran
  93 focused tests. No review dispositions or derived board needed.
- Archify source/HTML updated: validation, delivery and strict artifact checks
  pass. Browser check is skipped because Chrome is unavailable; no visual review
  claimed. agent-toolkit check is unavailable (exit 127).

No migration, dependency, hosted write, paid inference or deployment. Existing
admin/README edits are unrelated and preserved. Graft is unavailable; focused
source searches used. This is a maintenance repair, with no new milestone/plan.

Release: owner explicitly authorized push to main. Fetched origin/main matches
the reviewed base; only this chat change is selected for publication. Generated
diagram bytes are preserved with their validated artifact hash.
