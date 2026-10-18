# Verification — 2026-10-18

- Red: adapter tests initially failed collection because XAdapter did not exist.
  Five processing cases then failed without X routing and durable admission.
- Green: 53 focused adapter/runtime/processing cases pass; final complete backend
  suite has 285 passing tests. The existing Starlette/httpx deprecation warning
  remains unrelated. Mocked integrations only; no credentials were read.
- Mutation: temporarily bypassed begin_x_fetch in the application service. Both
  protected attempt/failure cases failed. Restored the guard and reran green.
- Runtime test uses the real app lifespan, repository adapter and X adapter with
  HTTPX MockTransport. Enabled X reaches official lookup/search and saves text;
  disabled X consumes no attempt and issues no X request. X credentials never
  appear on Supabase requests and Supabase credentials never appear on X reads.
- Adapter cases cover long text and legacy response aliases, page ordering,
  bounded pagination, URL variants, invalid URLs, response/source byte bounds,
  timeout, redirects, partial/malformed lookup/search, wrong author/conversation,
  missing parents/cycles, short text, 401/402/403/404/429/500 and search-access
  failure without a recent-search downgrade. The request uses the established
  tweet.fields wire contract from X's official lookup quickstart (see research).
- Strict mypy passes for 40 source files. Ruff passes for all X-touched Python
  files. git diff --check passes. Full Ruff/format were attempted; concurrent
  chat work changed during verification. Transient broad failures came from concurrent
  chat edits outside this change. After that work settled, the final full
  repository Ruff lint and format checks pass (107 files formatted). No chat
  source was modified by the X implementation.
- Frontend: 57 tests pass, including five X fallback/click cases; lint and build
  pass. Existing queue keyboard/button behavior is reused.
- Local real PostgreSQL 17: created an isolated cluster at
  /private/tmp/linksifty-x-pg, loopback port 55441, database linksifty_x_test,
  synthetic role linksifty_test_runner. Applied repository migrations including
  000012 there only. Eleven SQL suites pass, including ten X assertions proving
  owner isolation, lease fencing, one attempt, crash recovery and browser denial.
  Six concurrency gates pass; simultaneous X admissions admit exactly one.
  Fixed a nondeterministic test fixture by creating the second queued job only
  after reclaiming the interrupted first job. Cluster stopped after verification.
- English contract diagram x-workflow.json/html: Archify validate, deliver and
  strict artifact check pass. Browser gate skipped because Chrome/Chromium is
  unavailable; no perceptual review or repository-snapshot provenance claimed.
- agent-toolkit check attempted: command not found (127). Graft unavailable.
- No live X access, hosted migration, invoice reconciliation or deployment claimed.

Commands use UV_CACHE_DIR=/private/tmp/linksifty-uv-cache and uv run --no-sync
--package linksifty against the existing environment; no dependency changes.
Database gate: backend/tests/integration/check_processing_database.py with the
explicit disposable LINKSIFTY_TEST_DATABASE_URL. Frontend checks run in frontend/.
