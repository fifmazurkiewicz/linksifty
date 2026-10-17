# Verification — 2026-10-17

- Compatibility reproduction: loaded the processing contracts from Git HEAD
  (`2bb056c`) into an isolated Python module. Both `Reservation` and
  `ProcessingJob` rejected a synthetic v2 rubric at `rubric_snapshot.version`
  with `extra_forbidden`. Working-tree contracts accepted both payloads.
- Red: four regression cases failed before the fix. Three reproduced
  `RuntimeError: Caught handled exception, but response already started` after
  a successful snapshot; one showed missing safe worker diagnostics.
- Green: 23 focused processing/API/failure tests passed.
- Deliberate break: replaced the API module's caught exception class in memory
  with an unmatched exception, then ran the usage-stream regression. It failed
  as expected. No source files were changed by this mutation check.
- Final full backend suite: 188 passed. Existing TestClient deprecation warning.
- Frontend: 35 tests passed; lint and production build passed.
- Strict mypy: 33 source files passed. Ruff lint/format and diff checks passed.
- Staging also included the previously untracked Archify HTML. The staged
  whitespace check reports 15 whitespace-only renderer lines in that artifact.
  It is preserved with its existing validation/hash receipts; source checks
  remain passing.
- `agent-toolkit check`: unavailable, exit 127 (command not found).
- SQL gate rerun could not connect to the prior disposable cluster;
  `pg_isready -h 127.0.0.1 -p 55440` reported no response. No SQL was changed
  for this incident. Earlier calibration SQL/concurrency evidence remains in
  `../assessment-calibration/evidence.md`; this is not a fresh SQL pass.
- Graft unavailable; focused repository inspection used.
- No provider calls, production mutations, commit/push or deployment performed
  during verification. The owner subsequently approved pushing the release to
  `main`; hosted rollout and reservation recovery remain separate checks.
