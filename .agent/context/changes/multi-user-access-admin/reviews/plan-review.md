# Plan review: multi-user access, approval and spend controls

**Date:** 2026-10-14
**Outcome:** Approve for owner review; implementation remains gated on explicit plan approval.

## Scope and spec coverage

- AR-01–AR-12 are assigned to Tasks 1–6. Google identity scopes, verified identity, server-owned status, three-link transaction, profile access checks, admin-only account operations, approval email timing/retry and safe errors are covered.
- AR-13–AR-19 are assigned to Tasks 7–11. Cost is attributed per provider call, reservations are atomic, actuals are reconciled, ambiguous results remain reserved, summaries are owner/admin scoped, and UI distinguishes actual, reserved, cap, remaining and reset.
- AR-20–AR-22 are assigned to Task 5, with title/preview cleanup and accessible responsive auth/account states.
- Stage 2 explicitly includes the absent execution path needed to produce real costs and requires it to reuse/synchronize with existing C2–C4 safe-fetch, assessment and lease tasks.

## Findings resolved before review completion

- The existing `monthly_budget_cents` representation is cents-only. The plan now specifies integer-cent admin caps and sub-cent provider costs rather than an ambiguous sub-cent cap representation.
- Existing CORS permits only GET/POST. Task 3 now includes only the required PATCH/PUT methods for account and budget changes.
- First-login bootstrap must not reset an account. Task 2 tests repeated login preserving approval and trial count.
- The owner-supplied email is absent from tracked design/context files; only the private environment variable name remains.

## Contracts, assumptions and manual work

- The plan defines the identity, service, repository, API and UI contracts consumed across tasks.
- Resend and OpenRouter use mocked HTTPX transports; no new SDK is assumed. The selected OpenRouter cost response is verified from current primary documentation immediately before adapter implementation and recorded with a date.
- Local PostgreSQL is needed for transactional race, grants and RLS tests. If unavailable, record that limitation; hosted application still requires manual owner setup for Google OAuth, sender-domain verification and migrations.
- The plan's initial Python PostgreSQL test path was adapted to the repository's Supabase SQL test convention (`supabase/tests/account_approval.test.sql`); outcome coverage is unchanged.
- Verification commands include backend unit/integration tests, strict mypy, Ruff, frontend tests/lint/build and `agent-toolkit check`; evidence is written to the change folder.
- Plan is proposed to the owner, not yet approved. No code or external service configuration is authorized by this planning review alone.
