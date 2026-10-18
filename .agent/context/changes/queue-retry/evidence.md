# Verification — 2026-10-18

- Red: four new queue tests failed because Retry did not exist. The new pgTAP
  suite failed 5 of 15 assertions against migrations 000001–000013, proving that
  fetch failures were not resumable.
- Green: 64 frontend tests pass, including authenticated retry success/error,
  queue refresh, busy disabling and uncertain-X exclusion. Lint and build pass.
- Deliberate break: removing the uncertain-X UI guard caused its test to fail;
  restored the guard and all 14 queue tests pass again.
- PostgreSQL: initialized a fresh temporary PostgreSQL 17 cluster on loopback
  port 55448, with a UTF-8 database and the repository's minimal auth bootstrap.
  Applied all migrations including 000014. The existing processing database gate
  passed all 12 pgTAP files (including 15 new retry assertions), plus concurrent
  budget, duplicate-submission, rubric snapshot, deletion and X-admission checks.
  No hosted database or paid providers were used.
- Relevant Python tests: 19 pass across test_x_processing.py,
  test_processing_service.py and test_duplicate_links.py.
- Required static checks: strict mypy passes (40 source files), Ruff check passes,
  Ruff format check passes (107 files). Used uv with a temporary cache.
- `agent-toolkit check` attempted, exit 127: executable unavailable. The previously
  documented local toolkit interpreter was also absent. Graft unavailable; focused
  repository searches used instead. No tools installed.
- No browser visual inspection or hosted acceptance is claimed. Existing layout
  and native buttons are reused; rollout requires migration 000014 before frontend.
