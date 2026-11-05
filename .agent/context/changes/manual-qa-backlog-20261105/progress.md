# Manual QA backlog execution — 2026-11-05

Owner: execute all open QA-001…QA-008; deliver one MR for review.

## Locked product decisions

- **QA-001/002:** Keep DB statuses `pending|approved|rejected`. Admin UI: pending → Approve/Reject; approved → Block (sets `rejected`); hide `rejected` from default admin list; users get “Request access again” → `pending` + new Resend notification. Trial preserved.
- **QA-003:** Stronger login-wall phrases; bare “Sign in” alone does not fail long pages.
- **QA-004:** Valid Article body + malformed `entities.code` → omit bad snippets (fail-soft).
- **QA-007:** Bounded follow-up `_lookup` for missing `quoted`/`retweeted` (including top-level repost originals).
- **QA-005:** After 2+ Retries, UX hint about vision when fetch succeeds; no new video pipeline.
- **QA-006:** Document acquisition failures are not Sentry issues.
- **QA-008:** Clearer `classification_uncertain` copy; classifier note for short “is it like X?” comparisons.

## Packages

- [x] accounts (001/002)
- [x] fetch (003/004/007)
- [x] chat-ops (005/006/008)
- [x] verify (focused tests/mypy/ruff/frontend lint+build) — see evidence.md
