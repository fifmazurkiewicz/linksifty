# Evidence — editable rubric

## Behavior and deliberate regressions

- Red: rubric domain test failed collection before the new domain module existed;
  API tests failed before update_settings existed; frontend tests failed for
  missing editable fields and historical rules before UI implementation.
- Green: mixed-score calculation defaults to 26.67%, novelty weight 10 gives
  58.10%. Existing default scoring tests pass.
- Deliberate break: ignored custom weights; domain/new analysis/cached recovery
  tests all failed (3 failed, 18 passed). Restored implementation.
- Deliberate break: sent an empty rubric in frontend PUT; threshold/payload tests
  failed (2 failed, 4 passed). Restored implementation.
- Adapter test inspects actual mocked request rubric/source messages, rejects
  invented citation despite hostile rule text, retains actual cost and calls once.

## Database

Existing installed PostgreSQL 17/pgTAP runtime, loopback 127.0.0.1:55439 only;
synthetic local runner and fresh `linksifty_rubric_test` database. Applied all
nine migrations. Gate runs all seven SQL suites, plus concurrent budget,
duplicate submission and settings-update/reservation tests. No hosted data read.
31 new pgTAP rubric assertions passed, including atomic rejection, owner isolation,
restricted grants, immutable recovery snapshot, authoritative completion snapshot
and explicit fresh-analysis reset.

The initial SQL run caught copying an obsolete paste function that used digest;
restored 000006's built-in SHA256, then all existing SQL suites passed.
Concurrency fixture numeric decoding was corrected from int('60.0') to Decimal.
A second fresh `linksifty_rubric_upgrade_test` database applied 000001–000008,
seeded legacy reservation/completed-result fixtures, applied 000009, then edited
current settings. Assertions confirmed old job/reservation/assessment snapshots
retain defaults and historical score 60 remains unchanged.

Reproducible main gate (explicit disposable URL has no real credentials):
`PATH=/opt/homebrew/opt/postgresql@17/bin:$PATH UV_CACHE_DIR=/private/tmp/linksifty-uv-cache LINKSIFTY_TEST_DATABASE_URL=postgresql://linksifty_test_runner@127.0.0.1:55439/linksifty_rubric_test uv run --package linksifty python backend/tests/integration/check_processing_database.py`.

## Browser

Temporary local Vite harness imports actual SettingsPanel, ThemeToggle and CSS,
with synthetic session and mocked settings GET/PUT; external fetches blocked.
Edited Polish description and weight 10, saved, observed success. At 390px,
document width was exactly 390px, eight fieldsets present; Tab from novelty
description focused its weight with visible outline. Light/mobile and dark/
desktop screenshots inspected. Final captures: `/private/tmp/linksifty-rubric-mobile.png`
and `/private/tmp/linksifty-rubric-desktop.png`. No live authentication/provider call.
Harness will be removed after verification; production routes are unchanged.

## Final gates

- Full backend tests: 163 passed; one existing Starlette/httpx deprecation warning.
- Strict mypy: 34 source files pass. Ruff lint/format pass (87 files).
- Frontend: 32 tests pass, lint clean, production build succeeds.
- Toolkit check: clean. `git diff --check`: clean.
- SQL: 120 pgTAP assertions across seven suites plus all three concurrency
  checks pass. Separate legacy-upgrade assertions passed.
- Shared frontend rubric types/validation live in lib/rubric.ts (used by settings,
  historical detail and API types), avoiding a lib-to-feature dependency.
- Archify architecture `finalize` passes validate/deliver/strict check/browser-check,
  with zero diagnostics. Canonical source/HTML/receipts are under docs/architecture.
  Sources pin local immutable revision 053f110ffee2041d880391816f064219e0b3d716.
  Browser used the already-installed Playwright Chromium headless shell through
  ARCHIFY_CHROME; sandbox launch first failed, then authorized local execution
  passed. No browser/tool was installed. The default locator did not find Chrome.
  A previous evidence-path conflict was resolved by preserving old generated
  evidence in /private/tmp before regenerating the canonical receipts.
- Diagram visualReview is not-requested; its automated browser gate passed.
  GUI screenshots were manually inspected separately. No diagram screenshot
  was inspected and no perceptual diagram-quality claim is made.
- Archify reports installed 3.0.1 / available 3.1.0; installed skill unchanged.
- Implementation self-review approved; verified SHA256 regression disposition
  recorded in reviews/review-decisions.md before its derived board.
- Temporary GUI harness removed and Vite stopped. Local PostgreSQL was
  stopped cleanly with pg_ctl fast/wait; synthetic test DBs are retained for
  reproducibility. Final toolkit check and git diff --check pass.
