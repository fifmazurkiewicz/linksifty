# Verification evidence

- RED: 10 backend title regressions failed before implementation (missing schema
  field, provider method, service/API and reservation contract).
- RED: all three queue regressions failed before implementation (missing clickable
  sources and confirmed title action).
- GREEN: all 10 backend title regressions pass. Initial frontend check exposed
  missing test cleanup; corrected to match existing test conventions.
- Final backend suite: 493 passed. Strict mypy: 50 source files passed.
  Ruff check and format check pass (129 files). Frontend: 86 tests passed;
  lint and production build pass. The existing Starlette/httpx deprecation
  warning is unrelated to this change.
- Deliberate break: suppressed model title assignment; both valid/invalid
  assessment title regressions failed. Restored implementation in `finally`
  before the full green run.
- Installed PostgreSQL 17/pgTAP was used in a dedicated temporary cluster at
  loopback 55462, with synthetic auth and database `linksifty_titles_test`.
  All 20 migrations applied. The 17 SQL suites pass, including 25 new title
  assertions. Existing concurrency gates plus new title duplicate-admission
  and shared-budget races pass. No hosted data or paid provider was accessed.
- Database tests caught and drove fixes for SQL NULL handling when preserving a
  meaningful title on pasted items, and a missing RETURNING clause in the title
  write RPC. The complete SQL gate passes with both fixes.
- `agent-toolkit check`: exit 127, command unavailable. Graft is unavailable.
  Neither tool was installed; required toolkit verification remains an operator
  limitation and is not reported as passed.
- Exact staged frontend (excluding unrelated admin edits): all 83 tests and the
  production build pass in `/private/tmp/linksifty-title-staged`.
- Final migration replay: a second fresh `linksifty_titles_replay_test` database
  applied all 20 migrations verbatim, then passed the full SQL/concurrency gate.
- Archify workflow JSON and HTML are retained. Schema validation, delivery and
  strict artifact checks pass. `finalize` exits 2 at browser-check because
  Chrome/Chromium is unavailable; no browser or perceptual pass is claimed.
  The current summary receipt is `titles-workflow.finalize-summary.json`.
  Sources pin implementation commit `ca29e438f693d07c77ddf6d97d48095c889988a0`;
  all cited source files are clean. Unrelated dirty frontend/admin paths remain
  outside the feature commit. The first unavailable browser receipt is retained
  under `diagnostics/`; an evidence-path collision was resolved by moving that
  earlier receipt aside before the final delivery.
- `git diff --check` passes after removing an extra documentation EOF blank line.
  The final whitespace check excludes only renderer-produced workflow HTML,
  whose whitespace is preserved to keep validated artifact hashes intact.
- Implementation review: [reviews/implementation-review.md](reviews/implementation-review.md).
