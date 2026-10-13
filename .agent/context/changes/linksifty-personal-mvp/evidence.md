# Implementation evidence: Linksifty personal MVP

## C8.3 Docker artifact slice — 2026-10-14

- User explicitly requested Dockerfile after a Render Docker build failed because
  the file was missing. D-011 and plan amendment reviewed before implementation.
- Root Dockerfile uses python:3.11.16-slim-bookworm and uv:0.12.17, copies workspace
  manifests/lockfile/README/backend source, installs locked production dependencies
  non-editably and starts Uvicorn as app UID 10001. exec preserves stop signals;
  runtime PORT defaults to 8000. No secret ARG/ENV values or inherited .env files.
- Deny-by-default .dockerignore excludes frontend, Git, sessions, virtualenv and
  env files. Added CI container build/non-default-port health/auth/non-root smoke.
  README and setup guide now explain Docker on Render and native-Python fallback.
- Official uv Docker and Render Docker docs checked. No local Docker/Podman
  executable: actual image validation delegated to the new GitHub CI job.
- Local: 73 backend tests, strict mypy, Ruff lint/format, YAML container-job
  validation and git diff --check pass. agent-toolkit check unavailable (exit 127).
- Google OAuth documentation changes from the preceding request are preserved.
  No hosted service, provider key, permission or paid integration was modified.
  C8.3 remains incomplete beyond this artifact slice.


## Google OAuth setup preference — 2026-10-14

- User selected Google/Gmail sign-in through Supabase. Updated setup section 3.4,
  C6.2 description, derived task disclosure, progress and D-010. No task status
  changed and no frontend/provider configuration was implemented.
- Official Google/Supabase docs verify OAuth web client, origins, Supabase callback,
  provider credential placement, identity-only scopes and matching-email linking.
  Google secrets are stored in Supabase, not frontend/Render env; no new backend
  env variables are needed just to enable the hosted provider.
- Provider setup remains manual and frontend sign-in/session handling remains C6.2.
  No external account, permission, signup or credential change was performed.


## Manual setup guide — 2026-10-13

- User requested step-by-step Supabase/Render/Vercel/OpenRouter/X and environment instructions. Added docs/deployment/setup.md and linked it from README and the existing Supabase reference.
- Verified all seven backend env names against config.py and the one current frontend env against App.tsx. Checked local migration links, monorepo build/start paths, uv --env-file support, and git diff --check.
- Official provider docs checked for Supabase legacy/new API key compatibility, Auth/signup/redirect settings, Render Python/uv/PORT/free-service behavior, Vercel Vite/root/env settings, OpenRouter key limits/structured output and official X onboarding.
- Guide explicitly marks unfinished frontend auth, job execution, provider adapters, budget enforcement, ownership/RLS and cleanup. New Supabase secret keys cannot replace the current service-role JWT without adapting Authorization headers. No invented model/frontend-auth env names are presented as implemented.
- Repository regression: 73 backend tests, strict mypy and Ruff lint/format pass. agent-toolkit check remains unavailable (exit 127). No frontend implementation changes; frontend behavior runner remains C6.1.
- Documentation only: no account setup, key collection, hosted migrations, push, deployment, purchase or provider request performed. E1 and C8.3 stay incomplete; the guide is a manual preparation artifact.


## C2.1 — URL/DNS safety — 2026-10-13

