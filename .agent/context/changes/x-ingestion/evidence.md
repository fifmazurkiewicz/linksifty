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
# Render diagnostics follow-up — 2026-10-18

- Red: 18 focused cases failed on missing diagnostic records before implementation
  (14 status/endpoint cases, two exception cases, two existing processing cases
  extended with job-level log assertions). An initially invalid fixture username
  was corrected before confirming failures at the logging assertions.
- Green: 69 focused X adapter/processing cases pass. Tests cover both endpoint
  labels, HTTP 400/401/402/403/404/429/500, transport/JSON exception types,
  job correlation, no automatic repeat, no model assessment on failed reads and
  exclusion of fixture credentials, source text, headers, payloads and URLs.
- Deliberate break: temporarily changed the HTTP rejection warning to debug;
  all 14 endpoint/status cases failed. Restored warning level before final checks.
- Full backend suite: 325 pass, with an existing Starlette/httpx deprecation warning.
- Strict mypy: 40 source files pass. Repository Ruff lint and format checks pass
  (108 files). `git diff --check` passes.
- Default-logging smoke check: a mocked 403 emits
  `x_api_request_failed endpoint=post_lookup status=403` to terminal output with
  no logging setup, demonstrating warning visibility without a debug flag.
- `agent-toolkit check`: unavailable (exit 127, command not found). Graft MCP
  unavailable; used focused repository reads. No tools installed.
- No frontend, migration, paid request, deployment or hosted validation performed.
  Render diagnosis requires backend deployment and a new explicitly requested
  attempt; prior failures cannot produce logs retroactively.

## Completeness diagnostics follow-up — 2026-10-18

- Hosted logs supplied by the owner show the first diagnostics build running,
  but only the job-level `partial_content` reason. No HTTP-status or parse warning
  accompanies it. Exact failing content check remains unverified.
- Red: 11 focused cases failed on missing check labels before implementation.
- Green: 80 focused X cases pass. New checks cover attachments, Articles,
  withheld text, missing long text, truncation, unsupported references, mismatched
  identities, provider partial errors and lookup/search validation. Tests assert
  no source/body leakage, no extra reads on rejected lookup and no returned text.
- Deliberate break: replaced logged check names with `unknown`; all 11 new cases
  failed. Restored the check names before final verification.
- Full backend suite: 336 pass; existing Starlette/httpx deprecation warning.
  Strict mypy (40 source files), repository Ruff lint/format (108 files) and
  `git diff --check` pass. `agent-toolkit check` is unavailable (exit 127).
- Every internal adapter rejection now has a static diagnostic check label.
  Content acceptance and paid retry boundaries are unchanged. No live API call
  or hosted retry was made. Public browsing could not retrieve the specific
  post, so no claim about its media/Article content is made.

## Quote/repost support fix — 2026-10-18

- Evidence: owner-provided Render logs identify `unsupported_references`. This
  traces to the former parent guard rejecting quoted/reposted references and
  any multi-reference reply. The screenshot alone supplies no network status
  for the red activity request and is not evidence of a separate API failure.
- Red: new success cases for quotes (both include aliases), quoting replies and
  repost originals failed before implementation; missing-reference diagnostics
  and expanded-post bounds also failed (seven failing focused cases in total).
- Green: quote/repost expansion and related source context are handled in the
  original requests. New tests cover nested/deduplicated context, conflicting
  versions, unavailable/partial references, cycles, invalid combinations,
  unrelated expansions and RT previews not padding the minimum, plus shared
  post limits. Pipeline tests verify complete context is saved before model
  reservation and incomplete context is neither saved nor reserved/assessed.
- Deliberate break: disallow quoted/retweeted types again; all four selected
  successful quote/quoting-reply/repost cases fail. Restored support before checks.
- Final full backend suite: 357 pass, one pre-existing Starlette/httpx deprecation
  warning. Strict mypy passes for 40 source files; repository Ruff lint/format
  pass for 108 files. `git diff --check` passes.
- Archify workflow: editable JSON and HTML updated. Validation, delivery and
  strict artifact checks pass. Finalize exits 2 at skipped browser check because
  Chrome/Chromium is unavailable; no visual review claimed. Current receipts:
  [finalize summary](reference-diagram-check/x-workflow.finalize-summary.json),
  [browser status](reference-diagram-check/x-workflow.browser-check.json).
  Specification SHA256: `1bfef07562b4e559fa1b6de3b384756cdea32988e27f8a8c70afa65ffe61bc0e`;
  HTML SHA256: `16007ce15421114a55960f28bcb46eded68bcbbf6c1451f3efd4520e497adbec`.
- Toolkit check is unavailable (exit 127); Graft unavailable. No new dependencies,
  migration, env flag, frontend change or live provider request. Expansion may
  increase resource-based X charges; HTTP request count and retry rules unchanged.
- Hosted outcome remains unverified until the owner explicitly retries after
  deployment. Missing reference text/media/Articles still require manual paste.
