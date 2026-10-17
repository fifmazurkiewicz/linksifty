# Verification evidence

2026-10-17. Bounded design approved in chat; no changes to provider prompts,
stored assessment content, score calculation, database or paid integrations.

## Behavior verification

- Initial red: `npm test -- --run tests/assessment.test.tsx` failed 8 of 9 tests
  before implementation (missing article heading and disclosures, always-visible
  evidence and missing compact research states).
- Budget red: `npm test -- --run tests/settings-usage.test.tsx --reporter=dot`
  failed the new compact-budget test before its implementation.
- Green: all 47 frontend tests pass across six files on the final source.
  Coverage includes title/source propagation from the actual inbox, independent
  analysis/research disclosures, exact inline quotations, saved historical
  descriptions and weights, coverage/unscored/legacy states, visible hype
  warnings, research uncertainty, unsafe/malformed URLs, loading/errors,
  back navigation, and expandable budget/reservations.
- Deliberate break: setting the Analysis disclosure to `open` initially caused
  two assessment tests to fail. Restored the original implementation and reran
  the complete passing suite.

## Final automated gates

Commands ran from `frontend/` for npm and repository root for uv:

- `npm test -- --run`: 47 tests passed, six files.
- `npm run lint`: passed.
- `npm run build`: TypeScript and Vite build passed.
- `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty mypy --strict backend/src`:
  passed, 34 source files.
- `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty ruff check .`:
  passed.
- `UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty ruff format --check .`:
  passed, 92 files.
- `git diff --check`: passed.
- `agent-toolkit check`: unavailable (`command not found`). Existing-checkout
  fallback `.venv/bin/python -m agent_toolkit --project /Users/Filip/dev/linksifty check`
  also unavailable (`No module named agent_toolkit`). No tool was installed.

## Browser verification

Used a temporary local Vite entry rendering the real App with mock authentication,
public IKE example content and mocked API responses. No remote or paid API calls.
The fixture intentionally contains sample explanations and scores, not a fresh
assessment. Temporary source/HTML were removed after inspection.

- Desktop 1280px: title/source hierarchy, larger summary, compact verdict,
  independently closed disclosure rows, and compact sidebar budget inspected.
- Mobile 390px and 320px: inspected title wrapping, summary text, stacked research
  status, criterion/score layout and exact quoted evidence in normal page flow.
- Light and dark theme inspected; existing palette retained.
- Enter expanded/collapsed Analysis; Space opened exact evidence inline. Native
  accessibility state announced collapsed/expanded correctly.
- Source checking could expand while Analysis remained open. Evidence retained
  its own open state when Analysis was closed and reopened.
- Enter expanded the sidebar budget, exposing spent/reserved/limit/available
  values and reservation explanation. Collapsed accessible name retains funds
  available and reservation state.
- Temporary browser viewport override reset after verification.

Screenshots (temporary local artifacts):

- `/private/tmp/linksifty-assessment-desktop.png`
- `/private/tmp/linksifty-assessment-desktop-dark.png`
- `/private/tmp/linksifty-assessment-mobile.png`

Graft is unavailable in this session; repository documentation and focused source
searches supplied context. Hosted deployment and live-account verification were
not performed.

## Pre-push verification, 2026-10-18

User explicitly requested a push to `main`. Repeated the complete frontend
suite (47 passing tests), lint, build, strict mypy, Ruff check, Ruff format check
and whitespace checks on the final source; all pass. `agent-toolkit check` still
reports command not found. After `git fetch origin main`, HEAD and origin/main
had no divergent commits. No email-login implementation is included.
