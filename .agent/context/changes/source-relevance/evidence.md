# Source relevance verification — 2026-10-18

All provider/HTTP responses used in tests are mocked. No live provider request,
credential read, hosted migration, deployment, or automatic reprocessing occurred.
Graft is unavailable; focused documentation/source reads were used.

## Behavioral evidence

- Initial red: new source-selection tests failed collection because SearchCandidate
  did not exist. The service regression protects the real numeric X ID query,
  an irrelevant Walmart result and relevant Opik documentation.
- Green: 19 focused selection tests cover typed choices and exact coverage,
  missing/invented choices, low confidence, known/unknown cost, provider rejection,
  timeout without retry, oversize unsent input, twenty metadata candidates,
  Brave metadata retention, topic/candidate absence, budget denial, configuration,
  cached/reclaimed jobs and fetched-text-only evidence.
- Deliberate break: removed `decision.relevant and` from the fetch admission guard.
  The valid service regression failed: expected one fetch, got two (Walmart included).
  Restored the guard before all final checks. No test weakened.
- Existing research/deduplication/twenty-page/cost tests now supply typed selection.
  Real Langfuse SDK in-memory export verifies selection decisions and ensures the
  transient-private-snippet fixture never appears in trace output.
- Frontend consent test verifies unchecked opt-in, Brave fee, Jev maximum hold,
  metadata sharing and explicit web_search submission. Research uncertainty copy
  covers a hold from either provider. Existing saved assessments are unchanged.

## Final commands

Using `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache` for uv:

| Check | Result |
| --- | --- |
| `uv run --package linksifty pytest backend/tests -q` | 463 passed; existing Starlette/httpx deprecation warning |
| `uv run --package linksifty mypy --strict backend/src` | Pass, 47 source files |
| `uv run --package linksifty ruff check .` | Pass |
| `uv run --package linksifty ruff format --check .` | Pass, 120 files |
| frontend `npm test -- --run` | 66 passed, 7 files |
| frontend `npm run lint` and `npm run build` | Pass |
| `agent-toolkit check` | Unavailable: command not found, exit 127 |

## Local PostgreSQL and upgrade

Disposable loopback PostgreSQL 17.11/pgTAP only; no hosted database. Complete
bootstrap and migrations 000001–000017 replayed into a second fresh test database.
Before 000017, seeded one opted-in job without research and one with saved context.
After migration, three assertions passed: unfinished consent disabled, saved
consent unchanged and saved context retained. This checks the actual full migration,
including the claim function's new return shape. An initial admission execution
exposed PL/pgSQL ambiguous `id`; qualified usage_reservations.id, then reran gates.

`check_processing_database.py` passed all fourteen SQL suites and ten concurrency
checks on the fresh migrated database. New source_selection.test.sql has 21 checks:
owner/lease/account/expiry/budget, settled-search prerequisite, one-time admission,
shared held/actual cost, reclaimed pointer, late generation/first-write behavior,
deleted-content ledger and server-only RPC privileges. New overlap checks prove
same-job admission once with ample budget and different-job shared-budget fencing.
`check_chat_database.py` also passed its 39 assertions and five concurrency checks.

## Diagram evidence and limits

[Editable contract JSON](source-selection-workflow.json) and
[workflow HTML](source-selection-workflow.html) retained. Archify finalize's
validate, deliver and strict artifact check pass. Browser gate skipped because
Chrome/Chromium is unavailable; command exit 2 is not a full finalize pass.
[Summary receipt](diagram-check/source-selection-workflow.finalize-summary.json).
No perceptual inspection or browser layout quality is claimed. Boards use the
existing project style, static SVG and canonical Markdown references. Both change
and roadmap boards pass diagram-design scripts/self_check.py.

## Activation limits

Migration 000017 and coordinated backend/frontend rollout remain owner actions.
Pause old workers/submissions, apply migration, deploy matching UI/backend, resume.
No main push that could auto-deploy before migration. Provisional confidence 0.8
is not an accuracy measurement; paid relevance calibration remains external.
No old saved result is silently rewritten; uncertainty retains charge accounting.
