# Inline chat references — 2026-10-21

Bounded frontend presentation change requested by the owner: numbered references
beside cited answer paragraphs and unique source links underneath each answer.

- Number sources by first appearance within an answer; reuse the number for the
  same URL and collapse duplicate markers in one paragraph.
- Group exact quoted passages under each source with native details disclosure;
  preserve distinct excerpts and saved-analysis evidence without URLs.
- Native fragment links point to focusable source entries. useId separates
  destinations across answers; preserve focus tokens, safe URL checks, wrapping,
  and existing pending/error/refusal behavior.
- Existing API/model output remains unchanged. No migration, paid request or new
  dependency. Citation placement uses the existing paragraph-level provenance;
  it does not invent sentence-level quote offsets.
- Red: four focused frontend regressions fail against the previous layout.
  Green: all ten chat tests and frontend lint/build pass after implementation.
- Full checks: 93 frontend tests, lint/build, backend strict mypy and Ruff
  lint/format pass. agent-toolkit remains unavailable (exit 127).
- Deliberately changed grouping from source URL to passage ID: the repeated-source
  regression fails; restored source and all ten focused chat tests pass.
- Native browser QA on synthetic data confirms inline references, unique links,
  Enter-to-source focus and keyboard passage disclosure. Screenshot retained in
  qa/desktop.jpg. A fixed mobile viewport was not tested.
- Independent reviewer approves with no actionable findings; independently reran
  ten focused chat tests, frontend lint and scoped whitespace checks.
- Local implementation complete. Temporary synthetic preview files/server were
  removed/stopped. Hosted deployment is not verified by the local checks.

Graft is unavailable; used focused documentation/source reads. Existing unrelated
admin/README/App changes are preserved; App.css is shared with one prior admin
badge rule. No new architecture or complex flow requires a diagram.

Publication: owner explicitly authorized push to main. Fresh origin/main matches
the reviewed base 3f945d5. Only citation layout code, its CSS hunk, tests,
documentation and verification records are selected; admin edits remain local.
