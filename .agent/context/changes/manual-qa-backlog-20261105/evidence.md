# Evidence — manual QA backlog 2026-11-05

## Commands

- Focused backend: `pytest` on account/http/content_policy/x_adapter/x_rich_sources/supabase_repository — **217 passed**
- `mypy --strict backend/src` — Success (51 files)
- `ruff check` + `ruff format --check` — pass (after formatting `test_x_adapter.py`)
- Frontend: `vitest` auth-flow/chat/queue — **48 passed**; `oxlint` + `tsc -b && vite build` — pass
- Graft: `npx @nanonets/graft check` — permission denied on local binary; used focused reads
- `agent-toolkit check` — not run (tool may be unavailable)
- Hosted SQL/pgTAP / live X / Resend — not run

## Residual risks

- Migration `20261105_000024_account_access_rerequest.sql` must apply before matching backend/frontend on hosted.
- Soft-omit of malformed Article code may drop snippets; body still assessed.
- Nested quote lookups consume X request budget (shared 12-request cap).
- Blocked accounts leave admin list until user re-requests (by design).
- QA-005 is UX hint only; no new vision/video pipeline.
