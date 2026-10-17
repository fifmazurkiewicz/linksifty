# Verification evidence

2026-10-18. The user requested topic basics and practical relevance, then refined
the design so structure follows the topic/theme/article rather than a template.

## Red, green and deliberate break

- Before product changes, all four new request-contract cases failed on the
  missing topic-basics guidance. Cases cover rubric versions 1/2 and both fluent
  prose and optional sections/bullets.
- After implementation, 30 relevant mocked backend tests passed. The contract
  checks the actual HTTP request and summary property description, supplied
  primary passages, a single model call, and exact preservation of returned text.
- The existing processing-completion test now verifies that the multiline note
  reaches the completed assessment unchanged, alongside its existing checks for
  reserved rubric/threshold, deterministic scoring, costs and exact citations.
- Deliberately removed the shared guidance from the outgoing system message.
  All four request-contract cases failed. Restored the implementation in a
  `finally` block, then reran the passing focused suite.

## Commands and results

From repository root, using the existing uv workspace and a temporary cache:

```sh
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty pytest backend/tests/unit/test_informative_summaries.py backend/tests/unit/test_openrouter.py backend/tests/unit/test_calibrated_provider.py backend/tests/unit/test_processing_service.py backend/tests/unit/test_processing_failures.py backend/tests/unit/test_calibrated_processing.py -q
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty mypy --strict backend/src
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty ruff check .
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty ruff format --check .
git diff --check
agent-toolkit check
```

- Tests: 30 passed. Existing Starlette TestClient/httpx deprecation warning only.
- Strict mypy: 34 source files, no issues.
- Ruff lint: passed after splitting one overlong prompt literal without changing
  the concatenated message. Ruff format: 93 files already formatted.
- Whitespace check: passed.
- Toolkit: unavailable (`command not found`), consistent with the previous change;
  no tool installation or release-gate waiver is claimed.

## Scope and limitations

Only provider generation instructions, response-field description, tests and
product documentation changed. Existing note shape, 6000-character maximum,
4096 output-token cap, price ceilings and reservation accounting remain in place.
Prompt/context budgeting includes the new guidance and schema description; the
existing 20-source/context-limit and incomplete-output/paid-retry tests pass.

No frontend change, schema migration, extra model request, score recalculation,
automatic summary rewrite, deployed change or paid model-quality evaluation.
Mocked writing samples demonstrate transport/preservation, not factual accuracy
or writing quality of a live model. A live sample remains an explicitly authorized
future check. Existing cached/completed results retain their saved summaries.

Graft is unavailable in this session; focused source and existing docs were used.

## Pre-push verification

2026-10-18: User authorized a direct push to `main`. Repeated the 30-test focused
suite, strict mypy, Ruff check, Ruff format check and whitespace check; all pass.
Toolkit still reports command not found. Fetched origin/main has no divergent
commits relative to local HEAD before committing the change.
