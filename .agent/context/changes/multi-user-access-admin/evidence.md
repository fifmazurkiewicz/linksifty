# Verification evidence: multi-user access, approval and spend controls

## Stage 1 implementation

- Backend account/auth/admin/notification implementation and owner-scoped item API: `UV_CACHE_DIR=/tmp/linksifty-uv-cache uv run --package linksifty pytest backend/tests -q` → **93 passed**, one upstream Starlette/httpx deprecation warning.
- Backend static/type checks: `UV_CACHE_DIR=/tmp/linksifty-uv-cache uv run --package linksifty mypy --strict backend/src` → **passed, 23 source files**; `UV_CACHE_DIR=/tmp/linksifty-uv-cache uv run --package linksifty ruff check .` → **passed**; `UV_CACHE_DIR=/tmp/linksifty-uv-cache uv run --package linksifty ruff format --check .` → **passed, 64 files formatted**.
- Frontend behavior: `npm --prefix frontend test -- --run` → **7 passed**. Covers Google OAuth scopes, keyboard activation, pending remaining-trial cap, rejected account, 401 sign-out, admin approval and approval-email retry with mocked APIs/Supabase. The admin mutation test asserts a bearer token is attached.
- Frontend quality: `npm --prefix frontend run lint` → **passed**; `npm --prefix frontend run build` → **passed**. Production bundle uses only the Supabase browser client; server-role, Resend and provider secrets are not referenced by Vite.
- TDD red/green: frontend tests first failed against the prior no-auth UI. Deliberately removed the Google `profile` scope; the OAuth behavior test failed on the exact scope assertion. Restored the scope and reran the suite successfully.
- Resend behavior uses HTTPX mock transports only. No message was sent and no paid provider request was made.
- `supabase/tests/account_approval.test.sql` contains 13 pgTAP assertions for pending profiles, trial limit and all-or-nothing batches, repeat-login retention, rejection, approved access, and durable non-duplicate approval notifications. It was **not executed**: `supabase`, `psql`, and `docker` are unavailable in PATH. Parallel SQL race and live grants/RLS still need a Postgres/Supabase run.
- Archify `architecture.json` and `architecture.html`: schema validation, artifact delivery and strict artifact checks passed. Browser check was skipped because Chrome/Chromium is unavailable; no visual review is claimed. Archify's update lookup returned `cache-unavailable` and required no action.

## Remaining validation and activation

- `agent-toolkit check` was attempted and returned `command not found`; the toolkit is unavailable in this runtime.
- No hosted Supabase migration, Google OAuth, Resend sender, Vercel, or Render settings were changed. The setup guide documents the owner steps. Set the private admin email only in Render as `LINKSIFTY_ADMIN_EMAIL`.
- Stage 2 USD usage ledger and OpenRouter enforcement remain unimplemented, as approved: they follow Stage 1 and the source-safe assessment runner.
- The domain remains the configured production frontend origin in the docs; deployment of this local work has not been performed.

## Supabase API key compatibility follow-up (2026-10-15)

- TDD red: `UV_CACHE_DIR=/tmp/linksifty-uv-cache uv run --package linksifty pytest backend/tests/unit/test_supabase_repository.py::test_new_secret_key_is_not_sent_as_a_bearer_token -q` failed because the repository sent `Authorization: Bearer sb_secret_test`.
- Green: the focused repository test passed after the adapter omitted Authorization for the new `sb_secret_` key prefix. Legacy JWT header behavior remains covered by `test_profile_bootstrap_uses_verified_identity_and_server_admin_decision`.
- Deliberate break: temporarily restored unconditional Bearer authorization; the new regression test failed on the missing-header assertion, then the correct implementation was restored.
- Final backend validation: `UV_CACHE_DIR=/tmp/linksifty-uv-cache uv run --package linksifty pytest backend/tests -q` → **94 passed** (one existing Starlette/httpx deprecation warning); strict mypy passed for 23 source files; Ruff check passed; Ruff format check passed for 64 files.
- `agent-toolkit check` was attempted and is unavailable (`command not found`). No production keys were read or used; mocked tests use only the placeholder `sb_secret_test`.

## Supabase 503 diagnostic follow-up (2026-10-15)

- TDD red: the new profile-RPC diagnostic test failed before logging was added because the response status and error code were absent from captured logs.
- Green: `test_profile_rpc_logs_safe_provider_diagnostics_for_secret_key` passes with an HTTP mock returning 403/code `42501`; it also verifies the provider message is not logged.
- Deliberate break: removed the provider-failure warning and reran the focused test; it failed because the expected status was missing. Restored the warning and reran the full suite.
- Final verification: backend suite **94 passed** (one existing Starlette/httpx deprecation warning); strict mypy, Ruff check, Ruff format check, and `git diff --check` passed. `agent-toolkit check` is unavailable (`command not found`).
- Diagnostic fields are limited to operation, HTTP status, Supabase error code, error class, and invalid-response category. No credentials, response message/body, email, or profile data are logged.
