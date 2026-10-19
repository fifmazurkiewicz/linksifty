# Partial preview implementation review

Outcome: approve locally, with PP1 and PP2 fixed and verified. No open actionable findings
or Skip decisions; hosted model quality remains unverified.

## Plan coverage

The owner explicitly approved automatic generation from any readable fetched
fragment and rejected a Generate button. Partial text has a separate field, is
bounded/memory-only, and never enters complete-source storage, research, scoring
or assessment. Safe X fragments are identity-validated and reachable, including
200 responses with partial API errors; withheld/unrelated text is excluded. Web
fragment parsing retains URL/MIME/byte limits and excludes scripts/navigation.
The model describes only the fragment with no score or invented missing facts.

Preview admission is consented via updated Submit/Retry disclosure, owner/account/
lease/expiry fenced and budget-locked. Old jobs default off. One durable slot
prevents automatic resends; late generation IDs survive stale/deleted jobs and
known cost settles separately. Stored preview metadata follows item retention
and owner RLS. No new service/dependency or paid call.

## PP1 — Unknown preview charge

During implementation review, the queue initially offered Retry even though the
SQL guard rejected it. Expose pending preview cost in the owner-scoped snapshot,
hide Retry with a clear explanation, retain Paste. The new UI assertion failed
before this correction; final UI/SQL tests verify it. Canonical disposition is
[PP1](review-decisions.md#pp1--hide-retry-while-preview-cost-is-unknown).

## Verification and delivery limits

Red/green and a deliberate assessment-on-partial mutation protect the boundary.
Python/frontend checks and all disposable SQL/admission/deletion/budget races
pass; exact outcomes are in evidence.md. Toolkit and diagram Chrome checks are
unavailable and are not counted passed. Canonical progress precedes the boards;
local tasks are complete, hosted acceptance stays Planned. Migration 000021 must
precede matching backend/frontend; no hosted operation, automatic backfill,
push or current-item retry is included. Unrelated workspace work is preserved.

## PP2 — Consent admission race

A separate consent RPC after job creation allowed another worker to claim the job
before consent was visible, producing no preview even though the user approved it.
Fix now: existing submission/search/retry RPCs receive explicit three-argument
overloads, delegate to their original guarded functions and enable preview consent
within the same transaction. Old two-argument calls retain default-off behavior.
The services/repositories forward only an explicitly true flag. API forwarding
regression failed before this correction; SQL verifies atomic flags for all three
paths. No extra integration or paid operation is introduced. See canonical PP2.

Final acceptance evidence: whole-worktree 560 Python and 89 frontend tests pass,
strict mypy/Ruff and frontend build/lint pass; 31 preview SQL assertions and all
18 pgTAP/race suites pass in a disposable cluster. Both review dispositions are
verified. Active diagrams have matching current receipt hashes. Toolkit/Chrome
remain disclosed limits. Final approve is for local implementation only.
