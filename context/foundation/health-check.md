---
project: linksift
checked_at: 2026-10-04T21:21:59Z
health_status: critical-issues
context_type: brownfield
language_family: python
stack_assessment_available: true
checks_run:
  - lockfile
  - dependency_audit
  - outdated_deps
  - test_runner
  - ci_cd
  - configuration
audit_findings:
  critical: 0
  high: 0
  moderate: 0
  low: 0
test_runner_detected: false
ci_provider: null
recommended_fixes: 5
---

## Dependency Health

### Lockfile

```
Status: present (uv.lock)
Package manager: uv
```

`uv.lock` resolves 20 packages: the direct dependencies `fastapi 0.142.2` and `uvicorn 0.54.0`, plus the dev dependency `mypy 2.4.0`.

### Security Audit

```
Tool: pip-audit (run as `uvx pip-audit -r <uv export --all-groups --no-emit-project> --format json`)
Summary: 0 CRITICAL, 0 HIGH, 0 MODERATE, 0 LOW
Direct vs transitive: not distinguished by this tool
```

No known vulnerabilities were found across the 19 audited dependencies.

### Outdated Dependencies

```
Packages with major version gaps: 0
```

`uv tree --outdated --depth 1` reports every direct dependency (fastapi, uvicorn, mypy) at its latest version.

## Test Suite

```
Test runner: not detected
Tests found: not applicable
Test execution: not attempted
```

⚠ No test runner was detected. The agent cannot verify its own changes:
- pytest is not in the dependencies.
- There is no `[tool.pytest.ini_options]` section, no `pytest.ini` and no `tox.ini`.
- There is no `tests/` directory.

The FastAPI app module also does not exist yet. `src/linksift/__init__.py` contains only a hello-world `main()`, so there is nothing to test against.

