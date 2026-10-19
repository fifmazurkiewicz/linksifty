# Chat tracing evidence — 2026-10-19

## Behavioral verification

- Before implementation: `test_chat_traces.py`: 8 failed, 1 passed. Both named
  generations were absent. Added service scope/outcome cases then failed because
  the service did not accept telemetry.
- After implementation: focused chat/provider/telemetry/startup tests passed.
- Deliberate break: temporarily renamed only the classification generation to
  `disabled.classification`; the selected success/classification test failed
  (1 failed, 12 deselected). Restored the source immediately using `finally`.
- Final `uv run --package linksifty pytest backend/tests/unit -q --tb=short`:
  **532 passed**, one pre-existing Starlette/httpx deprecation warning.
- Real installed SDK with in-memory OpenTelemetry exporter verifies named
  generations share their chat parent trace, turn correlation, input/output,
  usage/cost, redaction, HTTP rejection/malformed/timeout/incomplete and low
  confidence diagnostics. Test HTTP is mocked; there are no paid calls.
- SDK start/update/end and event failures leave provider results/known zero-cost
  rejections intact, with exactly one request per operation.
- Service tests cover completed, classifier rejection and invalid evidence
  outcomes and ensure owner identity is absent from telemetry arguments.
- Existing chat tests cover duplicate fencing, no automatic provider retry,
  budgets, research, citations and owner scope. Existing provider tests cover
  disabled/default telemetry and oversize input with no HTTP request.

All uv commands used `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache` because the
default cache was outside the writable sandbox. The existing environment and
lockfile were reused; no dependency was installed or added.

## Required checks

- `uv run --package linksifty mypy --strict backend/src`: pass, 50 source files.
- `uv run --package linksifty ruff check .`: pass.
- `uv run --package linksifty ruff format --check .`: pass, 131 files.
- `git diff --check`: pass.
- `agent-toolkit check`: unavailable, shell exit 127, command not found.
- Graft unavailable in this session; targeted source/doc reads used.
- No frontend files changed by this task; unrelated working-tree edits retained.

### Final shared-workspace rerun

Concurrent partial-preview implementation appeared after the initial green run,
including updates to AGENTS.md and new methods in shared openrouter_client.py.
Inspected these changes and retained them. No running chat task was messaged.

- Focused chat/provider/telemetry/startup tests: **72 passed**, same deprecation warning.
- Strict mypy: pass, 50 source files.
- Full suite: **539 passed, 3 failed**. Failures are the newly added preview
  acquisition expectations: failed X readable text, partial HTML and HTTP 206
  readable text in test_partial_previews.py. This task did not edit that test or
  the acquisition adapters.
- Global Ruff lint/format now fail in concurrent processing_service.py, new
  preview sections of openrouter_client.py and preview tests (four files require
  formatting). Earlier green Ruff evidence is a snapshot, not a final global pass.
- No repeated runs to chase independently changing work; chat-specific checks
  remain green. Toolkit gate remains unavailable.

## Current hosted failure

Used the already signed-in Supabase SQL editor to SELECT only the current
owner's exact reported question and its associated reservation metadata. No
source contents, secrets, broader user records or production writes were needed.

Two failed turns at 16:39:18 and 16:39:28 UTC both have
`error=classification_uncertain`, `search_status=not_needed`. Each has one
classification reservation, settled at USD **0.000091938**, with generation ID;
there are no decision, answer or search reservations. Their initial reservation
was USD 0.002688 each, subsequently settled. The generic UI wording does not
prove any remaining reservation for these attempts.

The adapter sets this failure only after a valid classification response with
scope confidence below **0.8**. Exact confidence and winning choice were not
retained historically. New raw response events make those inspectable after
backend rollout. No confidence cutoff or safety/relevance routing was changed.

Langfuse UI shows existing production analysis traces; this confirms analysis
ingestion, not delivery of the new undeployed chat tracing. Past failures cannot
be backfilled. Deployment/hosted trace delivery are not claimed. No new migration
or environment flag is needed, and no paid replay was performed.

## Main release verification

Owner explicitly authorized pushing this chat change to main. Prepared an exact
chat-only snapshot from a4fd537, taking only the chat hunks from shared main.py
and openrouter_client.py; excluded concurrent admin/partial-preview changes.
PYTHONPATH points to the snapshot source; its imported provider path was checked.
The snapshot's complete backend unit suite passes: **532 passed** (same existing
deprecation warning). Strict mypy, Ruff lint/format and whitespace checks pass.
`agent-toolkit check` remains unavailable. No frontend or migration is included.
The earlier shared-workspace failures are not part of this release snapshot.
