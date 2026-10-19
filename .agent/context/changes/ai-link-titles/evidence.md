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
- Diagram validation and final review are tracked in progress.md.
