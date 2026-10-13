# Linksifty personal MVP roadmap

Canonical product roadmap · updated 2026-10-13. [Derived Kanban](roadmap-kanban.html). Detailed coding cards: [completion plan](superpowers/plans/2026-10-13-linksifty-completion.md).

| Milestone | Status | Current evidence | Remaining deliverable | Completion cards |
| --- | --- | --- | --- | --- |
| M1 Foundation | Done (local foundation) | Monorepo, API health/config, pure scoring, frontend shell; local tests/build | Deployment is M7 | D1, D2 |
| M2 Identity and data lifecycle | In progress | Bearer verification and owner-filtered repository; migrations written | Database ownership/RLS validation, cleanup, login UI, deletion workflow | C1, C5, C6 |
| M3 Submission and durable processing | In progress | URL API submission and item+job transaction; pure lease rules | Paste mode, duplicate choices, lease fencing, execution/resume and retry correctness | C1, C4, C5 |
| M4 Source-grounded verdict | In progress | C2.1 URL/DNS safety + pinned connection (mock verified), domain scorer, injected assessment draft | Redirect/body safety, completeness enforcement, provider schema/citations and atomic budget | C2, C3, C4 |
| M5 Inbox and detail | In progress | Inbox/Add preview uses API | Authentication, filters, detail, read/delete/recovery and persisted threshold | C5, C6 |
| M6 Chat and source enrichment | Planned | Product contracts only | Grounded chat, five-source checking, official X adapter | C7 |
| M7 Validation and release | In progress | C8.1 GitHub CI and Docker build/smoke verified; 73 mock-backed backend tests, mypy/Ruff and frontend lint/build | Frontend behavior tests, log redaction, deployment artifacts, real RLS and 20-link evaluation | C8, E1 |

## Delivery rules

- The coding goal is C1–C8. Configure credentials and hosted infrastructure only after the code is ready; E1 tracks that work.
- Jobs run opportunistically in the API while awake; PostgreSQL stores their state. There is no paid background worker.
- A failed/partial source requests pasted content and creates no assessment.
- Threshold changes affect future results only; every completed assessment stores its threshold.
- 30-day deletion requires cleanup execution; an expiry timestamp alone is not deletion.
- No public signup/admin content access, Jev/System One, or scope expansion.
- “Done” distinguishes local code evidence from live service validation. No production readiness is currently claimed.

## Sequence and blockers

Epiki C1–C8 mają 40 podzadań wykonawczych C1.1–C8.5 z opisami, testami i zależnościami w completion plan. [Kanban szczegółowy](../.agent/context/changes/linksifty-personal-mvp/plan-kanban.html) pokazuje następne kroki i rozwijaną pełną listę. Roadmapa pozostaje widokiem milestone'ów.

C1 and independent C2/C3 tests → C4 → C5 → C6/C7 → C8. E1: Supabase/X/OpenRouter credentials, real database checks and hosted evaluation. C8.1 is Done for current local CI scope. C1.1 awaits a local PostgreSQL runtime for its SQL gate; C2.1 URL/DNS safety is Done (local mocked evidence); C2.2 safe redirects is next Ready. Missing credentials do not block coding. Missing agent-toolkit runtime blocks that particular quality check until restored.
