---
project: linksift
assessed_at: 2026-10-04T21:18:14Z
agent_readiness: ready-with-compensation
context_type: brownfield
stack_components:
  language: python 3.11
  framework: fastapi 0.142.2 (starlette 1.7.0, pydantic 2.13.5, uvicorn 0.54.0)
  build_tool: uv_build (>=0.12.17,<0.13)
  test_runner: null
  package_manager: uv
  ci_provider: null
  deployment_target: null
gates_passed: 4
gates_failed: 3
---

## Stack Components

**Language — Python 3.11.** Pinned by `.python-version` (`3.11`) and `pyproject.toml` (`requires-python = ">=3.11"`). The venv resolves CPython 3.11.16. Pydantic 2.13.5 arrives as a FastAPI dependency, so request and response schemas can be typed. No static type checker (mypy or pyright) is configured, and there is no linter or formatter (ruff, black) and no `.editorconfig`.

**Framework — FastAPI 0.142.2.** It is declared in `pyproject.toml` `[project].dependencies`, with Starlette 1.7.0, Pydantic 2.13.5 and uvicorn 0.54.0 resolved in `uv.lock`. The app module has not been written yet. `src/linksift/__init__.py` holds only a `main()` that prints "Hello from linksift!", and no `FastAPI()` instance exists anywhere.

**Build tool — uv_build.** `[build-system]` uses `uv_build>=0.12.17,<0.13.0` with the src layout (`src/linksift/`) and a console script `linksift = "linksift:main"`.

**Test runner — not detected.** pytest is not in the dependencies, and there is no `tests/` directory and no `[tool.pytest]` section.

**Package manager — uv.** Detected from `uv.lock` (15 packages) and `.venv/`.

**CI/CD — not detected.** There is no `.github/workflows/` directory. `context/foundation/tech-stack.md` plans GitHub Actions with auto-deploy on merge.

**Deployment — not detected.** There is no `render.yaml`, `Dockerfile` or `Procfile`. `tech-stack.md` plans Render for the API and Vercel for the frontend.

**Instruction files — none.** There is no `CLAUDE.md`, `AGENTS.md`, `.cursor/rules` or `.github/copilot-instructions.md`. `README.md` is empty (0 bytes).

**Out of scope for this assessment:** the Vite + React TypeScript frontend described in `tech-stack.md` is not on disk yet. Assess it once it is scaffolded. Its known gap is that the template is not convention-based, and `tech-stack.md` already records the plan to compensate with a router and documented folder conventions.

## Quality Gate Assessment

| Component                | Typed | Convention | Training Data | Documented | Verdict            |
|--------------------------|-------|------------|---------------|------------|--------------------|
| Language (Python 3.11)   | ~     | —          | —             | —          | compensate         |
| Framework (FastAPI)      | —     | ✗          | ✓             | ✓          | compensate         |
| Build tool (uv / uv_build)| —    | ✓          | ~             | ✓          | pass with note     |
| Test runner              | —     | —          | —             | —          | missing (not a gate failure; see Gaps) |

Legend: ✓ = pass, ✗ = fail, ~ = partial, — = not applicable

Count: 4 full passes and 3 gates that need compensation (2 partial, 1 failed), out of 7 applicable.

### Gate Details

**Language — typed: partial.**
- In favour: Pydantic 2.13.5 is installed (`uv.lock`), so API boundaries can be schema-typed. FastAPI reads type hints to validate requests.
- Against: no type checker is configured. `pyproject.toml` has no `[tool.mypy]` or `[tool.pyright]` section, mypy and pyright are absent from the dependencies and dev groups, and there is no `py.typed`. Nothing enforces type hints outside route signatures. Services, the scoring rule and fetchers can be left untyped and nothing will catch it.

**Framework — convention-based: fail.**
- FastAPI does not prescribe a folder layout, router registration or where business logic lives. Its "Bigger Applications" guide suggests `APIRouter` modules but does not enforce them.
- The project documents no conventions: there is no `CLAUDE.md` or `AGENTS.md`, and `README.md` is empty.
- `tech-stack.md` records `conventions: true` as a self-check answer, but nothing on disk backs that up yet. This becomes a partial pass once the conventions below are in an instruction file.

**Framework — popular in training data: pass.**
- Within the Python family, FastAPI is one of the three dominant web frameworks, alongside Django and Flask. Pydantic and Starlette are equally well represented.

