# Progress: multi-user access, approval and spend controls

## Current phase

Product specification and implementation plan approved. Stage 1 is in progress.

## Completed

- Framed the request and reviewed existing product notes and repository integration points.
- Confirmed Graft is unavailable in this runtime; used focused repository searches and documented relevant evidence in `research.md`.
- Recorded owner decisions: three accepted pending trial links, approval email only through Resend, two delivery stages, and a $10 UTC-month OpenRouter default with per-user admin limits.
- Prepared the proposed design in `docs/superpowers/specs/2026-10-14-multi-user-access-admin-design.md`.
- Kept the owner's email out of project files; deployment will receive it privately.
- Updated canonical product roadmap and its derived Kanban for the approved two-stage scope.
- Prepared `docs/superpowers/plans/2026-10-14-multi-user-access-admin.md`, recorded accepted decisions, and completed a plan review with findings resolved.
- Owner approved the implementation plan and asked to begin stage 1.
- Initialized the Stage 1 change board.
- Implemented Tasks 1–4 locally: account profile/trial migration, verified identity and account gate, `/v1/me`, admin review/actions, durable approval notification, Resend adapter and explicit retry.
- Implemented Task 5 locally: Supabase Google sign-in, bearer-authenticated frontend API, pending/rejected/admin views, trial-aware submission limit, Vercel/Render/Supabase/Resend setup guide and environment placeholders.
- Added account-flow frontend tests, expanded pgTAP migration assertions, and created the Stage 1 architecture artifact.

## Next gate

Finish integration review and record the artifact/check evidence. Stage 2 follows the verified source-safe assessment pipeline. Hosted migrations, OAuth provider secrets, Resend sender verification and live acceptance remain owner-side setup.

## Verification evidence

- Full backend test suite: 93 passed; strict mypy and Ruff check/format pass; frontend tests 7 passed, lint and production build pass. The built frontend contains no server-only environment names.
- PostgreSQL migration/RLS tests remain unrun because Supabase CLI, psql and Docker are unavailable.
- Archify candidate validation, delivery and strict artifact checks pass; browser check is skipped because Chrome/Chromium is unavailable.
- `agent-toolkit check` remains unavailable because `agent-toolkit` is not on PATH.
- Stage 1 is implemented locally and has passed the pre-push implementation review. The owner requested pushing to `main`; hosted migrations, environment updates, OAuth/Resend setup and live acceptance remain separate activation steps documented in the setup guide.

## Supabase API key compatibility follow-up (2026-10-15)

- Added support for Supabase's current `sb_secret_...` backend key format. New secret keys are sent only as `apikey`; legacy `service_role` JWTs retain both `apikey` and Bearer headers.
- Updated Supabase deployment instructions to accept publishable/secret keys and legacy anon/service-role keys in the matching server/browser variables.
- Added a request-level regression test. It failed against the old Bearer behavior, passed after the fix, and failed again after deliberately restoring the regression.
- Backend suite passes (94 tests), strict mypy passes, and Ruff check/format pass. `agent-toolkit check` remains unavailable (`command not found`).

## Supabase 503 diagnostic follow-up (2026-10-15)

- The owner confirmed `/v1/me` still returns the generic persistence 503 after key changes. Render access logs do not show the upstream Supabase response details.
- Added privacy-safe backend logging for the profile RPC's upstream HTTP status and provider error code, plus transport/invalid-response categories. No response body, user data, or credentials are logged.
- Added a request-level test proving the diagnostic appears for a provider error while its message is not exposed. TDD red/green/deliberate-break evidence is recorded below.
- Validation passes: 94 backend tests, strict mypy, Ruff check and format. `agent-toolkit check` remains unavailable.
