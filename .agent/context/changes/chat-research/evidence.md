# Chat research evidence

Initial source inspection: a single decision/search/answer path, one unique
reservation per slot, explicit no-retry behavior and owner-scoped RPCs. A second
search requires additive SQL slot support, not reusing an existing reservation.
All provider-quality checks use mocks; no live answer-quality claim is made.

2026-10-20 verification:
- Initial service regression: 5 failed / 25 passed against the one-search path.
- Prompt transport regressions: 2 failed / 11 passed before prompt update.
- UI disclosure regression: 1 failed / 5 passed before copy update.
- New SQL tests fail before 000022 with invalid_reservation; the old RPC cannot
  admit the new slots. Fresh local bootstrap plus migrations 000001–000021 applied.
- After 000022: 50 pgTAP assertions and 7 concurrent gates PASS, including
  simultaneous initial/refined search, final generation, budget, claim and deletion.
- Full backend suite: 570 passed, one existing Starlette/httpx deprecation warning.
- Strict mypy: 50 source files pass. Ruff format: 132 files pass.
- Frontend: 89 tests pass, lint and production build pass.
- Deliberate regression: allowing a third search makes both comparison-bound
  tests fail. Source restored in finally; service suite returns to 31 passed.
- agent-toolkit check: unavailable (command not found); Graft unavailable.
- PostgreSQL 17 runtime already installed. Isolated synthetic cluster under
  /private/tmp/linksifty-chat-research-pg, loopback 55463, database
  linksifty_chat_research_test. Sandbox denies shared memory/socket access;
  escalated local-only init/start/test calls succeeded. No installation, hosted
  credentials, production data or paid integrations used.
