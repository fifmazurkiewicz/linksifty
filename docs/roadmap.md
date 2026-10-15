# Linksifty product roadmap

Canonical product roadmap · updated 2026-10-15. [Derived Kanban](roadmap-kanban.html). Detailed coding cards: [completion plan](superpowers/plans/2026-10-13-linksifty-completion.md).

| Milestone | Status | Current evidence | Remaining deliverable | Completion cards |
| --- | --- | --- | --- | --- |
| M1 Foundation | Done (local foundation) | Monorepo, API health/config, pure scoring, frontend shell; local tests/build | Deployment is M7 | D1, D2 |
| M2 Identity and data lifecycle | In progress | Bearer verification and owner-filtered repository; migrations written | Database ownership/RLS validation, cleanup, login UI, deletion workflow | C1, C5, C6 |
| M3 Submission and durable processing | In progress | URL/paste submission, fenced bounded execution, heartbeat and recovery implemented locally with mocked tests | Database/concurrency and hosted restart validation; duplicate choices remain | C1, C4, C5 |
| M4 Source-grounded verdict | In progress | Safe redirects/body controls, completeness guard, OpenRouter schema/excerpts, pure scorer and USD reservation code locally verified | Execute SQL budget/RLS gates and hosted source/provider acceptance | C2, C3, C4 |
| M5 Inbox and detail | In progress | Authenticated queue/groups/verdict filter, live stages, detail/citations, paste recovery and persisted threshold implemented locally | Hosted acceptance and browser QA; read/delete product routes remain broader MVP work | C5, C6 |
| M6 Chat and source enrichment | Planned | Product contracts only | Grounded chat, five-source checking, official X adapter | C7 |
| M7 Validation and release | In progress | C8.1 GitHub CI and Docker build/smoke verified; 73 mock-backed backend tests, mypy/Ruff and frontend lint/build | Frontend behavior tests, log redaction, deployment artifacts, real RLS and 20-link evaluation | C8, E1 |
| M8 Google access and account approval | In progress | Backend access rules, admin API, Resend flow and authenticated frontend implemented locally; mock suites pass | Apply and validate database migrations, configure hosted Google OAuth/Resend, run hosted account-flow check | [Implementation plan](superpowers/plans/2026-10-14-multi-user-access-admin.md) |
| M9 Per-user model spend | In progress (local implementation) | Exact USD ledger/reservations, supported-model bound, admin caps and scoped user/admin views implemented with mocked tests | PostgreSQL/RLS/concurrency gate, retention schedule and hosted provider/cost acceptance | [Current plan](../.agent/context/changes/processing-usage-inbox/plan.md) |

## Delivery rules

- The coding goal is C1–C8. Configure credentials and hosted infrastructure only after the code is ready; E1 tracks that work.
- Jobs run opportunistically in the API while awake; PostgreSQL stores their state. There is no paid background worker.
- A failed/partial source requests pasted content and creates no assessment.
- Threshold changes affect future results only; every completed assessment stores its threshold.
- 30-day deletion requires cleanup execution; an expiry timestamp alone is not deletion.
- The approved M8/M9 scope supersedes the earlier personal-only exclusion of public signup and account administration. Admins still cannot access another user's content. Jev/System One remains excluded.
- “Done” distinguishes local code evidence from live service validation. No production readiness is currently claimed.

## Sequence and blockers

Owner resumed the processing/usage/inbox change on 2026-10-15. Its [specification](superpowers/specs/2026-10-15-processing-usage-inbox-design.md), [plan](../.agent/context/changes/processing-usage-inbox/plan.md) and [canonical progress](../.agent/context/changes/processing-usage-inbox/progress.md) describe the local implementation and unresolved gates. M3–M5/M9 have code and mock verification; PostgreSQL, agent-toolkit and hosted activation are not certified. The [lifecycle contract](../.agent/context/changes/processing-usage-inbox/lifecycle.html) includes safe recovery and liveness; it is not production evidence.

Epiki C1–C8 mają 40 podzadań wykonawczych C1.1–C8.5 z opisami, testami i zależnościami w completion plan. [Kanban szczegółowy](../.agent/context/changes/linksifty-personal-mvp/plan-kanban.html) pokazuje następne kroki i rozwijaną pełną listę. Roadmapa pozostaje widokiem milestone'ów.

C1 and independent C2/C3 tests → C4 → C5 → C6/C7 → C8. M8 can proceed alongside the remaining MVP coding; M9 depends on the source-safe assessment pipeline in C2–C4 and then its usage accounting. E1: Supabase/X/OpenRouter credentials, real database checks and hosted evaluation. C8.1 is Done for current local CI scope. C1.1 awaits a local PostgreSQL runtime for its SQL gate; C2.1 URL/DNS safety is Done (local mocked evidence); Safe acquisition, bounded processing, paste/detail/settings and per-user USD are now implemented locally in the current change; execute their database and hosted gates before marking the broader milestones Done. Missing credentials do not block coding. Missing agent-toolkit runtime blocks that particular quality check until restored.
