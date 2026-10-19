# Partial preview verification — 2026-10-19

- New backend regressions initially: 10 failed before implementation. Initial UI:
  1 failed, 1 passed. Added API-partial-response and repost-fragment regressions
  each fail before their targeted correction, then pass. Final backend preview
  file contains 22 cases: X reachable/withheld/unknown/truncated/repost/API-error
  fragments, partial HTTP/HTML, safe text extraction, budget denial/known/unknown
  cost, source/assessment isolation, typed submission/Retry consent, no-content
  skip and bounded invalid/truncated model output with retained billing IDs.
- UI regressions cover labeled auto preview/no Generate button/no score, stale
  preview hiding on completion and unknown-charge suppression of Retry while
  retaining Paste. PP1's Retry assertion fails before the charge-state guard;
  the final three cases pass. No styling system or navigation change.
- Deliberately replacing provider.preview with provider.assess makes two tests
  fail (19 pass at that point). Source restored in finally, and restored/mutated
  modules force-compiled to avoid stale equal-size bytecode. No mutation remains.
- Python commands use UV_CACHE_DIR=/private/tmp/linksifty-uv-cache and
  UV_OFFLINE=true with uv run --package linksifty. Final full backend suite and
  exact count are recorded in the completion summary below. Strict mypy passes
  50 files; Ruff check and format-check pass (132 formatted files). Frontend
  npm test -- --run passes 89 tests; npm run lint and npm run build pass. These
  worktree suites include unrelated local admin and completed chat diagnostics.
- A disposable PostgreSQL 17 cluster applies migrations 1–20 and the new SQL test
  fails on the absent preview RPC; migration 000021 then makes 31 assertions pass.
  The full 18-file pgTAP/processing gate and all existing concurrency checks pass,
  plus new overlapping preview same-job admission and two-job monthly-budget
  races. Guards cover consent default-off, false/foreign consent, foreign/stale/
  expired/rejected/zero-budget admission, one-shot slot, wrong owner/lease output,
  invalid output, late generation, no source/assessment, Needs action, owned list,
  unknown charge/Retry state, explicit Retry no resend, server-only RPC, deletion
  and detached billing. The temp cluster is always stopped and removed.
- Initial PostgreSQL initdb was sandbox-blocked by shared memory. The same
  disposable-local script was then permitted with sandbox escalation; no hosted
  connection, secret discovery, dependency install or migration took place.
- Archify finalize for workflow.json and x-rich-sources/text-only-workflow.json:
  validate/deliver/strict artifact check PASS, browser-check SKIPPED (Chrome not
  installed), exit 2. Editable English JSON and rendered HTML plus receipts are
  retained. Update check unavailable, noticeRequired=false. No browser/perceptual
  diagram review claimed. agent-toolkit check exits 127 (command unavailable).
- README, product vision, architecture, setup, roadmap and derived board reflect
  the new explicit preview exception and migration ordering. AGENTS.md now keeps
  no partial assessment/score while permitting owner-requested labeled previews.
  Raw fragments remain memory-only and never become complete source or research.
  No additional key/model/dependency or live paid action.

## Final correction and completion checks

- PP2 API forwarding assertion failed before atomic consent forwarding, then
  passes. SQL now contains 31 assertions, including atomic fetch/search/retry
  consent via three-argument overloads. Existing two-argument paths stay off.
- Current workflow diagrams describe automatic metadata only; no partial source
  reaches scoring. New preview workflow updated with atomic-consent detail;
  latest static validation receipts are under atomic-check/.

Final completion snapshot: `pytest backend/tests -q --tb=short` passes 560 tests
in 7.61s (one existing Starlette/httpx deprecation warning); `mypy --strict
backend/src` passes 50 files; `ruff check .` passes; `ruff format --check .`
passes 132 files. Frontend 89 tests, lint and TypeScript/Vite build pass. The
latest whole-worktree Python run includes concurrent independent chat-model work.
An intermediate full run saw 27 failures while that other feature was between
its tests and implementation; none were partial-preview tests, and the final
full run is green after those independent source updates. No unrelated behavior
was changed to make the preview checks pass.

The complete disposable gate passes 31 new SQL assertions, all 18 pgTAP files
and all existing races plus both preview admission races. New previews use the
same transaction as submission/Retry for consent, eliminating the reviewed race.
No tests contact real X/OpenRouter, access real credentials or apply hosted DDL.
Source/document whitespace checks pass excluding renderer-preserved workflow
HTML whitespace; new documentation links and current diagram receipt hashes
are checked. Diagram browser inspection and agent-toolkit remain unavailable,
not passed. No push/deployment or paid verification has been performed.
