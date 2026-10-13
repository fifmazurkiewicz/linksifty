---
project: Linksifty
version: 2
status: implementation-in-progress
updated: 2026-10-13
prd_version: 2
milestone_id: personal-mvp
milestone_status: in-progress
---

# Roadmap: Linksifty personal MVP

> Derived from `context/foundation/prd.md` v2 and the confirmed planning quiz. This document is the detailed companion to `docs/roadmap.md`.

Current evidence and statuses are canonical in [docs/roadmap.md](../../docs/roadmap.md). Detailed remaining tasks C1–C8 and external gate E1 are in [completion plan](../../docs/superpowers/plans/2026-10-13-linksifty-completion.md). This milestone is unfinished; demo screens and HTTP mocks do not prove deployed behavior.

## Milestone

**Personal MVP** — Filip can submit or paste content for up to five links, return to a truthful inbox, and use explainable value verdicts and source-bounded chat to triage his own backlog.

**Done when:** the PRD's 20-link acceptance measurement passes and required coding/security gates are verified. Tuning evidence alone does not establish completion.

## Delivery slices

| ID | Change ID | Outcome | Prerequisites | Status |
| --- | --- | --- | --- | --- |
| P-01 | personal-app-foundation | Deployed React/FastAPI shells, configuration, CI, and deploy health checks | — | local code verified; CI/deploy pending |
| P-02 | personal-identity-data | One authenticated account, user-scoped schema/RLS, deletion, and 30-day expiry | P-01 | in progress: auth/REST code; C1/C5/C6 remain |
| P-03 | durable-submission-jobs | URL/paste submission, duplicate decision, persisted task states, and safe resume after sleep | P-02 | in progress: submission RPC; C4/C5 remain |
| P-04 | generic-web-assessment | Generic web fetch, manual-content fallback, source excerpts, schema-validated assessment, pure scoring, and spend cap | P-03 | in progress: prototypes; C2/C3 remain |
| P-05 | inbox-and-item-detail | Mobile inbox, verdict filter, read state, item explanation, and prospective threshold setting | P-04 | in progress: preview; C5/C6 remain |
| P-06 | chat-and-source-enrichment | Source-bounded item chat, up to five cited-source checks, and dedicated X adapter | P-04, P-05 | planned |
| P-07 | release-evaluation | CI evidence, structured logs, security review, and 20-link evaluation | P-01–P-06 | planned |

## Dependency and scope notes

- P-02 is early because isolation and retention are difficult to retrofit.
- P-03 writes durable state before asynchronous work begins; FastAPI in-process execution is opportunistic only and cannot be treated as a durable worker.
- P-04 must enforce no-assessment-on-partial-content and must record cost from the first paid call.
- P-05 applies a changed threshold only to future assessments by snapshotting it with the completed item.
- P-06 remains part of v1. If schedule pressure forces a cut, defer cited-source enrichment first, then the X adapter; do not remove manual-content fallback, scoring explainability, or data isolation.

## External gates

1. **X API:** Verify post/thread availability and cost before P-06 enables real calls. Owner: Filip.
2. **OpenRouter model:** Select a model with reliable schema-constrained output and verify its unit cost before P-04 enables real paid calls. Owner: Filip.
3. **Free-tier behavior:** Render cold starts and Supabase low-activity pausing are accepted constraints, not blockers.

## Explicitly deferred

- Public signup, pending trials, admin approval, and all multi-user product operations.
- Bookmark import, Telegram, sharing, topic categorization, full-text search, BYOK, and manual reassessment.
- Automatic content extraction for PDFs, video, podcasts, newsletters, Reddit, and blocked or unsupported pages.
- A paid or always-on background worker and a dedicated analytics platform.
