# Implementation review — 2026-10-16

**Outcome: Approve for local implementation scope.** Native agent self-review,
not an independent reviewer or hosted acceptance. Read approved design/plan,
progress/evidence, code diff and current migration; Graft unavailable.

## Findings and dispositions

High: the initial migration draft copied obsolete digest-based paste hashing.
Fixed before completion by retaining the 000006 built-in SHA256 implementation;
all existing SQL regressions and legacy-upgrade checks pass. Canonical disposition:
[REV-001](review-decisions.md#rev-001--preserve-the-corrected-source-hashing-function).
No unresolved non-informational finding and no Skip.

## Plan fidelity

1. Pure immutable rubric, eight stable IDs, bounded descriptions/strict integer
   weights, defaults derived from CriterionName.weight; mixed-score/default tests.
2. Atomic owner-scoped settings update and reservation snapshot; database
   constraints/grants, immutable recovery, explicit reset and legacy backfill.
3. Reserved rubric reaches provider as user-level data subordinate to system
   grounding, scorer and saved history. Citation/corroboration checks remain.
   Mocked hostile description cannot bypass exact excerpt validation. No retry.
4. Eight fieldsets, accessible names/keyboard focus, bounded editing, atomic save,
   failed-load disablement, failed-save draft retention, owner-session remount,
   historical display and responsive themed layout. Shared frontend types in
   lib/rubric.ts avoid a feature-to-lib import inversion.
5. Product/deployment docs, canonical progress and derived boards updated;
   editable architecture source and HTML pass all four Archify gates.

## Evidence

163 backend tests; strict mypy on 34 source files; Ruff lint/format; 32 frontend
tests/lint/build; toolkit clean; 120 pgTAP assertions plus three concurrent races;
separate legacy upgrade assertions. Deliberate scoring/payload breaks were caught.
GUI tested with synthetic mock API, mobile 390px/light, desktop/dark and Tab order.
Diagram has automated browser validation, no separate perceptual inspection.
See [evidence](../evidence.md) for limitations and exact commands.

## Security, privacy and deployment

Authenticated owner supplies all data scope, including admin sessions. No user
account selector, new credential, provider, paid action or dependency was added.
Descriptions are bounded rubric data, not an alternative to fixed validation.
Snapshot persistence is transactionally fenced to the job lease; uncertain charges
remain reserved and cannot be silently reset. Existing completeness/source and
budget checks pass regression suites. No real credentials or hosted records read.

Hosted migration 000009 and matching backend/frontend deployment are separate
manual gates; old/new workers must not run custom rubrics together. No production
readiness, hosted isolation or paid model-quality claim is made. Plan/progress
mark only local implementation Done; boards mirror that scope.
