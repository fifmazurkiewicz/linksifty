# Verification — 2026-10-18

No paid inference, hosted migration, deployment, external communication or secret
read was performed. Remote integrations are mocked; database fixtures are synthetic.

## Behavior

- Red: new contract imports initially fail. After adding types, all eight new
  service cases fail because rejected messages still answer and classification
  is never called. All 14 initial adapter cases fail because Jev is not implemented.
- Red/green: an added boolean-probability case initially accepts malformed output;
  strict numeric validation makes it fail closed.
- Green: service/adapter checks cover topic/history follow-ups, Polish/English
  off-topic and unsafe refusals, no answer/search/fetch after rejection, missing
  budget at classification and answer admission, uncertain/malformed/failed
  decisions, bounded input, price caps, preserved cost/ID, and no retries.
- Deliberate break: temporarily bypassed the refusal branch with `if False`.
  All four refusal tests fail, then original source bytes are restored.
- UI regression restores an uncited refusal without research/evidence badges and
  allows the reader to enter a subsequent relevant question.

## Required local checks

Commands use `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache` and `uv run --offline
--package linksifty`; existing installed dependencies are sufficient.

- `pytest backend/tests -q`: 309 pass; one existing TestClient deprecation warning.
- `mypy --strict backend/src`: pass, 40 files.
- `ruff check .`: pass.
- `ruff format --check .`: pass, 108 files.
- In frontend/: `npm test -- --run`: 65 pass; `npm run lint`: pass;
  `npm run build`: pass.
- `agent-toolkit check`: attempted, exit 127; executable unavailable.
- Graft unavailable; focused repository reads used instead. No tools installed.

## Real local PostgreSQL

Restarted the existing explicitly disposable cluster
`/private/tmp/linksifty-chat-pg-20261018` on loopback port 55443. The default sandbox
blocked shared memory; approved local execution succeeded. No hosted DB was used.

- Before migration: the new prerequisite assertion fails, and classification
  admission raises invalid_reservation, proving the SQL change is necessary.
- Applied 000014 and 000015 only to `linksifty_chat_checked_test`.
- `check_chat_database.py`: 39 pgTAP assertions and five overlapping-connection
  checks pass (shared cap, unique search, duplicate executor, unique classifier,
  deletion vs completion).
- `check_processing_database.py`: all 12 SQL suites plus six concurrency checks
  pass, including the classifier-updated chat suite and existing budget, duplicate,
  rubric, deletion and X-read behavior.
- SQL verifies owner isolation, settled classification replay rejection, actual
  classifier spend, retained generation ID, no answer slot before classification,
  zero-budget denial, and billing retention after content deletion.
- Cleanup: the temporary cluster directory was already absent, so pg_ctl could
  not stop it. A final pg_isready check returned no response on 127.0.0.1:55443;
  no unrelated server was stopped.

Reproduce against an already migrated disposable local database:

```sh
PATH=/opt/homebrew/opt/postgresql@17/bin:$PATH \
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache \
LINKSIFTY_TEST_DATABASE_URL=postgresql://linksifty_test_runner@127.0.0.1:55443/linksifty_chat_checked_test \
uv run --offline --package linksifty python backend/tests/integration/check_chat_database.py
```

## Diagram

The first workflow candidate hit routing/composition constraints; its editable
source and failure receipt are retained for diagnosis. A sequence diagram provides
the approved request/classification/refusal contract without those routing issues.

- `chat-sequence.json` / `chat-sequence.html`: showcase source validation,
  delivery and strict artifact checks pass.
- Finalize exits 2 (skipped) solely because Chrome/Chromium is unavailable.
  Browser evidence is skipped; visual review is not requested. This is not a
  successful complete finalize or a claim of perceptual inspection.
- Specification SHA-256: `7a251840ba6d5a4c2639361a296358bbc0f892af0bb421da5c801c0da6b21acb`.
- Artifact SHA-256: `07f18d3a3a3467103dc0e33de135107aff31d3849b23de147c8ac0435f2d9ae7`.
- Full receipts remain alongside both sources. Diagrams are English contract
  artifacts, not claims about a committed source snapshot or hosted deployment.
- Final focused service/provider regression rerun: 43 pass. Final Ruff lint/format
  and source diff checks pass after the prompt wording and documentation updates.
  The generated sequence HTML retains renderer-written trailing whitespace so its
  artifact hash and validation provenance remain intact; its staged whitespace
  check excludes blank-at-end-of-line warnings only.

## External acceptance

Apply 000015 before matching backend deployment; keep OPENROUTER_MODEL as the
answer model. Real Jev accuracy, the provisional 0.8 confidence threshold,
provider price-cap behavior and Decisions generation-ID lookup need separately
authorized live acceptance. Lookup failure leaves the charge reserved. Polish
and English refusal templates are supported; other languages use English.
