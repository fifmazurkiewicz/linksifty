# Implementation review: multi-user access and account approval

**Date:** 2026-10-14
**Outcome:** Approve for the owner-requested push to `main`; hosted activation remains gated on setup and database validation.

## Plan coverage

- Tasks 1–5 are implemented locally: account profiles and trial enforcement, verified Supabase identity, account/admin APIs, durable approval notifications through Resend, and the authenticated frontend/setup guide.
- Task 6 is partially complete. The architecture artifact and local code verification are recorded; the plan's end-to-end cross-layer test, PostgreSQL execution, committed-source artifact citation and browser review remain open. Stage 2 usage metering was explicitly deferred by the approved two-stage plan.
- No source changes outside this approved Stage 1 scope appear in the working tree. The branch is `main`; `HEAD` and freshly fetched `origin/main` both resolve to `7b11e9fdc759b7f68ce5ff362f4a8953f7ddb1df` before this change is committed.

## Evidence

- Backend tests: 93 passed (one upstream Starlette/httpx deprecation warning).
- Strict mypy: 23 source files passed. Ruff check and format check passed (64 files).
- Frontend tests: 7 passed; lint and production build passed.
- `git diff --check` passed. Secret-pattern review found only environment configuration declarations and test fixtures; `.env.example` contains empty placeholders.
- `supabase/tests/account_approval.test.sql` has 13 assertions but could not run because Supabase CLI, `psql` and Docker are unavailable. `agent-toolkit check` is unavailable in this runtime. Graft is unavailable; focused repository inspection was used.

## Security, privacy and conventions

- Admin authority comes from the verified server-side email setting; browser metadata cannot grant it. Supabase service credentials and Resend/OpenRouter credentials remain server-side, while Vite receives only public Supabase configuration.
- Database helpers restrict direct client grants, pending trial submissions lock the account profile row, and user content APIs remain owner-scoped. Admin endpoints expose account metadata only.
- Resend and other remote behavior are mocked in tests; no paid provider calls or emails were made.
- The approved stack, package layout, migrations, strict typing, accessibility-oriented UI behavior and setup documentation conventions are followed.

## Operational limitation

Pushing `main` can trigger Vercel/Render deployments before the hosted Supabase migrations and environment variables are configured. The setup guide records those required steps. This review authorizes the requested source push and does not claim that hosted account approval or live SQL behavior has been validated.
