# Linksifty Setup Implementation Plan

**Goal:** Create independent Linksifty repository with agent-toolkit support for Codex, Cursor, and Claude Code and durable product documentation.

**Architecture:** Copy the LinkSift seed without local artifacts, then rename the Python package and product documentation. Agent-toolkit 1.2 generates its managed standard and runtime skills. Linksifty rules remain outside generated blocks. This work does not implement product functionality.

**Tech Stack:** Python 3.11, FastAPI, uv, agent-toolkit 1.2 web profile, TOML, YAML, Markdown.

**Spec:** outputs/linksifty-setup-design.md

## Global Constraints

- Source: /Users/Filip/dev/linksift. Destination: /Users/Filip/dev/linksifty.
- Preserve source unchanged; exclude .git, .venv, caches, .env, and editor-local files.
- Rename distribution, console command, package directory, and project-owned docs to linksifty.
- Select web profile and clients codex, cursor, claude.
- Do not implement product flows, provision services, use credentials, or call paid APIs.

## Review Focus

- No source runtime artifact or secret enters the new repository.
- Package directory, distribution name, and console command agree on linksifty.
- Agent-toolkit check passes for all three clients with no writes.
- Linksifty rules survive future toolkit updates.
- Rules protect user isolation, manual-content fallback, secrets, and tests from paid calls.

---

### Task 1: Establish a clean independent seed

**Files:**
- Create: /Users/Filip/dev/linksifty
- Copy: .gitignore, .python-version, README.md, pyproject.toml, uv.lock, src, context
- Exclude: .git, .venv, .mypy_cache, .pytest_cache, __pycache__, .env

**Interfaces:**
- Consumes: the LinkSift seed.
- Produces: independent Git repository with inherited requirements.

- [ ] **Step 1: Validate state**

~~~
test ! -e /Users/Filip/dev/linksifty
git -C /Users/Filip/dev/linksift status --short
~~~

Expected: destination does not exist; source is only observed.

- [ ] **Step 2: Copy declared files and initialize Git**

Copy only the listed paths. Then run:

~~~
git -C /Users/Filip/dev/linksifty init -b main
git -C /Users/Filip/dev/linksifty status --short
~~~

Expected: copied inputs are untracked.

- [ ] **Step 3: Verify exclusions**

~~~
find /Users/Filip/dev/linksifty -type d \( -name .venv -o -name .mypy_cache -o -name .pytest_cache -o -name __pycache__ \) -print
find /Users/Filip/dev/linksifty -type f -name .env -print
~~~

Expected: no output.

- [ ] **Step 4: Commit the seed**

~~~
git -C /Users/Filip/dev/linksifty add .gitignore .python-version README.md pyproject.toml uv.lock src context
git -C /Users/Filip/dev/linksifty commit -m "chore: initialize linksifty from linksift seed"
~~~

### Task 2: Rebrand the Python project

**Files:**
- Modify: pyproject.toml, README.md, inherited product documents
- Move: src/linksift to src/linksifty
- Modify: src/linksifty/__init__.py

**Interfaces:**
- Consumes: copied seed repository.
- Produces: linksifty distribution with linksifty console command.

- [ ] **Step 1: Update metadata**

Set name to linksifty, description to “Linksifty turns saved links into source-grounded notes and a repeatable value verdict.”, and command to linksifty = linksifty:main.

- [ ] **Step 2: Rename and update the package**

Move source directory and change main output to Hello from linksifty!.

- [ ] **Step 3: Rebrand project documentation**

Replace product name with Linksifty while retaining requirements, decisions, acceptance criteria, and historical dates.

- [ ] **Step 4: Verify and commit**

~~~
uv --directory /Users/Filip/dev/linksifty run linksifty
git -C /Users/Filip/dev/linksifty add pyproject.toml README.md src context
git -C /Users/Filip/dev/linksifty commit -m "chore: rebrand project as linksifty"
~~~

Expected: command prints Hello from linksifty!.

### Task 3: Generate the shared agent environment

**Files:**
- Create: .agent/manifest.yaml, .agent/lock.yaml, .agents/skills, .claude/skills
- Create or modify: AGENTS.md, CLAUDE.md, .cursor/mcp.json, .mcp.json, .codex/config.toml

**Interfaces:**
- Consumes: local toolkit checkout at /Users/Filip/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/agent-toolkit.
- Produces: web-profile instructions, skills, and MCP configuration for all three clients.

- [ ] **Step 1: Initialize and install**

~~~
uv run --project /Users/Filip/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/agent-toolkit agent-toolkit --project /Users/Filip/dev/linksifty init --profile web
uv run --project /Users/Filip/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/agent-toolkit agent-toolkit --project /Users/Filip/dev/linksifty install
~~~

Expected: manifest includes cursor, codex, claude; skill copies are normal files.

- [ ] **Step 2: Validate and commit**

