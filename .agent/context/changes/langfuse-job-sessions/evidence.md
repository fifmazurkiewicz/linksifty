# Verification

- Added real-SDK in-memory export assertions for session attributes on roots,
  generations and events. Separate attempts share a session only for the same
  job; a nested fetch inherits it; unrelated reconciliation has no session.
- Red: export assertions failed before propagation was implemented. Corrected
  the asserted wire attribute to the installed SDK's `session.id`, then green.
- Deliberate break: disabled propagation; export regression failed. Restored it.
- Added a setup-failure test: processing continues and opened context is closed.
- Strict mypy: 33 source files passed. Ruff lint/format: passed.
- Full backend unit suite: 147 passed, one existing Starlette/httpx deprecation
  warning. Toolkit check: clean. `git diff --check`: clean.
- All integrations mocked/local; no hosted or paid request was made.
