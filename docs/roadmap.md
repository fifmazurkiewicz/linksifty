# Linksifty product roadmap

Canonical product roadmap · updated 2026-10-17. [Derived Kanban](roadmap-kanban.html). Detailed coding cards: [completion plan](superpowers/plans/2026-10-13-linksifty-completion.md).

| Milestone | Status | Current evidence | Remaining deliverable | Completion cards |
| --- | --- | --- | --- | --- |
| M1 Foundation | Done (local foundation) | Monorepo, API health/config, pure scoring, frontend shell; local tests/build | Deployment is M7 | D1, D2 |
| M2 Identity and data lifecycle | In progress | Bearer verification, owner-filtered repository and confirmed single/bulk hard deletion locally tested | Hosted ownership/RLS, cleanup and deletion acceptance | C1, C5, C6 |
| M3 Submission and durable processing | In progress | URL/paste submission, fenced bounded execution, heartbeat and recovery implemented locally with mocked tests | Hosted restart validation (duplicate blocking implemented locally) | C1, C4, C5 |
| M4 Source-grounded verdict | In progress | Safe redirects/body controls, completeness guard, OpenRouter schema/excerpts, pure scorer and USD reservation code locally verified | Hosted source/provider acceptance (local SQL budget/RLS gate passed) | C2, C3, C4 |
| M5 Inbox and detail | In progress | Authenticated queue, filters, stages, detail, recovery, settings and confirmed single/bulk deletion locally implemented | Hosted acceptance and browser QA; marking read remains broader MVP work | C5, C6 |
| M6 Chat and source enrichment | In progress (local chat, source checking and X ingestion) | Saved analysis/topic chat with citations, conditional one-search research, shared budget and idempotency; Brave/Langfuse and official X adapter implemented locally | Hosted chat/search/X acceptance and live answer-quality evaluation | C7 |
| M7 Validation and release | In progress | C8.1 GitHub CI and Docker build/smoke verified; 138 backend tests, 89 local pgTAP assertions, mypy/Ruff and 21 frontend tests/lint/build | Log redaction, deployment artifacts, hosted RLS/auth and 20-link evaluation | C8, E1 |
| M8 Google access and account approval | In progress | Backend access rules, admin API, Resend flow and authenticated frontend implemented locally; mock suites pass | Apply and validate database migrations, configure hosted Google OAuth/Resend, run hosted account-flow check | [Implementation plan](superpowers/plans/2026-10-14-multi-user-access-admin.md) |
| M9 Per-user model spend | In progress (local implementation) | Exact USD ledger/reservations, supported-model bound, admin caps and scoped user/admin views implemented with mocked tests | Retention schedule and hosted provider/cost acceptance (local PostgreSQL/RLS/concurrency passed) | [Current plan](../.agent/context/changes/processing-usage-inbox/plan.md) |

## Delivery rules

- The coding goal is C1–C8. Configure credentials and hosted infrastructure only after the code is ready; E1 tracks that work.
- Jobs run opportunistically in the API while awake; PostgreSQL stores their state. There is no paid background worker.
- A failed/partial source requests pasted content and creates no assessment.
- Threshold changes affect future results only; every completed assessment stores its threshold.
- 30-day deletion requires cleanup execution; an expiry timestamp alone is not deletion.
- The approved M8/M9 scope supersedes the earlier personal-only exclusion of public signup and account administration. Admins still cannot access another user's content. Jev/System One remains excluded.
- “Done” distinguishes local code evidence from live service validation. No production readiness is currently claimed.

## Sequence and blockers

Owner resumed the processing/usage/inbox change on 2026-10-15. Its [specification](superpowers/specs/2026-10-15-processing-usage-inbox-design.md), [plan](../.agent/context/changes/processing-usage-inbox/plan.md) and [canonical progress](../.agent/context/changes/processing-usage-inbox/progress.md) describe the local implementation and unresolved gates. M3–M5/M9 have code and mock verification; six migrations, 63 pgTAP assertions and overlapping budget reservations also pass on local PostgreSQL 17.11. Agent-toolkit and hosted activation remain unverified. The [lifecycle contract](../.agent/context/changes/processing-usage-inbox/lifecycle.html) includes safe recovery and liveness; it is not production evidence.