~~~
uv run --project /Users/Filip/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/agent-toolkit agent-toolkit --project /Users/Filip/dev/linksifty check
git -C /Users/Filip/dev/linksifty add AGENTS.md CLAUDE.md .agent .agents .claude .cursor .codex .mcp.json
git -C /Users/Filip/dev/linksifty commit -m "chore: add agent toolkit workflow"
~~~

Expected: check exits 0 without writes.

### Task 4: Add Linksifty-owned rules and quality gates

**Files:**
- Modify: AGENTS.md, pyproject.toml, .gitignore, uv.lock
- Create: .env.example, tests/test_package.py

**Interfaces:**
- Consumes: toolkit baseline.
- Produces: durable project conventions and executable checks.

- [ ] **Step 1: Add instructions outside generated markers**

Require uv only; Python 3.11+, FastAPI and Pydantic v2; strict typing; framework-free services; pure deterministic scoring; no note after failed or partial fetch; user-scoped data including admins; server-only secrets; mocked paid calls; tests, mypy, Ruff, and toolkit check before completion.

- [ ] **Step 2: Add development tools**

~~~
uv --directory /Users/Filip/dev/linksifty add --dev pytest httpx ruff
~~~

Configure test path tests, strict mypy package linksifty, and Ruff selections E, F, I, UP, B, ANN.

- [ ] **Step 3: Add safe environment and package test**

Create .env.example with names SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, OPENROUTER_API_KEY, X_API_BEARER_TOKEN and empty values. Ignore .env but track .env.example. Test that main is callable from linksifty.

- [ ] **Step 4: Verify and commit**

~~~
uv --directory /Users/Filip/dev/linksifty run pytest
uv --directory /Users/Filip/dev/linksifty run mypy src
uv --directory /Users/Filip/dev/linksifty run ruff check .
uv --directory /Users/Filip/dev/linksifty run ruff format --check .
uv run --project /Users/Filip/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/agent-toolkit agent-toolkit --project /Users/Filip/dev/linksifty check
git -C /Users/Filip/dev/linksifty add AGENTS.md pyproject.toml uv.lock .gitignore .env.example tests
git -C /Users/Filip/dev/linksifty commit -m "chore: add linksifty engineering rules"
~~~

Expected: all checks pass without product integrations.

### Task 5: Add vision, architecture, roadmap, and active context

**Files:**
- Create: docs/product/vision.md, docs/architecture/overview.md, docs/roadmap.md
- Create: docs/superpowers/specs/2026-10-04-linksifty-setup-design.md
- Create: docs/superpowers/plans/2026-10-04-linksifty-setup.md
- Create: .agent/context/changes/mvp-foundation/change.md, frame.md, decisions.md, plan.md, progress.md, evidence.md

**Interfaces:**
- Consumes: inherited foundation requirements and accepted setup design.
- Produces: implementation-ready product knowledge without feature code.

- [ ] **Step 1: Write vision and architecture**

Vision includes primary user, source-grounded promise, eight criteria, deterministic verdict, success measures, non-goals, and 2026-11-04 deadline. Architecture names future frontend, API, Supabase Auth/Postgres/RLS, worker, fetchers, OpenRouter, trust boundaries, manual fallback, and pure scoring.

- [ ] **Step 2: Write roadmap and change record**

Roadmap: foundation; identity/isolation; submission/fallback; assessment/scoring/cost cap; inbox; integrations/chat; production readiness. Referenced-link checks and chat are cut-line candidates. Change record begins with MVP Foundation and planned status, preserving inherited decisions and prohibiting paid calls during foundation work.

- [ ] **Step 3: Copy approved design and plan, verify, and commit**

~~~
test -f /Users/Filip/dev/linksifty/docs/product/vision.md
test -f /Users/Filip/dev/linksifty/docs/architecture/overview.md
test -f /Users/Filip/dev/linksifty/docs/roadmap.md
test -f /Users/Filip/dev/linksifty/.agent/context/changes/mvp-foundation/progress.md
git -C /Users/Filip/dev/linksifty add docs .agent/context
git -C /Users/Filip/dev/linksifty commit -m "docs: define linksifty vision and roadmap"
~~~

### Task 6: Final validation and handoff

**Files:**
- Modify: .agent/context/changes/mvp-foundation/evidence.md

**Interfaces:**
- Consumes: complete setup repository.
- Produces: recorded evidence and clean setup history.

- [ ] **Step 1: Run final verification**

~~~
git -C /Users/Filip/dev/linksift status --short
git -C /Users/Filip/dev/linksifty status --short --branch
uv --directory /Users/Filip/dev/linksifty run pytest
uv --directory /Users/Filip/dev/linksifty run mypy src
uv --directory /Users/Filip/dev/linksifty run ruff check .
uv --directory /Users/Filip/dev/linksifty run ruff format --check .
uv run --project /Users/Filip/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/agent-toolkit agent-toolkit --project /Users/Filip/dev/linksifty check
~~~

Expected: destination is clean, all commands exit 0, source remains unchanged.

- [ ] **Step 2: Record and commit evidence**

Record commands, date, exit results, and no use of paid APIs, Supabase project, or credentials. Then commit with message docs: record linksifty setup verification.