**Framework — well-documented: pass.**
- fastapi.tiangolo.com has a tutorial and an advanced guide, plus release notes per version and auto-generated OpenAPI docs per app. Pydantic v2 has versioned docs at docs.pydantic.dev.
- Caveat: FastAPI's docs track only the latest release (there is no per-version switcher). Starlette 1.x is a recent major line, so older tutorials and the agent's priors may show deprecated APIs such as `@app.on_event` or Pydantic v1 `class Config`.

**Build tool — convention-based: pass.**
- `uv init` gives a standard src layout, `pyproject.toml` (PEP 621) and a lockfile. Commands are predictable: `uv add`, `uv run`, `uv sync`.

**Build tool — popular in training data: partial.**
- uv itself is now mainstream in Python, but it is recent (2024 onward).
- `uv_build` is a very new build backend, so there is less training data for it than for hatchling or setuptools.
- Agents often fall back to `pip install` or `python -m venv`, which bypasses the lockfile.

**Build tool — well-documented: pass.**
- docs.astral.sh/uv is current and comes with a detailed changelog.

**Test runner — not present.**
- There is no runner to score. This is a missing component rather than a failed gate, but it means the agent has no feedback loop. The compensation below adds pytest; dependency and CI checks belong to `/10x-health-check`.

## Gaps & Compensation

### 1. Type safety is only partial (language)
**What failed:** Python hints are optional and nothing checks them.
**Why it matters for agents:** the core of LinkSift is data-shape heavy: eight-criteria assessments, weighted scores, verdicts and per-user thresholds. An agent changing the scoring rule or the assessment schema gets no static signal when a caller breaks. Mistakes surface only at runtime, possibly inside a background job.
**Compensation:** add a mypy strict configuration and ruff. Require type hints everywhere and Pydantic models at every boundary (HTTP, LLM output, Supabase rows, fetcher results).

### 2. Framework is not convention-based (FastAPI)
**What failed:** FastAPI leaves the layout to the project, and none is documented.
**Why it matters for agents:** without a documented layout, every agent session invents its own placement. Routes end up in `__init__.py`, business logic goes into route handlers, and the deterministic scoring rule gets duplicated. This drift compounds over a 5-week MVP.
**Compensation:** document the folder layout, router registration, the dependency-injection pattern for auth and the database, the error-handling pattern, and where the pure scoring rule lives.

### 3. Build tool is newer than most training data (uv / uv_build)
**What is partial:** agents tend to fall back to pip or venv commands.
**Why it matters for agents:** `pip install` bypasses `uv.lock`, the environment drifts, and Render builds stop matching local runs.
**Compensation:** add explicit uv-only command rules.

### 4. No test runner (missing component)
**What is missing:** there is no pytest and no tests directory.
**Why it matters for agents:** the agent cannot verify its own changes. The deterministic scoring rule (FR-011, FR-018) is the most testable piece of the product and currently has no safety net.
**Compensation:** add pytest and httpx as dev dependencies and document the test command and layout.

### 5. Version-specific API drift (FastAPI / Starlette 1.x / Pydantic v2)
**What is partial:** the docs track only the latest release, and the agent may produce deprecated idioms from older data.
**Compensation:** pin the versions in the instruction file and list the preferred idioms.

### Recommended Instruction File Additions

Paste into `CLAUDE.md` (or `AGENTS.md`) at the root of `linksift`:

