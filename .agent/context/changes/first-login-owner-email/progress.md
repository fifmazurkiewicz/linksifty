# First-login owner notification

User request: notify fifmazurkiewicz@gmail.com once when a new user first signs in; approval grants full access and does not send mail. Preserve three-source trial and monthly spend limits.

- [x] Trace existing profile, notification, Resend and admin flows.
- [x] Prepare focused regression tests and observe red against old implementation (8 failed, 1 passed).
- [x] Implement durable one-event enqueue and dispatch to owner.
- [x] Verify backend, UI, local SQL and quality gates.
- [x] Independent implementation review.

Design: add account_requested event on first pending profile insertion; unique partial index per user; /v1/me dispatches only pending events using existing atomic claim and provider idempotency. No mail on approval or repeat login, no backfill of existing profiles, no automatic retry of failed/uncertain events. Legacy RPC response fields and retry URL remain compatible; UI labels describe new-account mail. RESEND_ADMIN_EMAIL is separate from admin authorization and defaults to the requested owner address. External deployment/migration/email dispatch not performed.

Risks: duplicate/spam notification (high/medium), wrong recipient or unescaped email in HTML (high/medium), notification outage blocking login (high/medium), approval/trial regression (high/medium). Ratings are conservative, based on user requirements and existing notification/auth integration, and do not reduce coverage.

Completed locally. Full backend 611 passed; frontend 112 passed; UTF-8 PostgreSQL migrations, 19 SQL suites and concurrency gate passed. Mypy, Ruff, format, lint, build, toolkit and diff checks passed. Independent review approved. Production rollout not performed. Temporary local database stopped.