- Changed: HTTP acquisition adapter + its security tests, D-009 decision, architecture documentation, completion plan/progress/roadmap and derived boards. No dependencies, provider integrations, deployment or frontend changes. Graft unavailable; focused caller search found only tests for the former borrowed-client function.
- Production path uses standard-library `getaddrinfo` through the async event loop with a 10-second resolution timeout; all returned IPv4/IPv6 addresses must pass conservative public-address checks. Empty/mixed/private DNS sets reject before HTTP. DNS errors/timeouts return unavailable with no text.
- Malformed URLs, non-HTTP(S) schemes, userinfo including empty credentials, invalid ports, controls/backslashes, localhost, zone IDs and non-public literals are rejected. Fresh client per fetch, no environment proxies or inherited auth/cookies. Numeric-IP URL pins the actual connection; original Host/SNI preserve virtual-host routing and TLS hostname verification.
- Verified the installed HTTPX/httpcore connection path and official [SNI extension contract](https://www.encode.io/httpcore/extensions/#sni_hostname). No custom network backend or direct production httpcore dependency added. Mixed DNS and 6to4 are conservatively refused; first public IP only, with no failover/retry added.
- Red: before implementation, the new transport-owned contract failed (35 cases). A separate behavioral assertion against the original function also failed: a credential-bearing URL was fetched rather than returning unsafe_url.
- Green: 38 fetcher cases pass, including private IPv4/IPv6, mapped/transition addresses, credentials, malformed URL/ports, mixed/empty DNS, resolution failure/timeout, literal public IP, pinned IPv4/IPv6 and original Host/SNI. The actual HTTPX transport is exercised with a mocked network backend: the socket receives the numeric public IP; TLS receives the original hostname with certificate hostname checking enabled. Hostile HTTPS_PROXY does not redirect the connection. No remote DNS/fetch occurs in tests.
- Deliberate break: replacing `target.copy_with(host=addresses[0])` with `target` caused the real-transport test to fail: socket destination `example.com` instead of `93.184.216.34`. Source restored byte-for-byte before final checks.
- `uv run --package linksifty pytest backend/tests -q`: 73 passed (one existing FastAPI/httpx deprecation warning).
- `uv run --package linksifty mypy --strict backend/src`: passed, 19 source files.
- `uv run --package linksifty ruff check .`: passed; `uv run --package linksifty ruff format --check .`: passed, 54 files.
- Final artifact checks: both Kanban files pass diagram-design self_check, all 40 detailed task statuses match the canonical plan (34 Planned, 3 Ready, 1 Blocked, 2 Done), and git diff --check passes. Scope review is recorded in reviews/implementation-review.md.
- `agent-toolkit check`: exit 127, runtime missing; gate outstanding. No hosted/private-network test or actual certificate exchange claimed. Redirects, streaming/body bounds, extraction and full completeness remain C2.2–C2.5, rather than marking C2 complete.


## C8.1 — CI for both packages — 2026-10-13

- Selected the independent Ready CI task because C1.1 requires local PostgreSQL; `psql`, `postgres`, `initdb`, `pg_ctl`, Docker and Podman were unavailable. No database changes were made and no RLS/ownership SQL execution is claimed.
- Changed surfaces: `.github/workflows/ci.yml`, README CI documentation, completion task statuses, progress/roadmap and derived boards. Existing unrelated changes preserved.
- Design: two independent Ubuntu jobs, read-only token permissions, checkout without persisted credentials, bounded timeouts/concurrency, uv 0.12.17/Python 3.11 and Node 22.23.2. No deploy, provider calls or credentials. `uv sync --locked --package linksifty --group dev` and `npm ci` use committed lockfiles. Backend checks run from root; npm runs only inside frontend.
- Official action inputs checked against [setup-uv](https://github.com/astral-sh/setup-uv), [setup-node](https://github.com/actions/setup-node) and [checkout](https://github.com/actions/checkout). setup-uv uses its documented v10.3.0 commit; checkout/setup-node use documented v7 tags.
- Red: Ruby YAML contract validation failed with ENOENT before CI existed. Green: valid YAML with backend/frontend jobs, push/pull_request/manual triggers, read-only permissions and no failure suppression. Static validation is not a hosted Actions execution; actionlint is unavailable.
- Deliberate failure: temporarily set the frontend test script to `node -e "process.exit(17)"`; `npm run test --if-present` returned 17. Restored package.json byte-for-byte before final checks. C6.1 owns the real frontend test runner; the absent test script currently executes no tests, and this is documented rather than counted as passing behavior tests.
- Locked install: uv sync passed (30 resolved, 29 checked); npm ci passed (28 packages installed, zero reported vulnerabilities). Initial offline npm install lacked cached Vite; ordinary locked install completed with approved registry access. No dependencies or lockfiles changed.
- `uv run --package linksifty pytest backend/tests`: 37 passed (one existing FastAPI/httpx deprecation warning).
- `uv run --package linksifty mypy --strict backend/src`: passed, 19 source files.
- `uv run --package linksifty ruff check .`: passed.
- `uv run --package linksifty ruff format --check .`: passed, 54 files.
- Frontend `npm run lint`: passed. `npm run build`: passed, Vite 8.3.4 production bundle. `npm run test --if-present`: exit 0 with no test script, explicitly not a test-suite pass.
- Final documentation checks: both Kanban HTML files pass diagram-design self_check; all 40 displayed task statuses match the canonical plan (35 Planned, 3 Ready, 1 Blocked, 1 Done); git diff --check passes. Scope review recorded in reviews/implementation-review.md.
- `agent-toolkit check`: exit 127, executable missing. This gate remains outstanding and is not silently installed or represented as green in CI. No GitHub workflow dispatch, push, deployment, live database or paid integration executed.


## Granular task decomposition — 2026-10-13

- C1–C8 split into 40 uniquely identified coding tasks C1.1–C8.5. Each has description, dependencies, acceptance, verification and its area file paths. External E1 split into three setup steps owned by Filip.
- Automated documentation check confirms 40 unique headings, one matching Kanban entry per task, and 40 acceptance/verification sections. The derived board passes diagram-design self_check and git diff --check. No implementation behavior or Done scope changed.

## Documentation reconciliation — 2026-10-13

- Completion plan C1–C8 preserves the original scope and maps each missing feature to files, dependencies, acceptance and verification. E1 isolates external activation from coding work.
- Canonical roadmap/progress updated before their derived SVG Kanban boards. Both boards pass diagram-design self_check; they include detailed task disclosures and source links.
- New architecture and target lifecycle artifacts pass Archify validate/deliver/strict-check. Finalize exits 2 at browser-check: Chrome/Chromium unavailable. Browser evidence is skipped; no perceptual review was performed. JSON/HTML/receipts remain together under the dated .archify folders.
- No hosted deployment, database policy execution, cleanup or full job runner is claimed by these documentation changes.

## Authenticated persistence — 2026-10-13

- Red: new auth/repository tests failed with missing modules before implementation.
- Green: 37 backend tests pass, including Supabase identity verification, missing/rejected credentials, malformed provider identity, auth timeouts, owner filters, transactional submission requests, inaccessible item 404, and failed-write 503.
- Runtime HTTP dependency declared through `uv add --package linksifty httpx`.
- Deliberate-break check: temporarily bypassing authentication caused the production-auth test to fail; the correct condition was restored immediately.
- Strict mypy, Ruff lint/format checks passed. `agent-toolkit check` could not run: executable is not installed. Hosted database validation is pending; mocked HTTP is not evidence of actual RLS enforcement.

## Task 1 — executable skeleton and configuration boundary

**Changed surfaces:** `src/linksifty/config.py`, `src/linksifty/main.py`, `src/linksifty/__init__.py`, `tests/unit/test_config.py`, and `README.md`.

**TDD evidence:**

- Red: `uv run pytest tests/unit/test_config.py -v` failed during collection with `ModuleNotFoundError: linksifty.config`.
- Green: the focused test suite passed: 2 tests passed.
- Deliberate break: changing `/health` from `{"status": "ok"}` to `{"status": "broken"}` made `test_health_endpoint_needs_no_provider_call` fail with the expected differing response.
- Restored green behavior before continuing.

**Quality evidence:** `uv run mypy src`, `uv run ruff check .`, and `uv run ruff format --check .` all passed after the implementation.

**Environment note:** the initial sandboxed `uv` invocation could not access its cache at `/Users/Filip/.cache/uv`; the same verification commands succeeded after approved access to that existing cache. No secret or provider integration was invoked.

## Task 2 — deterministic domain behavior

**Changed surfaces:** `src/linksifty/domain/models.py`, `src/linksifty/domain/content_policy.py`, `src/linksifty/domain/scoring.py`, `tests/unit/test_content_policy.py`, and `tests/unit/test_scoring.py`.

**TDD evidence:**

- Red: source and scoring tests initially failed during collection because `linksifty.domain` did not exist.
- Green: content completeness, weighted scoring, threshold snapshot, low-score hype, and review-band tests passed.
- Deliberate break: replacing `score >= threshold` with `score > threshold` made the equal-threshold test fail; restored the approved inclusive boundary.

**Quality evidence:** all eight focused tests pass; strict mypy, Ruff lint/format, and `git diff --check` pass.

**Deliberate simplification:** content completeness uses transparent text markers plus a 200-character floor. It is conservative by design; the browser-rendered/source-specific acquisition layer can add stronger signals later without weakening the no-assessment guardrail.
