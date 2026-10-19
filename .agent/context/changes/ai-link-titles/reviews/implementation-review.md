# Implementation review — AI link titles

Outcome: approve the bounded implementation for publication to main as requested
by the owner. This is local verification; hosted activation is not certified.

## Findings

No unresolved code findings. No Skip dispositions or accepted code risks.
Environment limitations are recorded below, not treated as passed gates.

## Coverage and conventions

- New analyses request primary-source topic titles in the existing paid call.
  Independent validation retains a title when citation/assessment validation
  fails; lease-fenced SQL persists it without changing assessment readiness.
- Existing meaningful titles survive. All queue filters use the same heading
  and HTTP(S)-only source link, with safe new-tab attributes, wrapping and focus.
- Existing untitled ready/failed items offer confirmed title-only generation.
  API validation requires strict true confirmation and the authenticated owner.
  Orchestration remains in ProcessingService; routes only translate transport.
- Admission requires owner/account/expiry, inactive processing, complete saved
  text, shared monthly budget and no unresolved title call. No new dependency,
  source fetch, automatic backfill, assessment rerun or implicit paid retry.
- Actual costs settle through the existing idempotent ledger. Uncertain calls
  remain reserved. Deletion detaches the title reservation and late generation
  IDs still reconcile without resurrecting content.
- Pre-existing admin-count changes are excluded. Exact staged frontend checks
  verify the published feature does not depend on those edits.

## Evidence and limitations

493 backend tests, strict mypy, Ruff check/format, 83 exact-staged frontend tests,
frontend build and working-tree lint pass. All 20 migrations replay into a fresh
synthetic database. All 17 pgTAP suites pass, including 25 title assertions;
existing and new duplicate/shared-budget concurrency gates pass. A deliberate
title-loss mutation is caught by both title preservation regressions.

Archify schema/delivery/strict artifact checks pass. Browser QA is unavailable
without Chrome/Chromium; no perceptual review is claimed. `agent-toolkit check`
was attempted and unavailable (exit 127). Graft is unavailable; focused source
inspection was used. These remain explicit operator verification limitations.
No hosted migration, live provider call, real user data or external cost was used.
Deploy migration 000020 before the matching backend/UI.
