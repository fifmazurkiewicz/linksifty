# Verification evidence

- Red: `pytest backend/tests/unit/test_output_language.py -q --tb=short` failed
  all four generation entrypoint cases before prompt changes.
- Green: the same four cases pass after shared English/Polish instructions.
- Deliberate break: replacing the shared restriction with an instruction to mirror
  the source language makes all four cases fail. Source restored in `finally`.
- Requests use HTTPX MockTransport and a local rejection response. These tests
  verify outgoing prompt policy, not a real model's translation quality or
  guaranteed language compliance. No paid/remote requests were made.
- Final checks: full backend suite passes 575 tests (one existing Starlette/httpx
  deprecation warning); strict mypy passes 50 source files; Ruff check and format
  check pass (133 files). `git diff --check` passes. Commands used
  `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache UV_OFFLINE=true uv run --package linksifty`.
- `agent-toolkit check` cannot run: command unavailable (exit 127).
- Independent reviewer approves with no actionable findings and independently
  reran the four new cases successfully. Reviewed both rubric versions, chat's
  pl/en contract across research rounds, previews, titles and existing refusals.
  No live model-language guarantee is claimed.
