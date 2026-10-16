# Verification evidence

- RED: `test_passage_selection.py` fails both cases with `KeyError: passage_id`
  against the original adapter. The regression selects the provided Polish IKE
  source passage and asserts original typography, source attribution, cost and
  exactly one provider call; unknown IDs must fail closed.

- GREEN: 26 focused adapter/research/tracing tests passed; the full backend suite
  passed 164 tests. Strengthened the forged-source test to include a valid selected
  passage alongside prohibited quote/source fields; its 7-test research suite passes.
- Deliberate break: forced hydrated `source_id` to `primary`; the Polish IKE
  regression failed (`primary != iwuc`). Restored the original implementation in
  `finally` before the full green run.
- Long-source cases preserve every character, bound excerpts to the persisted
  schema, retain Unicode/whitespace and select the final passage successfully.
- End-to-end mocked research/provider/processing tracing verifies saved source URL,
  source ID and exact original offsets. Old persisted assessment contracts are
  unchanged; new provider output rejects extra source/quote fields.
- `uv run --package linksifty mypy --strict backend/src`: PASS, 33 source files.
- `uv run --package linksifty ruff check .`: PASS.
- `uv run --package linksifty ruff format --check .`: PASS, 86 files.
- `git diff --check`: PASS.
- Commands use `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache` because the default uv
  cache is outside the sandbox's writable roots; the existing project environment
  and lockfile are unchanged.
- `agent-toolkit check`: NOT RUN successfully; shell exit 127, command not found.
  Graft is also unavailable. No tool installation or waiver is inferred.
- Frontend/SQL were not changed. No live provider call, deployment or new cost.
  Existing test warning concerns Starlette's deprecated httpx TestClient adapter.
