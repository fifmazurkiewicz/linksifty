---
bootstrapped_at: 2026-10-03T21:52:53Z
starter_id: fastapi
starter_name: FastAPI
project_name: linksift
language_family: python
package_manager: uv
cwd_strategy: native-cwd
bootstrapper_confidence: first-class
phase_3_status: ok
audit_command: pip-audit
---

## Hand-off

```yaml
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
```

**Why this stack** (verbatim from hand-off):

A solo, after-hours, 5-week web-app MVP whose core work is fetching link content, scoring it with an LLM on eight criteria, chatting about items, and processing in the background fits a typed Python API: FastAPI clears all four agent-friendly gates (Pydantic schemas, conventions, popular within Python, current docs) and matches the author's existing stack, while Django — the Python default — was set aside for failing the typed gate. The UI is a separate Vite + React TypeScript SPA deployed to Vercel; that template fails the convention gate, which the author chose to compensate for with a router and documented folder conventions in CLAUDE.md. Supabase provides PostgreSQL, auth and per-user row-level isolation; OpenRouter is the LLM gateway on server-side keys; X content comes from the official paid API. The backend deploys to Render with GitHub Actions auto-deploy on merge. FastAPI ships no queue, so background processing needs an explicit worker or task mechanism chosen during planning. Scaffolding confidence is first-class: expect occasional manual steps.

## Pre-scaffold verification

| Signal      | Value   | Severity | Notes                                                                 |
| ----------- | ------- | -------- | --------------------------------------------------------------------- |
| npm package | not run | —        | non-JS starter                                                        |
| GitHub repo | not run | —        | card docs_url (https://fastapi.tiangolo.com) is not a GitHub URL; no recency signal available |

## Scaffold log

**Project directory**: `/Users/Filip/dev/linksift` — created at the user's request outside the original workspace (`/Users/Filip/dev/10xdevs4`); `context/` was copied there before scaffolding (original left intact).
**Resolved invocation**: `uv init . && uv add fastapi uvicorn`
**Strategy**: native-cwd
**Exit code**: 0
**Pre-flight files-to-touch**: pyproject.toml, README.md, .python-version, .gitignore, entry module, uv.lock, .venv/
**Files written by CLI**: 6 (pyproject.toml, README.md, .gitignore, .python-version, src/linksift/__init__.py, uv.lock) + .venv/ + .git/
**Pre-existing files preserved**: context/ (all files)

Notes:
- uv 0.12.17 scaffolded a packaged layout (`src/linksift/__init__.py`, `uv_build` backend, `linksift` console script) rather than a flat `main.py`; no FastAPI app module was generated.
- `uv init` ran `git init` (branch `main`, no commits).
- Python resolved to CPython 3.11.16 (`requires-python >= 3.11`).
- Installed: fastapi 0.142.2, uvicorn 0.54.0, pydantic 2.13.5, starlette 1.7.0 (+ transitive, 15 packages total).

## Post-scaffold audit

**Tool**: pip-audit (run as `uvx pip-audit -r <uv export of project deps> --format json`)
**Summary**: 0 CRITICAL, 0 HIGH, 0 MODERATE, 0 LOW
**Direct vs transitive**: not distinguished by this tool

No known vulnerabilities found across 14 resolved dependencies.

## Hints recorded but not acted on

| Hint                    | Value                |
| ----------------------- | -------------------- |
| bootstrapper_confidence | first-class          |
| quality_override        | false                |
| path_taken              | custom               |
| self_check_answers      | typed: true, from_official_starter: false, conventions: true, docs_current: true, can_judge_agent: true |
| team_size               | solo                 |
| deployment_target       | render               |
| ci_provider             | github-actions       |
| ci_default_flow         | auto-deploy-on-merge |
| has_auth                | true                 |
| has_payments            | false                |
| has_realtime            | false                |
| has_ai                  | true                 |
| has_background_jobs     | true                 |

Not scaffolded by this run: the Vite + React TypeScript frontend (separate app, Vercel) — must be created separately.

## Next steps

Next: a future skill will set up agent context (CLAUDE.md, AGENTS.md). For now, your project is scaffolded and verified — happy hacking.

Useful manual steps in the meantime:
- `git init` already ran via `uv init`; make the first commit to start your repo history.
- No `.scaffold` siblings were created (empty target directory).
- Address audit findings per your project's risk tolerance — the full breakdown is in this log (currently clean).
- Scaffold the frontend separately (e.g. `npm create vite@latest web -- --template react-ts`).
- Copy the needed `.claude/skills` from the original workspace if you want to run the remaining chain steps from inside `linksift`.