Recommended setup: pytest, with httpx for `TestClient` (see Recommended Fixes #1).

## CI/CD

```
Provider: not detected
Configuration: not found
```

| Stage      | Status | Notes          |
|------------|--------|----------------|
| Lint       | ✗      | not configured |
| Test       | ✗      | not configured |
| Build      | ✗      | not configured |
| Type check | ✗      | not configured |
| Security   | ✗      | not configured |

ℹ No CI/CD configuration was detected. You'll set this up in the infrastructure and deployment lesson. `context/foundation/tech-stack.md` already plans GitHub Actions with auto-deploy to Render. For now, a local test runner is sufficient for agent collaboration.

## Configuration

### High severity

No high-severity gaps. `.gitignore` is present, and the `mypy` strict config is in `pyproject.toml`.

### Medium severity

- **Linter/formatter (ruff)** — Python has no linter or formatter configured: there is no `[tool.ruff]` section, no `ruff.toml` and no black. Without one, code style will drift between agent sessions, and unused imports or unsorted imports will pile up. Fix: see Recommended Fixes #2.
- **`.gitignore` does not cover `.env`** — The project will soon hold Supabase, OpenRouter and X API keys, but `.env` is not ignored, so one `git add .` would commit secrets. Fix: see Recommended Fixes #3.

### Low severity

- **`.env.example`** — The required environment variables are not documented. Fix: see Recommended Fixes #3.
- **`.editorconfig`** — There are no editor-agnostic settings for indentation and line endings. Fix: see Recommended Fixes #5.
- **No initial commit** — `git` is initialised on `main` but has no commits, and every file is untracked. Without a baseline, there is no diff to review agent changes against and no way to roll back. Fix: see Recommended Fixes #4.

## Stack Assessment Cross-Reference

```
Stack assessment: context/foundation/stack-assessment.md
Agent readiness (from stack-assess): ready-with-compensation
```

| Quality Gate Gap                        | Health-Check Finding                                                                                     | Status                  |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------|-------------------------|
| typed: partial (no type checker)        | mypy 2.4.0 strict + `pydantic.mypy` plugin now configured in `pyproject.toml`; `uv run mypy` passes. Not yet enforced anywhere (no CI, no hook, no CLAUDE.md rule). | Partially mitigated     |
| convention_based: fail (FastAPI layout) | No `CLAUDE.md` / `AGENTS.md`, `README.md` is empty; the recommended layout rules are not on disk yet.     | Reinforced (open)       |
| popular_in_training: partial (uv_build) | No instruction file pins the uv-only commands, so agents may still fall back to `pip install`.           | Open                    |
| test runner missing                     | Confirmed: no pytest, no tests directory.                                                                 | Reinforced              |
| version drift (Pydantic v2, lifespan)   | No instruction file pins versions or idioms.                                                              | Open                    |

Type safety is now only half in place. mypy runs cleanly when someone calls it, but nothing calls it automatically. Until a `CLAUDE.md` rule, a hook or a CI step runs it, agents will not run it by themselves.

The stack assessment's `ready-with-compensation` verdict assumes that its compensation entries exist. None of them are on disk yet. Writing them is the job of agent onboarding (Category B below).

## Recommended Fixes

### Fix before agent work (Category A)

### 1. Add a test runner (pytest)

**Impact**: Without a test runner, the agent has no feedback loop and cannot confirm that a change works. The deterministic score and verdict rule (FR-011, FR-018) is the most testable logic in the product and currently has no safety net.
**Severity**: critical
**Effort**: moderate (15–30 min, including the first real test once the app module exists)
**Fix**:

```bash
cd ~/dev/linksift
uv add --dev pytest httpx
mkdir -p tests
```

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

Create a first test in `tests/test_smoke.py`. Until the FastAPI app exists, a single assertion against `linksift` will do. Then check it with `uv run pytest`. pytest exits with code 5 when no tests are collected, so at least one test is required.

### 2. Add a linter and formatter (ruff)

**Impact**: Agent output stays consistent across sessions, and ruff catches unused imports, missing annotations and import order before mypy or tests do.
**Severity**: medium
**Effort**: quick (< 5 min)
**Fix**:

```bash
uv add --dev ruff
```

Add to `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "ANN"]
```

Verify: `uv run ruff check . && uv run ruff format --check .`

### 3. Ignore `.env` and document environment variables

**Impact**: Keys for Supabase, OpenRouter and the X API are coming in the next slices. If an agent runs `git add .` while `.env` is not ignored, it commits secrets.
**Severity**: medium
**Effort**: quick (< 5 min)
**Fix**:

```bash
printf '\n# Environment\n.env\n.env.*\n!.env.example\n' >> .gitignore
cat > .env.example <<'EOF'
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
OPENROUTER_API_KEY=
X_API_BEARER_TOKEN=
EOF
```

Adjust the variable names to match the code once it reads them.

### 4. Make the initial commit

**Impact**: Without a baseline commit there is no `git diff` to review agent changes against and no way to roll back a bad session.
**Severity**: low
**Effort**: quick (< 5 min)
**Fix** (after #3, so that `.env` is already ignored):

```bash
git add . && git commit -m "chore: bootstrap linksift (FastAPI + uv + mypy)"
```

### 5. Add `.editorconfig`

**Impact**: Indentation and line endings stay consistent between editors and agent-written files. This is a convenience, not a blocker.
**Severity**: low
**Effort**: quick (< 5 min)
**Fix**:

```bash
cat > .editorconfig <<'EOF'
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{toml,yml,yaml,json,md}]
indent_style = space
indent_size = 2
EOF
```

### Addressed in upcoming lessons (Category B)

### Agent instruction file (CLAUDE.md / AGENTS.md)

**Lesson**: [Agent Onboarding: Agents.md, AI Rules i feedback loops (M1L4)](https://platforma.przeprogramowani.pl/external/10xdevs-3/m1-l4)
**What you'll do there**: Write the instruction file. You can bring in the entries already prepared in `stack-assessment.md` (layout, uv-only commands, typing rules, Pydantic v2 / lifespan idioms) and wire `uv run mypy`, `uv run ruff` and `uv run pytest` into the agent's feedback loop.

### CI/CD pipeline (GitHub Actions)

**Lesson**: [Sprint Zero z Agentem: infrastruktura, walking skeleton i pierwszy deploy (M1L5)](https://platforma.przeprogramowani.pl/external/10xdevs-3/m1-l5)
**What you'll do there**: Set up the planned GitHub Actions workflow. It should cover lint (ruff), type check (mypy), tests (pytest) and a dependency audit (pip-audit), with auto-deploy on merge.

### Deployment configuration (Render)

**Lesson**: [Sprint Zero z Agentem: infrastruktura, walking skeleton i pierwszy deploy (M1L5)](https://platforma.przeprogramowani.pl/external/10xdevs-3/m1-l5)
**What you'll do there**: Add the Render service config (`render.yaml` or dashboard settings, with a start command such as `uv run uvicorn linksift.main:app --host 0.0.0.0 --port $PORT`) and ship a walking skeleton.

## Summary

Health status: critical-issues

The dependency tree is clean. It has a lockfile, zero known vulnerabilities and no outdated packages, and strict type checking with mypy and the Pydantic plugin is now configured and passing. The verdict is driven by a single finding: there is no test runner, so the agent cannot verify its own changes. Linting and secrets hygiene (`.env`) are smaller gaps that take minutes to close. The project is a fresh scaffold with no app module and no commits yet, so all of this is cheap to fix now. With pytest added, the status would move to needs-attention, or to healthy once ruff and the `.gitignore` fix are also in.

Next step: apply fixes #1–#4 (about 30 minutes in total), then proceed to agent onboarding (M1L4) to turn the stack-assessment compensation entries into a real `CLAUDE.md`.
