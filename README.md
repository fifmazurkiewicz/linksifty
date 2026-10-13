# Linksifty

Linksifty is an agent-toolkit-assisted personal web app that turns saved web links, including X posts, into source-grounded notes and a repeatable value verdict.

It is deliberately paired with a separate implementation of the same product that does not use agent-toolkit. The product contract is shared; workflow, evidence, and delivery process are the comparison surface.

## Start here

- [Product vision](docs/product/vision.md)
- [Architecture overview](docs/architecture/overview.md)
- [MVP roadmap](docs/roadmap.md)
- [Detailed completion tasks](docs/superpowers/plans/2026-10-13-linksifty-completion.md)
- [Step-by-step service and environment setup](docs/deployment/setup.md)
- [Implementation Kanban](.agent/context/changes/linksifty-personal-mvp/plan-kanban.html)
- [Architecture diagram](docs/architecture/overview.md)
- [Agent instructions](AGENTS.md)

## Local checks

```sh
uv run --package linksifty pytest backend/tests
uv run --package linksifty mypy --strict backend/src
uv run --package linksifty ruff check .
uv run --package linksifty ruff format --check .
```

If the local agent-toolkit checkout is available, also run `agent-toolkit check` for configuration drift.

## Continuous integration

[CI](.github/workflows/ci.yml) runs on pushes, pull requests, and manual dispatch.
The backend job installs `uv.lock` with `uv sync --locked --package linksifty --group dev`
and runs the Python checks above. The frontend job runs `npm ci`, lint, and the
production build inside `frontend/`, using `frontend/package-lock.json`.
CI uses Python 3.11, uv 0.12.17, and Node 22.23.2; no provider credentials are needed.

The frontend test step uses `npm run test --if-present` until C6.1 adds its test
runner. A present, failing test script fails CI; today this step runs no behavior
tests. `agent-toolkit check` remains a separate required local gate because its
runtime is not installed or bootstrapped in this repository. A green CI run does
not certify that gate, database RLS, hosted integrations, or deployment.

## Run the API

Copy `.env.example` to `.env` and set server-side values when integrating real providers. The health endpoint runs without provider credentials:

Environment values must be exported in the shell or provided by the hosting platform; copying the file alone does not load it. For local preview only, set `LINKSIFTY_DEMO_MODE=true`. Without this setting, `/v1/` endpoints require a Supabase-verified bearer token. Configure the Supabase URL, anon key, and server-only service-role key and apply both migrations to enable real item submission, listing, and detail retrieval. Set `FRONTEND_ORIGIN` to the deployed frontend origin for CORS.

```sh
uv run --package linksifty uvicorn linksifty.main:app --reload
```
