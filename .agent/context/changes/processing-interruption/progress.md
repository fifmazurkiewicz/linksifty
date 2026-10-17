# Processing interruption — 2026-10-17

Reported symptom: the TypeSafe article remained at `waiting_analysis`, then
showed a paused worker. User-supplied Render logs show repeated worker
interruptions approximately every 60 seconds and a separate Supabase read
timeout breaking `/v1/activity` after response headers were sent.

The owner confirmed migration 000010 was applied and identified the active
Render commit as `2bb056c2a358cc51b5427f1043a4667bbfd04a3f`. That commit rejects
the new rubric `version` field. The matching calibration implementation is
still uncommitted in this checkout. Reproducing both reservation parsing and
recovery-claim parsing against that commit raises `extra_forbidden`; the
current working-tree models accept both. The deployed compatibility mismatch
is confirmed; the historical worker exception itself was not captured by the
old generic logger.

Small local fixes completed:
- Worker interruption logs identify the operation, exception class and chained
  cause class, excluding messages, payloads, tracebacks and account identifiers.
- Persistence failures during account checks, inbox reads or usage reads close
  the SSE stream cleanly, using the existing frontend reconnect behavior.
- Regression tests and deployment troubleshooting documentation added.

No new retry, reservation reset, model call, database migration or deployment
was performed during local verification. The owner explicitly approved pushing
the pending calibration implementation and these fixes to `main` on 2026-10-17.
Release preparation is complete; commit/push and hosted rollout verification
are the remaining steps.
Inspect the retained reservation after deployment. A reservation can have
committed before old Python validation failed; reconcile its verified outcome
before an explicit new paid attempt. Never infer zero cost from missing logs.

Verification: [evidence.md](evidence.md). Hosted recovery remains outstanding.