```markdown
## Stack & versions

- Python 3.11, FastAPI 0.142, Starlette 1.7, Pydantic 2.13, uvicorn 0.54. Package manager and build: uv (`uv_build` backend, src layout).
- Docs: FastAPI https://fastapi.tiangolo.com · Pydantic v2 https://docs.pydantic.dev/latest/ · uv https://docs.astral.sh/uv/
- Use Pydantic **v2** APIs only: `model_config = ConfigDict(...)`, `model_validate`, `model_dump`, `field_validator`. Never `class Config`, `.dict()`, `.parse_obj()`, `@validator`.
- App startup/shutdown uses a `lifespan` async context manager passed to `FastAPI(lifespan=...)`. Never `@app.on_event("startup")`.
- Settings come from `pydantic-settings` (`BaseSettings`) in `src/linksift/core/config.py`; never read `os.environ` elsewhere.

## Commands (uv only)

- Install / add deps: `uv sync`, `uv add <pkg>`, `uv add --dev <pkg>`. Never `pip install`, never `python -m venv`, never edit `uv.lock` by hand.
- Run API locally: `uv run uvicorn linksift.main:app --reload`
- Tests: `uv run pytest`
- Types: `uv run mypy src`
- Lint/format: `uv run ruff check --fix . && uv run ruff format .`
- Before declaring a task done, run tests, mypy and ruff; all must pass.

## Project layout (src/linksift/)

- `main.py` — creates the `FastAPI` app, registers routers and exception handlers, defines `lifespan`. No business logic.
- `api/routes/<resource>.py` — one `APIRouter` per resource (`links.py`, `items.py`, `chat.py`, `settings.py`, `admin.py`), each with `prefix` and `tags`. Registered in `main.py` via `app.include_router(...)`.
- `api/deps.py` — shared `Depends` providers: `get_current_user`, `require_approved_user`, `require_admin`, `get_db`.
- `schemas/` — Pydantic request/response models and LLM output models. Routes accept and return these only, never dicts.
- `services/` — business logic, framework-free (no `Request`, no `HTTPException`): `fetching/` (articles, X), `assessment.py` (LLM call), `scoring.py`, `chat.py`.
- `services/scoring.py` — the deterministic weighted score and verdict rule. Pure functions, no I/O, no LLM. The single source of truth for weights and thresholds; never reimplement scoring elsewhere.
- `db/` — Supabase/Postgres access. Every query is scoped by the authenticated user's id.
- `workers/` — background processing of submitted links.
- `core/` — config, logging, domain exceptions.
- Files and modules: snake_case. Classes: PascalCase. Pydantic models end in their role: `LinkCreate`, `ItemRead`, `AssessmentResult`.

## Typing rules

- All functions have full type annotations (parameters and return), including private helpers. mypy runs in strict mode; do not add `# type: ignore` without a reason in the same comment.
- Every boundary is a Pydantic model: HTTP bodies, LLM responses (validate before use; reject invalid output), fetcher results, DB rows returned to callers.
- Use `X | None`, not `Optional[X]`; `list[...]`/`dict[...]`, not `typing.List`.

## Error handling

- Services raise domain exceptions from `core/exceptions.py` (e.g. `FetchFailed`, `DuplicateLink`, `TrialLimitReached`, `SpendCapReached`, `NotFound`).
- `main.py` maps them to HTTP responses with `@app.exception_handler`. Routes do not catch and re-wrap them.
- `HTTPException` is raised only in `api/` code, never in `services/`.
- A failed or partial fetch is never turned into a summary: set the item to "awaiting manual content" and stop.

## Data isolation

- Every read/write of links, items, assessments and chats filters by the current user's id, including for admins. Admin endpoints touch accounts only, never other users' items.

## Tests

- Tests live in `tests/`, mirroring `src/linksift/` (`tests/services/test_scoring.py`, `tests/api/test_links.py`).
- API tests use `fastapi.testclient.TestClient` (or `httpx.AsyncClient` with `ASGITransport`) and override dependencies via `app.dependency_overrides`; they never hit real LLM, X or Supabase.
- Any change to `services/scoring.py` requires a table-driven test covering the 40% / 60% boundaries and a custom user threshold.
```

Paste into `pyproject.toml` to back the rules above:

```toml
[dependency-groups]
dev = ["pytest", "httpx", "mypy", "ruff"]

[tool.mypy]
python_version = "3.11"
strict = true
plugins = ["pydantic.mypy"]
mypy_path = "src"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "ANN"]
```

(Install them with `uv add --dev pytest httpx mypy ruff` rather than by editing `[dependency-groups]` by hand.)

## Summary

**Verdict: ready-with-compensation.** The backend stack is a mainstream, well-documented Python choice. FastAPI and Pydantic are among the strongest picks in the Python family, and none of the gaps calls for changing the stack. All gaps can be closed with instruction-file rules and a few dev tools.

**Key strengths:** FastAPI, Pydantic and Starlette are all strongly represented in Python training data. Pydantic v2 gives typed boundaries out of the box. uv provides a single lockfile-driven workflow, and the docs are current.

**Key gaps:**
- No static type checking.
- No documented layout for a framework that does not impose one.
- No test runner.
- No instruction file at all.
- Agent priors about pip and Pydantic v1 / `on_event` may produce outdated code.

The project is freshly scaffolded and has no commits and no app module yet, so now is the cheapest moment to lock the conventions in.

**Recommended next step:** add the `CLAUDE.md` block and `pyproject.toml` config above, then run `/10x-health-check` to cover dependencies, security, CI (GitHub Actions is not set up yet) and the missing deployment config for Render.
