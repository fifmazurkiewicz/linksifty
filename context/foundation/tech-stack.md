---
starter_id: fastapi
package_manager: uv
project_name: linksift
hints:
  language_family: python
  team_size: solo
  deployment_target: render
  ci_provider: github-actions
  ci_default_flow: auto-deploy-on-merge
  bootstrapper_confidence: first-class
  path_taken: custom
  quality_override: false
  self_check_answers:
    typed: true
    from_official_starter: false
    conventions: true
    docs_current: true
    can_judge_agent: true
  has_auth: true
  has_payments: false
  has_realtime: false
  has_ai: true
  has_background_jobs: true
---

## Why this stack

Implementation note (2026-10-13): this paragraph describes the target stack. The monorepo uses `backend/` with uv and `frontend/` with npm. Auth and item REST persistence are mock-tested; job execution, OpenRouter/X/chat and deployed CI/hosting are unfinished. See `docs/roadmap.md` and the completion plan for evidence-based status.

A solo, after-hours, 5-week personal web-app MVP whose core work is fetching link content, scoring it with an LLM on eight criteria, and chatting about one item's saved source material fits a typed Python API: FastAPI clears all four agent-friendly gates (Pydantic schemas, conventions, popular within Python, current docs) and matches the author's existing stack, while Django — the Python default — was set aside for failing the typed gate. The UI is a separate Vite + React TypeScript SPA deployed to Vercel. Supabase Free provides PostgreSQL, auth and per-user row-level isolation; OpenRouter is the LLM gateway on server-side keys; X content comes from the official paid API. The backend deploys to Render Free with GitHub Actions auto-deploy on merge. There is no paid worker: durable jobs live in Supabase, FastAPI executes claimable work while awake, and an interrupted job resumes on a later application visit. Render cold starts and Supabase low-activity pauses are accepted MVP constraints. Scaffolding confidence is first-class: expect occasional manual steps.
