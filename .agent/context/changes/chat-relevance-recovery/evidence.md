# Evidence — chat relevance recovery

## Observations and decision basis

The owner supplied a current trace with scope choice relevant, probabilities
0.86/0.13/0.01 and confidence 0.79. Language chooses pl with probability 0.6
and confidence 0.2. Reported classifier cost is USD 0.000213864. These are
provider/telemetry observations, not a fresh ledger settlement audit.

The classification state begins with serialized rubric_snapshot; repository
inspection confirms the first 6,000 bytes of serialized assessment passages were
used as topic context. Depending on rubric size, the summary may be truncated.

Verified 2026-10-21: TypeSafe's official confidence documentation defines Choice
confidence as (p_max - 1/n)/(1 - 1/n), and explicitly supports using top probability
for application-specific decisions. For n=3 and p_max=0.86, confidence is 0.79.
The original 0.8 confidence gate effectively required p_max >=0.8666667.

- https://docs.typesafe.ai/confidence
- https://openrouter.ai/blog/insights/what-is-jev/

The selected-probability cutoff of 0.8 is a deliberate routing policy for this
bounded, source-grounded chat, not a claim of measured model accuracy. Mocked
replays prove routing; they cannot prove future classifier/answer quality.

## Red and green

- Initial focused backend run: 15 failed / 64 passed when valid low-confidence
  choices still failed and fixed clarification was absent. Frontend: 1 failed /
  7 passed; historical failures still displayed the generic retry text.
- After the owner's search clarification, a real-adapter/mock-HTTP service replay
  failed first on rubric JSON displacing the summary, then on missing research
  citations because 0.79 confidence still routed to clarification.
- After repair: 93 focused chat/provider/telemetry tests pass. The screenshot's
  valid response reaches one mocked search, safely fetched evidence and a cited
  final answer; a duplicate request causes no new provider or search call.
- Boundary checks cover selected probability 0.799, 0.8 and 0.86 for all three
  categories in Polish/English, malformed decisions, safe fixed scope replies,
  preserved cost/ID and raw response telemetry. All remote/paid calls are mocked.

## Required checks and review

- `uv run --offline --package linksifty pytest backend/tests -q --tb=short`:
  595 pass, one existing Starlette/httpx deprecation warning.
- `uv run --offline --package linksifty mypy --strict backend/src`: pass, 50 files.
- `uv run --offline --package linksifty ruff check .`: pass.
- `uv run --offline --package linksifty ruff format --check .`: pass, 133 files.
- Frontend `npm test -- --run`: 91 pass; `npm run lint` and `npm run build`: pass.
- `agent-toolkit check`: exit 127, executable unavailable. Nothing installed.
- Deliberately replaced the probability comparison with the old confidence gate:
  the screenshot replay fails with missing research citations (1 failed, 34
  deselected). Restored source in finally; all 93 focused tests pass again.
- Independent reviewer found no actionable findings and reran 93 focused tests
  successfully; scope and verification limits in reviews/implementation-review.md.

All Python commands use `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache`, reusing
the installed locked environment. Graft is unavailable; focused source reads used.

## Diagram

Archify updates the existing English sequence contract in this change folder.
Validation, delivery and strict artifact checks pass; finalize exits 2 because
Chrome/Chromium is unavailable for browser QA. No perceptual review is claimed.
Specification SHA-256: d6fb4405babe4c22a0835b2f77c814bb526e28f59c84355a8ebc9e0a637db4ae.
Artifact SHA-256: b6bcac5aed063eb54137437b52af7ac18ad2be04fd4a45d13e4c56a1e7d88d86.
Receipts remain with editable chat-sequence.json and generated chat-sequence.html.

## External state

No hosted reads/writes, deployment, migration, paid inference or Brave request was
performed. Production behavior remains unchanged until matching backend/frontend
deployment. Tests do not establish live classifier calibration, search necessity,
source quality, or factual answer accuracy. Pre-existing user edits are preserved.

## Publication preparation

Owner authorized push to main. Fresh origin/main and local HEAD both identify
7dfd146 before this change. The staged set contains only chat source/tests,
chat documentation and this change folder; pre-existing README/admin/App/auth
edits are excluded. Source/document whitespace checks pass. The generated
diagram HTML retains renderer-written blank-line trailing whitespace to preserve
its artifact SHA-256 and associated validation receipts.
