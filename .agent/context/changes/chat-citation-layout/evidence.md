# Citation layout verification

- Initial focused run: 4 failed, 6 passed before implementation (inline markers,
  grouped sources and passage disclosure missing).
- After implementation: 10 chat tests pass; frontend lint and build pass.
- Fixtures cover repeated URLs across paragraphs, duplicate citation occurrences,
  multiple excerpts, source list below the answer, distinct answer anchors,
  saved context without URLs, unsafe URL exclusion and empty/refusal states.
- All API interactions use synthetic fixtures; no provider, search or real owner
  content is used. Native links/details preserve the established semantic UI.

## Required gates

- Frontend `npm test -- --run`: 93 passed; `npm run lint` and `npm run build`: pass.
- `uv run --offline --package linksifty mypy --strict backend/src`: pass, 50 files.
- `uv run --offline --package linksifty ruff check .`: pass.
- `uv run --offline --package linksifty ruff format --check .`: pass, 133 files.
- `agent-toolkit check`: exit 127, command not installed; no installation attempted.
- Python commands use UV_CACHE_DIR=/private/tmp/linksifty-uv-cache.
- No backend implementation changed; no backend behavior test rerun is required.

## Deliberate regression

Temporarily replaced citationKey with passage_id grouping. The repeated-source
test fails (1 failed / 9 skipped) because the same source no longer reuses its
inline reference. Restored original source in finally; ten focused tests pass.

## Native browser QA

Used an isolated loopback preview with synthetic API responses and no live model,
database or remote source calls. Desktop screenshot qa/desktop.jpg was visually
inspected: paragraphs show [1] and [1][2], with two source links below.
Pressing Enter on Source 1 sets the URL fragment and activeElement.id to the
source list entry. Enter on Quoted passages (2) expands both distinct excerpts.
This is actual native browser interaction; automated jsdom checks separately
verify unsafe URLs, saved context and unique destination IDs. No fixed mobile
viewport was tested. Preview harness/server are temporary and excluded from code.

Independent reviewer approves without actionable findings and reran ten focused
chat tests, frontend lint and scoped whitespace checks successfully. Full details
are in reviews/implementation-review.md. Temporary preview files/server have been
removed/stopped; qa/desktop.jpg remains as synthetic visual evidence. Verification
made no production read/write or deployment claim.

Publication preparation: owner authorized push. Fresh main matches the reviewed
base 3f945d5; only citation-layout files and their shared CSS hunk are selected.
The pre-existing admin badge CSS, README, App/admin/auth-flow changes remain local.