Epiki C1–C8 mają 40 podzadań wykonawczych C1.1–C8.5 z opisami, testami i zależnościami w completion plan. [Kanban szczegółowy](../.agent/context/changes/linksifty-personal-mvp/plan-kanban.html) pokazuje następne kroki i rozwijaną pełną listę. Roadmapa pozostaje widokiem milestone'ów.

C1 and independent C2/C3 tests → C4 → C5 → C6/C7 → C8. M8 can proceed alongside the remaining MVP coding; M9 depends on the source-safe assessment pipeline in C2–C4 and then its usage accounting. E1: Supabase/X/OpenRouter credentials, real database checks and hosted evaluation. C8.1 is Done for current local CI scope. The local SQL gate for the current C1 processing/usage scope now passes; C2.1 URL/DNS safety is Done (local mocked evidence); Safe acquisition, bounded processing, paste/detail/settings and per-user USD are now implemented locally in the current change; execute their remaining hosted gates before marking the broader milestones Done. Missing credentials do not block coding. Missing agent-toolkit runtime blocks that particular quality check until restored.


## Editable assessment rubric — local delivery

The user approved editing descriptions and weights for the existing eight
criteria and native execution on 2026-10-16. This extends M4/M5/M9 with atomic
per-account settings and durable model/scoring snapshots. Local implementation
and verification are complete: 163 backend tests, 32 frontend tests, 120 SQL
assertions and three concurrency checks. Migration 000009 and coordinated hosted
rollout remain separate. [Plan](../.agent/context/changes/editable-assessment-rubric/plan.md)
· [Canonical progress](../.agent/context/changes/editable-assessment-rubric/progress.md).

## Assessment calibration — local delivery

On 2026-10-17 the owner approved revised eight metrics, unscored N/A and
unverified states, grounded hype signals and up to 20 additional source fetches.
This extends M4/M5/M6 without changing historical results. Local test evidence
and deployment boundaries are tracked in the [canonical progress](../.agent/context/changes/assessment-calibration/progress.md)
and [verification evidence](../.agent/context/changes/assessment-calibration/evidence.md).
Migration 000010, coordinated rollout and paid/live article calibration remain
external acceptance work; no hosted readiness is inferred.

## Permanent link deletion — local delivery

Owner approved and requested release to main on 2026-10-17. M2/M5 now include
confirmed single and selected-group deletion, content cascades, ownership and
late-worker fences, and preserved billing accounting. Requires migration
000011. Local evidence: 202 backend tests, 39 frontend tests, nine SQL suites
and five concurrency checks. Toolkit and diagram browser QA are unavailable;
hosted migration/deletion acceptance remains separate.
[Canonical progress](../.agent/context/changes/link-deletion/progress.md).

## Analysis and topic chat — local delivery

Owner requested analysis/topic investigation, web search only when necessary,
at most one search per query, and native completion on 2026-10-18. M5/M6/M9 now
include persisted private chat, restored passage citations, conditional research,
shared monthly spending and durable duplicate-request protection. Requires
migration 000013 and coordinated backend/frontend deployment. Local evidence:
283 backend tests, 57 frontend tests, 33 chat SQL assertions and four chat
concurrency checks, plus the existing SQL/regression gates. Toolkit/browser QA
and hosted paid acceptance remain separate; no production readiness is inferred.
[Canonical progress](../.agent/context/changes/analysis-chat/progress.md).

## Official X posts and threads — local delivery

On 2026-10-18 the owner requested official X ingestion and selected individual
posts plus full threads. C7.1 is implemented locally with long-post text, archive
pagination, completeness guards and distinct manual fallback explanations.
Migration 000012 fences potentially billed attempts across crashes; a server
flag explicitly approves X account billing outside the model/Brave ledger.
[Canonical progress](../.agent/context/changes/x-ingestion/progress.md) ·
[Verification evidence](../.agent/context/changes/x-ingestion/evidence.md).
Hosted migration, endpoint/billing approval and live acceptance remain external.
