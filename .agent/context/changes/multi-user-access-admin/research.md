# Research: Multi-user access, approval and spend controls

**Date:** 2026-10-14
**Graft:** unavailable in this session; repository evidence gathered with focused `rg`, `sed` and file reads.
**Scope:** current authentication, account approval, Resend notification and per-user OpenRouter spend boundaries.

## Verified repository facts

- `frontend/index.html` sets `<title>frontend</title>`; `frontend/src/App.tsx` hard-codes `LOCAL API PREVIEW` and calls `/v1/items` without an Authorization header.
- `@supabase/supabase-js` is not a direct frontend dependency; the current package has only React/ReactDOM at runtime.
- `backend/src/linksifty/infrastructure/supabase_auth.py` calls Supabase `/auth/v1/user` and returns only a verified UUID. `backend/src/linksifty/api/auth.py` exposes that UUID to authenticated routes, with no account-status or admin checks.
- `backend/src/linksifty/infrastructure/supabase_repository.py` uses the server service-role key and explicitly filters every current item request by `user_id`.
- `supabase/migrations/20261012_000001_personal_mvp.sql` creates per-user `settings.monthly_budget_cents`, default `1000` ($10), and stores `assessments.provider_cost_cents`; it has no profile/role/approval table and no provider-usage ledger or atomic monthly reservation.
- There is no OpenRouter adapter or Resend integration in the current source or dependency manifests. Item jobs are persisted but not yet run by a worker/runner.
- `docs/superpowers/specs/2026-10-04-linksifty-setup-design.md` and `context/foundation/shape-notes.md` record the earlier multi-user rules: open signup, pending accounts, admin approve/reject, three trial links, no admin access to other users' content, and a $10 per-user monthly spend cap. The later personal-MVP PRD explicitly deferred that scope; this request supersedes it.
- User confirmed the three-link pending allowance and specified an approval email to the user via Resend. The initial admin identity is the owner's verified Google account and must be configured privately at deployment.

## External facts

- Supabase's Google OAuth web flow uses `signInWithOAuth({ provider: 'google' })`; its documented identity scopes are `openid`, `userinfo.email`, and `userinfo.profile`. Source: [Supabase Google login](https://supabase.com/docs/guides/auth/social-login/auth-google), checked 2026-10-14.
- Supabase warns that `user_metadata` is user-editable and must not be used for authorization. Its RLS guidance recommends secure roles/claims and keeping secret/service-role keys server-side. Sources: [Supabase users](https://supabase.com/docs/guides/auth/users), [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security), [Supabase API keys](https://supabase.com/docs/guides/getting-started/api-keys), checked 2026-10-14.
- OpenRouter states that request usage details are returned when `usage: { include: true }` is included; its billing is based on model/provider usage. Source: [OpenRouter support and usage](https://openrouter.ai/support), checked 2026-10-14. Exact current response fields and reservation/reconciliation behavior still require verification against the chosen completion endpoint and model before implementation.
- Resend offers an email API and a Python SDK with asynchronous support; idempotency keys can prevent duplicate sends on retry. Sources: [Resend Python](https://resend.com/python), [Resend async Python SDK](https://resend.com/changelog/python-sdk-async-support), [Resend idempotency keys](https://resend.com/changelog/idempotency-keys), checked 2026-10-14.

## Constraints and alternatives to evaluate

- Admin role must be stored in a non-user-editable authorization source and checked on the API server. Do not authorize from frontend state or `user_metadata`.
- The existing $10 budget field can remain the configured cap, but actual usage needs a durable ledger and an atomic reservation/reconciliation operation; summing completed assessment rows alone will miss future chat costs and can overspend under concurrency.
- Resend email should be an effect after an approval commit. Delivery failure must not roll back approval; the product needs a clear failure/retry result.
- The initial admin bootstrap can use a protected server-side email allowlist or a database-backed role assigned by a controlled migration/bootstrap step. Evaluate simplicity and future admin changes before choosing.
- Cost capture can consume provider-reported USD cost or derive a conservative amount from returned token counts and fixed model pricing. Prefer provider-reported cost where the selected endpoint supplies it; record uncertainty rather than silently charging zero.
- Because the current assessment pipeline is absent, choose a staged delivery boundary that does not claim accurate spend reporting until real provider calls are ledgered.

## Unknowns

- Exact trial accounting point: accepted submission versus successfully completed assessment. The frame currently assumes accepted submission.
- Email sender domain and `From` address to verify in Resend; this is an external setup requirement, not a repository secret.
- Whether rejected users remain blocked permanently or can return to pending through a later admin action.
- Provider cost precision and the chosen OpenRouter endpoint/model response contract.
- Whether the user wants an admin retry action for failed approval emails or will rely on Resend dashboard/manual resend.
