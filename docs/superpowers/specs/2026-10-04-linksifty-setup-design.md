# Linksifty — Project Setup Design

**Date:** 2026-10-04  
**Status:** ready for review  
**Source:** `/Users/Filip/dev/linksift`  
**Destination:** `/Users/Filip/dev/linksifty`

## Purpose

Linksifty is the agent-toolkit-assisted implementation of the existing LinkSift MVP. It is intentionally compared with a second implementation of the same product made without agent-toolkit. The comparison is meaningful only if product requirements, baseline stack, and success criteria remain the same.

The product turns submitted article and X links into a concise source-grounded note, eight-criterion assessment, deterministic value score, and verdict: `valuable`, `to_review`, or `hype`. It serves an authenticated, approved user with isolated data, a mobile-friendly inbox, manual-content fallback, cost limits, and per-item chat.

## Scope of this setup

1. Copy the source project into a sibling directory without modifying the original.
2. Rebrand package and project metadata from `linksift` to `linksifty`; preserve the product requirements while replacing product naming in project-owned documents.
3. Initialize agent-toolkit 1.2 with the `web` profile for `codex`, `cursor`, and `claude`.
4. Generate and validate the toolkit-managed files: `.agent/manifest.yaml`, `.agent/lock.yaml`, `AGENTS.md`, `CLAUDE.md`, `.agents/skills/`, `.claude/skills/`, MCP configuration for all three clients, and `.codex/config.toml` managed Graft entry.
5. Add project-owned rules outside toolkit-managed blocks: Python/FastAPI and React conventions, `uv`-only dependency workflow, strict typing, test and verification gates, data-isolation requirements, no-hallucination handling, and cost/secret boundaries.
6. Normalize the project context under `.agent/context/` and create the first change record for the MVP implementation plan.
7. Record a product vision, architectural boundaries, delivery roadmap, and an implementation plan for the first independently shippable milestone.
8. Verify the resulting toolkit state with `agent-toolkit check` and verify that project metadata is consistently named `linksifty`.

## Explicit non-goals

- No frontend, routes, database schema, Supabase project, external credentials, deployment, or product feature implementation in this setup phase.
- No changes to `/Users/Filip/dev/linksift`.
- No attempt to make the non-toolkit implementation identical in process; it only shares the product contract and baseline stack.
- No global installation of the toolkit. The local checked-out agent-toolkit source is used reproducibly for this setup.

## Architecture and operating model

The repository is a single product workspace: FastAPI/Python API under `src/linksifty/` and a future Vite/React TypeScript client under `web/`. Supabase will own Auth and PostgreSQL with RLS; FastAPI owns server-side integrations, business rules, and background work; OpenRouter and X remain server-side integrations. The deterministic scoring rule is future pure domain code, separate from fetching, LLM assessment, HTTP routes, and database access.

The toolkit is a versioned delivery standard, not a product dependency. `.agent/manifest.yaml` declares the desired setup; `.agent/lock.yaml` detects drift. Agent-toolkit owns generated runtime skills and its marked instruction blocks only. Product-specific instructions live outside those blocks so toolkit upgrades remain safe.

All three clients read one shared root `AGENTS.md`; Claude Code additionally reads a generated `CLAUDE.md` import, and all clients receive their appropriate vendored skill locations. Graft is configured as the common MCP knowledge layer. If it is unavailable, agents use focused `rg` and state that limitation in change evidence.

## Project rules

- Package management is `uv` only. Agents do not use `pip install`, manually edit `uv.lock`, or create a second virtual environment.
- Python is 3.11+ with FastAPI, Pydantic v2 and strict mypy. All API, LLM, fetcher, and database boundaries use typed models.
- A route has HTTP concerns only; domain services have no FastAPI request/response types; scoring is pure and has one source of truth.
- A failed or partial fetch never produces a summary. It becomes an explicit manual-content request.
- Every item, note, assessment, and chat query is scoped to the authenticated user, including for administrators. Admin capabilities concern account approval only.
- Secrets are server-only, supplied by environment variables, excluded from Git, and represented by a committed `.env.example` without values.
- Any business-rule change leaves focused tests. Before a task is complete, run the relevant tests, type checking, linting/formatting, and toolkit drift check.
- The first implementation milestone must not create real paid external requests in automated tests.

## Planned documentation

- `docs/product/vision.md` — user problem, product promise, MVP contract, measures of success, non-goals.
- `docs/architecture/overview.md` — boundaries, data flow, trust boundaries, and explicit integration seams.
- `docs/roadmap.md` — ordered MVP milestones, including cut-line candidates if the deadline is at risk.
- `.agent/context/changes/mvp-foundation/` — framed change, decisions, plan, execution progress, verification evidence, and reviews.
- `docs/superpowers/specs/` and `docs/superpowers/plans/` — durable design and task-level implementation plan generated in the approved agent workflow.

## Delivery milestones after setup

1. Foundation: app shells, conventions, quality gates, and a local development contract.
2. Identity and isolation: Supabase auth, pending/approved accounts, RLS, and admin account approval.
3. Submission pipeline: bounded multi-link input, duplicate detection, processing lifecycle, and manual-content fallback.
4. Assessment: source-grounded note, structured eight-criterion model output, deterministic scoring, verdicts, spend controls.
5. Inbox: responsive list, verdict filters, read/delete actions, and processing state.
6. Integrations: article fetcher, X API, referenced-link checks, then item chat.
7. Production readiness: CI, deployment configuration, observability, security review, and the 20-link verdict-agreement evaluation.

## Verification of setup

- The source folder remains unchanged; destination is a separate Git repository.
- `pyproject.toml`, console script, source package path, and user-facing product docs use `linksifty`.
- `agent-toolkit check` reports no drift.
- Generated client files include all three clients and the web profile skill set.
- Root rules specify concrete verification commands and product guardrails without duplicating toolkit-managed content.
- No tracked secret, `.venv`, cache, or local environment file is copied into the destination repository.

## Comparison boundary

Both agent runs use the same MVP requirements and success criteria from the inherited foundation material. Linksifty additionally records decisions and evidence in `.agent/context/`, uses vendored skills selected by its manifest, and verifies standard drift. The comparison should evaluate delivery quality, reproducibility, verification evidence, and outcome — not whether the repositories have matching file layouts.
