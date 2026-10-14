# Supabase setup

Follow the [complete setup guide](setup.md) for account creation, compatible API
keys, Auth settings, migrations, Render/Vercel environment variables and staging
checks. This page is the short Supabase reference.

The current server repository adapter requires the legacy `service_role` JWT
because it sends that key in an Authorization Bearer header. Do not substitute
an `sb_secret_...` key without adapting those headers. Supabase recommends the
new publishable/secret keys and is deprecating legacy keys; key migration remains
necessary before long-term activation. See the complete guide for official sources.

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

Local demo mode uses sample records and does not persist submissions. Real submission calls `submit_fetch_items` to create each item and queued job in one transaction. Processing jobs is still being implemented, so currently real submissions remain queued.

Before release, verify RLS and foreign-key ownership on a real or local PostgreSQL instance with two user identities. HTTP mock tests prove that the API supplies ownership filters, but do not prove database policy enforcement.
