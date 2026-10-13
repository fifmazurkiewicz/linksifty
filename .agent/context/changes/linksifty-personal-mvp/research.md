# Technical research: Linksifty personal MVP

Research date: 2026-10-11. Graft was not available in this environment, so the repository facts below come from focused file inspection.

## Verified repository facts

- The project is a Python 3.11+ `uv` package with FastAPI declared; the only package source is `src/linksifty/__init__.py`, currently a placeholder. Evidence: `pyproject.toml`, `src/linksifty/__init__.py`.
- The prior product contract selected React/Vite, FastAPI, Supabase, OpenRouter, official X API, Vercel, and Render. Evidence: `context/foundation/tech-stack.md`.
- The original PRD contains the eight criterion names and the evidence-first weights: `×2` for evidence, replicability, source credibility, and absence of conflict of interest; `×1` for novelty, practicality, independent corroboration, and concreteness. Evidence: `context/foundation/prd.md`, Business Logic.
- The previous roadmap includes multi-user pending signup, admin approval, a 20-source reference cap, and a separate worker assumption. Those elements conflict with the new personal MVP decisions and require replacement. Evidence: `context/foundation/roadmap.md`, `docs/roadmap.md`, `docs/product/vision.md`, and `docs/architecture/overview.md`.

## Verified external facts

- Render Free web services spin down after 15 minutes without inbound HTTP traffic or WebSocket messages. A later request wakes the service, and Render describes the wake as taking about a minute. Source: Render, “Deploy for Free”, retrieved 2026-10-11: https://render.com/docs/free
- Supabase Free projects can be paused after a low-activity week; restoration is performed in the Supabase dashboard. Source: Supabase, “Project Pausing”, retrieved 2026-10-11: https://supabase.com/docs/guides/platform/free-project-pausing
- FastAPI `BackgroundTasks` are suitable for small work in the same application process. Its documentation directs heavy or multi-process work toward queue-based systems, which this MVP explicitly avoids for cost reasons. Source: FastAPI, “Background Tasks”, retrieved 2026-10-11: https://fastapi.tiangolo.com/tutorial/background-tasks/
- Supabase recommends enabling RLS and defining per-operation policies for exposed tables. It documents that a server-side `service_role` bypasses RLS and must remain server-only. Source: Supabase, “Row Level Security”, retrieved 2026-10-11: https://supabase.com/docs/guides/database/postgres/row-level-security

## Constraints inferred from those facts

- A Render process is not durable. The database, rather than in-memory `BackgroundTasks`, must be authoritative for job state.
- Running a task after an API response is only an opportunistic execution strategy. It must be safe to repeat or abandon when the process sleeps.
- Each job needs a lease or equivalent atomic claim, an attempt count, and terminal status so a new visit can resume unclaimed or expired work without double-charging.
- The browser must not access OpenRouter, X, or the Supabase service-role credential. Browser-visible reads and writes must remain constrained by RLS and authenticated user identity.

## Alternatives considered

1. **Dedicated queue worker:** strongest liveness but requires paid compute; rejected by the product owner.
2. **Synchronous HTTP processing:** simplest deployment but makes the user wait and risks request timeout; rejected by the product requirements.
3. **Persisted jobs plus opportunistic in-process execution:** accepts eventual completion after the next application visit, costs no additional worker, and preserves true job state; selected by the product owner.

## Remaining external unknowns

- The exact X API plan and cost for the required post/thread retrieval have not been verified; no credential or paid-provider documentation was inspected.
- The selected OpenRouter model and its structured-output and pricing behavior have not been chosen; this must be bounded before real paid calls are enabled.
