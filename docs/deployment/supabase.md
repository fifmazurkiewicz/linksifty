# Supabase setup

Follow the [complete setup guide](setup.md) for account creation, compatible API
keys, Auth settings, migrations, Render/Vercel environment variables and staging
checks. This page is the short Supabase reference.

The server repository adapter accepts either a legacy `service_role` JWT or a
new `sb_secret_...` key. Legacy keys are sent in `apikey` and `Authorization:
Bearer`; new secret keys are sent only in `apikey`, as required by Supabase.
The browser key may be a publishable `sb_publishable_...` key or legacy `anon`
JWT. See the complete guide for official sources.

Apply the files in `supabase/migrations/` in filename order. The second migration restricts RPC execution to the server service role and adds transactional submission of items and jobs. No migration has been executed on a hosted project by this agent.

Set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` on the backend. The backend validates each bearer token with `/auth/v1/user` before using its verified UUID for repository queries. Service-role credentials remain server-only.

The Vite app also needs the public `VITE_SUPABASE_URL` and
`VITE_SUPABASE_ANON_KEY` on Vercel. Enable Google under **Authentication → Sign
In / Providers**, configure the Google OAuth web client with Supabase's displayed
callback URL, and set the Supabase Site URL and redirect allowlist to the exact
production frontend origin (`https://linksifty.fmazurkiewicz.dev/`) and local
development origin (`http://localhost:5173/`). Never expose the service-role
key in Vercel or any `VITE_` variable.

Keep `LINKSIFTY_DEMO_MODE=false` on Render. Set `FRONTEND_ORIGIN` to the exact Vercel frontend origin. Missing or invalid authentication returns 401; unavailable auth or persistence returns 503.

Local demo mode uses sample records and does not persist submissions. Real submission calls `submit_fetch_items` to create each item and queued job in one transaction. The matching API now executes queued jobs opportunistically and exposes owner-scoped progress SSE after migration 000005; hosted activation is not yet verified.

Before release, verify RLS and foreign-key ownership on a real or local PostgreSQL instance with two user identities. HTTP mock tests prove that the API supplies ownership filters, but do not prove database policy enforcement.


Processing/usage requires `20261015_000005_processing_usage.sql`. It adds exact USD
reservations/totals, server-controlled budgets, threshold writes, fenced jobs and
heartbeats. After validating it in a disposable database, explicitly enable
`supabase/retention.sql` for cleanup while the app is inactive. Settled cost detail
expires after 30 days; current-month totals and unresolved reservations remain.
See setup section 13 for the pgTAP/concurrency gate and unknown-cost reconciliation.

### Source-saving compatibility fix (000006)

After 000005, apply `20261015_000006_source_hash.sql`. Supabase may keep pgcrypto
in `extensions`, outside the processing RPCs' fixed `public` search path. The
follow-up uses PostgreSQL's native SHA256 for fetched/pasted content, preserving
permissions and lease/owner checks. Affected jobs can remain at checking content
with a generic processing_interrupted warning. Refresh the queue after migration;
expired pre-inference jobs are recovered automatically. Do not submit duplicates
or clear unresolved cost reservations. No backend redeploy is needed for this SQL fix.

Brave source checking additionally requires `20261015_000007_brave_research.sql` after 000006: research consent/context, provider-scoped reservations, source identity and table-side citation validation. Apply before enabling the Brave key/rate. It notifies PostgREST to reload schema.
