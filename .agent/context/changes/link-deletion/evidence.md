# Verification — 2026-10-17

- Red: 14 API/repository cases failed before the route and batch operation
  existed. Three UI cases failed on missing controls. SQL cases failed against
  the prior schema's missing deletion function.
- Green: full backend suite 202 passed; frontend suite 39 passed. Existing
  TestClient deprecation warning remains unrelated.
- Strict mypy passed (34 source files); Ruff lint/format, frontend lint/build,
  and application source diff checks passed.
- Real SQL: nine pgTAP suites passed, including 30 deletion assertions. Five
  concurrency checks passed: budget admission, duplicate submission, atomic
  rubric snapshot, deletion/reservation and deletion/late-result persistence.
- The disposable PostgreSQL 17 cluster is `/private/tmp/linksifty-calibration-pg`,
  loopback port 55440, database `linksifty_calibration_test`, synthetic role
  `linksifty_test_runner`. Migration 000011 was applied only there.
- SQL mutation: within a rolled-back transaction, replaced the confirmation
  condition with false. The explicit-confirmation regression failed as expected.
  The complete original SQL suite passed again afterward.
- UI tests cover cancel/confirm, active links, visible-only selection, filter
  resets, retained selection on failure, disabled mutations, authenticated
  API payload, server-confirmed removal and stale-snapshot suppression.
- Workflow source pinned to implementation commit
  `97dc92f6f87c2177d058b7530f2f6ce9e7e1b282`. Corrected an out-of-range source
  reference and reduced automatic node width to satisfy readability. Final
  validation, delivery and strict artifact checks pass. Browser check skipped:
  Chrome/Chromium unavailable; no perceptual or live browser QA claimed.
- Generated workflow HTML retains 15 whitespace-only renderer lines to preserve
  its validation/hash receipts. The staged whitespace check reports those
  artifact lines; application source and documentation checks pass.
- `agent-toolkit check` attempted: exit 127, command not found. Graft unavailable.
- No provider calls, hosted migrations or production content deletions performed.
- Implementation commit `97dc92f6f87c2177d058b7530f2f6ce9e7e1b282` pushed to
  `origin/main`; Git reported `2ab3816..97dc92f main -> main`.

SQL command:
`PATH=/opt/homebrew/opt/postgresql@17/bin:$PATH UV_CACHE_DIR=/private/tmp/linksifty-uv-cache LINKSIFTY_TEST_DATABASE_URL=postgresql://linksifty_test_runner@127.0.0.1:55440/linksifty_calibration_test uv run --package linksifty python backend/tests/integration/check_processing_database.py`
