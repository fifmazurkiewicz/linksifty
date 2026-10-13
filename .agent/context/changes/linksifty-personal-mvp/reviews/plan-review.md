# Plan review: Linksifty personal MVP

**Plan reviewed:** `docs/superpowers/plans/2026-10-11-linksifty-personal-mvp.md`  
**Review date:** 2026-10-11  
**Outcome:** amended and approved for native implementation

## Inputs reviewed

Podział 2026-10-13: C1–C8 rozpisano na 40 podzadań bez zmiany produktu, architektury ani kryteriów nadrzędnych. Każde podzadanie ma własny wynik i weryfikację. E1.1–E1.3 pozostają zewnętrzną aktywacją; nowe Done nie zostały dodane.

2026-10-13 reconciliation: the completion supplement covers C1–C8 and E1 without adding product scope. It explicitly includes previously uncovered DNS/rebinding safeguards, child ownership, retry bounds, cleanup execution, citation validity and atomic cost reservation. The plan is suitable for continued authorized coding; production completion depends on executable SQL, provider and UI evidence.

- `frame.md`: personal, domain-agnostic inbox; source-grounded assessment; free-tier constraints.
- `research.md`: Render/Supabase durability facts and persisted-job alternative.
- `decisions.md`: manual-content fallback, five-source cap, no paid worker, 30-day retention, source-bounded chat, and no Jev/System One in MVP.
- Approved design specification and canonical PRD/roadmap.

## Coverage

The plan maps every accepted capability to an independently testable task:

- deterministic content readiness, eight criteria, scoring, and historic threshold snapshots in Task 2;
- RLS, ownership, retention, and durable records in Tasks 3 and 4;
- safe generic fetch and official X adapter seam in Task 5;
- schema-validated OpenRouter responses, cost cap, citations, and grounded chat in Task 6;
- authenticated, thin API routes and bounded opportunistic execution in Task 7;
- Inbox, Add, detail/recovery, chat, and Settings UX in Tasks 8 and 9;
- CI, logs, deployment guidance, and 20-link evidence in Task 10.

## Review findings

No non-informational findings. The plan explicitly preserves the required no-assessment-on-incomplete-content invariant, scopes all repository operations by user ID, and treats real provider/account setup as manual external work rather than claiming it can be automated.

## 2026-10-12 amendment review

The approved monorepo split changes repository layout, not runtime trust boundaries or product behavior. The root becomes the uv workspace, `backend/` owns the Python package, and `frontend/` owns its npm dependencies. The UX preview precedes persistence only as explicitly labelled local demo data; it neither fakes an authenticated session nor bypasses the planned API. This is safe to implement before Task 3. The earlier architecture diagram remains valid because its Vercel, Render, and Supabase boundaries do not change.

## Verification required during implementation

- Focused task tests before each task commit.
- Final Python checks: `uv run pytest`, `uv run mypy src`, `uv run ruff check .`, and `uv run ruff format --check .`.
- Final project check: `agent-toolkit check`.
- Frontend tests and production build under the `web/` package manager.
- Manual external evidence: Supabase migration/RLS validation, Render/Vercel deploy configuration, supplied X credential, selected OpenRouter model/cost, and the 20-link evaluation.


## 2026-10-14 Docker amendment

User explicitly requested a Dockerfile after Render selected Docker and failed
on the missing file. Approved bounded deployment slice: locked production uv
install, dedicated non-root API container, runtime PORT, excluded secret/build
context and CI smoke verification. Supabase persistence, Vercel frontend and
opportunistic runner architecture remain unchanged. Native Python remains an
optional fallback; Docker becomes the documented Render path. C8.3/E1 remain
incomplete. No new provider/worker/deployment action is authorized by this file.
