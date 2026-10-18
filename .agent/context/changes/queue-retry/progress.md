# Queue retry — 2026-10-18

Bounded request: add Retry alongside Paste content in the Needs action queue.

- Reuse the current resume callback, authenticated endpoint and database RPC.
  A new endpoint or duplicate submission would add complexity and risk trial use.
- Migration 000014 admits manual-content fetch failures, requeues the same job,
  clears stale failure state and explicitly resets X admission. Existing analysis
  retries preserve their cached source and research behavior.
- Retain owner/account/expiry/duplicate/budget guards. Unknown X attempts cannot
  retry; any unresolved job reservation blocks retry. No automatic provider retry.
- Existing button styling, busy disabling, accessible cost description and API
  error handling are reused. Paste remains available.
- Deploy migration before the frontend. No hosted changes or paid calls performed.
- Verification is recorded in [evidence.md](evidence.md).
