# Setup verification evidence

Verified on 2026-10-05 (Europe/Warsaw).

| Check | Result |
| --- | --- |
| `uv run linksifty` | Passed; printed `Hello from linksifty!`. |
| `uv run pytest` | Passed; 1 test passed. |
| `uv run mypy src` | Passed; no issues found. |
| `uv run ruff check .` | Passed. Vendored toolkit skill directories `.agent`, `.agents`, and `.claude` are excluded because they are lock-managed external source, not Linksifty application code. |
| `uv run ruff format --check .` | Passed; 20 files already formatted. |
| `agent-toolkit check` | Passed; toolkit state is clean. |
| Source isolation | `/Users/Filip/dev/linksift` still has only its pre-existing untracked `context/foundation/roadmap.md`; Linksifty did not modify it. |
| Secret and external-service use | No credentials, paid API, Supabase project, or external product service was used. |
