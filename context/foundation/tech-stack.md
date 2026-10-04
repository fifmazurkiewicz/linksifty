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

A solo, after-hours, 5-week web-app MVP whose core work is fetching link content, scoring it with an LLM on eight criteria, chatting about items, and processing in the background fits a typed Python API: FastAPI clears all four agent-friendly gates (Pydantic schemas, conventions, popular within Python, current docs) and matches the author's existing stack, while Django — the Python default — was set aside for failing the typed gate. The UI is a separate Vite + React TypeScript SPA deployed to Vercel; that template fails the convention gate, which the author chose to compensate for with a router and documented folder conventions in CLAUDE.md. Supabase provides PostgreSQL, auth and per-user row-level isolation; OpenRouter is the LLM gateway on server-side keys; X content comes from the official paid API. The backend deploys to Render with GitHub Actions auto-deploy on merge. FastAPI ships no queue, so background processing needs an explicit worker or task mechanism chosen during planning. Scaffolding confidence is first-class: expect occasional manual steps.
