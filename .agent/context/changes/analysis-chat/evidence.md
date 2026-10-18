# Verification evidence — 2026-10-18

All remote integrations are mocked. No paid provider call, hosted migration,
deployment, secret read, or external communication was performed.

## Behavioral tests

- Red: new backend tests failed collection because `chat_contracts` did not exist.
- Red: frontend chat tests failed because `AnalysisChat` did not exist.
- Green: 24 chat service/API/provider/repository tests, including zero-search
  saved-context answers, exactly one research request, disabled final search,
  duplicate UUID returns without paid work, foreign/incomplete context rejection,
  shared budget denial, fabricated citations, partial fetch exclusion, preserved
  unknown-cost reservations, restored prior sources/history, and relevant evidence
  beyond the beginning of long articles.
- Deliberate break: temporarily permitted search in final generation. The
  research behavioral test failed as expected; original bytes restored immediately.
- Five frontend chat tests cover source expansion/safe links, authenticated Send,
  keyboard Send, saved history, pending disables, question preservation after
  provider failure, and the same UUID after a network failure.

## Full local gates

Use `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache` with the repository's uv runtime.
The default uv cache is sandbox-inaccessible; `--offline` uses installed dependencies.

- `uv run --offline --package linksifty pytest backend/tests -q`: 283 pass.
- `uv run --offline --package linksifty mypy --strict backend/src`: pass, 40 files.
- `uv run --offline --package linksifty ruff check .`: pass.
- `uv run --offline --package linksifty ruff format --check .`: pass, 107 files.
- Frontend `npm test -- --run`: 57 pass; `npm run lint` and `npm run build`: pass.
- One upstream FastAPI TestClient deprecation warning is informational.
- Counts include concurrently developed X-ingestion work; its edits are preserved.

## Real local PostgreSQL

Used installed PostgreSQL 17.11/pgTAP, synthetic auth bootstrap, and all migrations
in a fresh isolated cluster under `/private/tmp/linksifty-chat-pg-20261018`, on
loopback port 55443. `linksifty_chat_checked_test` contains only disposable test
data. A bootstrap for the second fresh database reused cluster roles only.

- `supabase/tests/analysis_chat.test.sql`: 33 assertions pass, rollback-only.
- `check_chat_database.py`: four overlapping-connection checks pass: shared cap,
  exactly one search slot, one executor for duplicate request, and deletion versus
  completion. Synthetic concurrency users are deleted in a finally block.
- `check_processing_database.py`: all 11 SQL suites pass (including chat/X), plus
  existing budget/duplicate/rubric/deletion and X concurrency checks.
- Discovered and fixed a chat RLS policy dependency on a browser-inaccessible
  account table; final policy relies on the established owner/item boundary.
- Sandbox initially blocked PostgreSQL shared memory/socket access; approved
  isolated local execution worked. One generic permission review timed out;
  a narrower explicit psql invocation succeeded. No unsafe action was inferred.

Reproduce using the explicit disposable local database convention:

```sh
PATH=/opt/homebrew/opt/postgresql@17/bin:$PATH \
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache \
LINKSIFTY_TEST_DATABASE_URL=postgresql://linksifty_test_runner@127.0.0.1:55443/linksifty_chat_checked_test \
uv run --offline --package linksifty python backend/tests/integration/check_chat_database.py
```

## Diagrams and unavailable gates

Archify `chat-workflow.json` -> `chat-workflow.html`: showcase validation,
delivery and strict artifact checks pass. Browser check is skipped (Chrome/
Chromium unavailable); no visual inspection is claimed. The diagram describes
the agreed contract, not a committed source snapshot or hosted deployment.
Receipts are alongside the editable source/HTML.

`agent-toolkit check` attempted: exit 127, executable unavailable. Graft is
unavailable, so focused repository queries were used. No tools were installed.

Hosted migration/deployment, paid answer-quality and search-necessity evaluation,
browser visual QA and Langfuse/provider records remain external acceptance.
Local evidence does not establish factual model entailment or hosted readiness.

Board self-checks pass for plan and review-decision HTML. The isolated PostgreSQL test server was stopped after verification; no unrelated runtime was stopped. Final chat API no-store regression and strict mypy pass after the privacy fix. `git diff --check` passes.
