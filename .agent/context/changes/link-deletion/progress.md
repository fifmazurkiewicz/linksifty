# Permanent link deletion

2026-10-17: Owner approved single/bulk deletion, explicit confirmation, complete
content cleanup, worker fencing and preservation of billing-only records.
Implementation and push to `main` explicitly authorized.

| Step | Status | Acceptance |
| --- | --- | --- |
| Database/API | Done | Atomic 1–50 owner IDs; strict confirmation; cascade content; preserve billing |
| Queue UI | Done | Single delete, visible selection, native confirmation, busy/error/success states |
| Verification | Done (available checks) | 202 backend / 39 frontend tests; nine SQL suites and five concurrency checks; mypy, lint, format and build |
| Documentation/review | Done locally | Rollout notes, validated workflow source/HTML, resolved review findings and roadmap |
| Release | Done (code published) | Implementation commit 97dc92f pushed to origin/main on 2026-10-17 |

Graft and agent-toolkit are unavailable. Diagram source/artifact checks pass,
but browser QA is unavailable because Chrome/Chromium is absent. No unavailable
gate is claimed passing. This change remains unarchived pending those gates
and hosted acceptance. No production content was deleted by implementation
or tests. Apply additive migration 000011 before hosted deletion acceptance;
the code push does not apply it.
