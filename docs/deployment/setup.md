# Linksifty setup: Supabase, Render, Vercel, OpenRouter and X

Checked against repository code and official documentation on **2026-10-14**. Google OAuth is the requested login method.
Follow the steps in order. Example names and URLs below must be replaced with
your own. Keep actual keys in your password manager and platform environment
settings; do not put them in Git or this document.

## 1. Decide what you are setting up now

The processing/usage/inbox slice is implemented locally; database and hosted
activation remain separate release gates. Keep demo mode off on the real-data
service. Mock tests and local UI checks do not certify RLS or provider behavior.

| Component | Local implementation | Release gate |
| --- | --- | --- |
| Supabase | Owner-scoped records, fenced processing, exact USD reservations, settings/admin budget RPCs | Apply migration 000005, run SQL/RLS/concurrency gate, enable retention schedule |
| Render API | Authentication, resumable bounded runner, OpenRouter, progress SSE and recovery routes | Hosted restart/streaming and verified provider cost |
| Vercel frontend | Google session, queue, live progress, detail/citations, paste, settings and admin limits | Rebuild with matching API, hosted two-account check |
| OpenRouter | Actual-cost adapter and strict source-citation validation | Server key and verified model; explicitly approved paid acceptance |
| X/chat | Deferred; unsupported X content requests manual paste | Separate roadmap scope |

Setup order: **Supabase → Render → Vercel → final CORS/Auth URLs → optional
provider credentials → staging checks → release verification after coding**.

## 2. Prepare the repository and accounts

1. Have accounts on [GitHub](https://github.com/), [Supabase](https://supabase.com/dashboard),
   [Render](https://dashboard.render.com/), and [Vercel](https://vercel.com/).
2. Use the same GitHub repository for Render and Vercel. The deployable revision
   must contain `backend/`, `frontend/`, root `pyproject.toml`, `uv.lock`, and
   `supabase/migrations/`. Local uncommitted files are not available to hosting.
3. Keep the repository private if preferred; authorize each host to access only
   the repository it needs.
4. Keep lockfiles in Git. Keep `.env` and frontend `.env.local` out of Git.
5. Use staging data until the remaining ownership/RLS and API tests are complete.
   A successful `/health` check only proves the process is running.

## 3. Create and configure Supabase

### 3.1 Create the project

1. Open the Supabase dashboard and create a project in your organization.
2. Name it, for example, `linksifty-staging`.
3. Choose an available EU region near the intended Render region.
4. Generate a strong database password and save it in your password manager.
   The current app uses the HTTP API, so this password is **not** an app env variable.
5. Wait for the project to finish provisioning.
6. Open the project's **Connect** dialog and copy its HTTPS project URL, such as
   `https://<project-ref>.supabase.co`. This is `SUPABASE_URL`, not a dashboard URL
   or PostgreSQL connection string.

### 3.2 Collect compatible API keys

Open **Settings → API Keys** and use either the recommended new keys or legacy
keys:

- **Publishable** (`sb_publishable_...`) or legacy **anon** JWT →
  `SUPABASE_ANON_KEY` on Render and `VITE_SUPABASE_ANON_KEY` on Vercel.
- **Secret** (`sb_secret_...`) or legacy **service_role** JWT →
  `SUPABASE_SERVICE_ROLE_KEY` on Render, server-only.

The backend sends new secret keys only in `apikey`; legacy service-role JWTs are
sent in both `apikey` and `Authorization: Bearer`. Never put a secret/service-role
key in Vercel or any `VITE_` variable. Supabase's [API key guide](https://supabase.com/docs/guides/getting-started/api-keys)
explains the key formats and migration timeline.

### 3.3 Apply the development schema

On a **fresh staging project**, open **SQL Editor → New query**. Paste the entire
contents of each migration and run them in this order:

1. [`20261012_000001_personal_mvp.sql`](../../supabase/migrations/20261012_000001_personal_mvp.sql)
2. [`20261013_000002_submission_rpc.sql`](../../supabase/migrations/20261013_000002_submission_rpc.sql)
3. [`20261014_000003_account_approval.sql`](../../supabase/migrations/20261014_000003_account_approval.sql)
4. [`20261014_000004_account_notifications.sql`](../../supabase/migrations/20261014_000004_account_notifications.sql)
5. [`20261015_000005_processing_usage.sql`](../../supabase/migrations/20261015_000005_processing_usage.sql)

These scripts are not all rerunnable. If a migration has already succeeded,
do not run it again or delete existing tables to silence an error. Check the
project's migration history/SQL query history first. Future migrations must be
applied afterward in filename order; never edit an already-applied migration.

Check Table Editor for `settings`, `items`, `source_contents`, `jobs`,
`assessments`, `citations`, `chat_messages`, `account_profiles`, and
`account_notifications`, `usage_months`, and `usage_reservations`. Check Database Functions for `claim_next_job`,
`submit_fetch_items`, and the account profile/status/notification RPCs. The
migrations enable RLS, but this alone does not prove complete ownership isolation.
Run the account-approval pgTAP tests and two-user SQL checks before release.
[Supabase tables/SQL Editor](https://supabase.com/docs/guides/database/tables).

### 3.4 Configure Google/Gmail sign-in

Google OAuth authenticates your Google account; it does not require reading Gmail.
The frontend uses it for identity only; no Gmail mailbox access is requested.

1. Open [Google Cloud Console](https://console.cloud.google.com/), create/select a
   Linksifty project, then open **Google Auth Platform**.
2. Configure **Branding** (app name/support email). Choose **External** audience
   for a personal Gmail account. While in Testing, add your Gmail under Test users.
3. Use identity scopes only: `openid`, `userinfo.email`, `userinfo.profile`.
   Do not enable Gmail API or request mailbox scopes for login.
4. **Clients → Create client → Web application**. Add JavaScript origins:
   `https://linksifty.fmazurkiewicz.dev` and, for development,
   `http://localhost:5173`.
   [Google OAuth client setup](https://developers.google.com/identity/protocols/oauth2/web-server#creatingcred).
5. In Supabase **Authentication → Sign In / Providers → Google**, copy the
   displayed callback URL. Add it to Google's **Authorized redirect URIs**:

   ```text
   https://<project-ref>.supabase.co/auth/v1/callback
   ```

6. Save Google's Client ID and Client Secret in the **Supabase Google provider**
   settings and enable the provider. Keep the secret there; do not put it in
   frontend env, Render or Git. [Supabase Google provider](https://supabase.com/docs/guides/auth/social-login/auth-google).
7. Supabase **URL Configuration**: set Site URL to
   `https://linksifty.fmazurkiewicz.dev`; allow that exact root URL and
   `http://localhost:5173/`. Google's redirect goes to Supabase; Supabase then
   returns to the app root, where the client restores its session.
   [Redirect configuration](https://supabase.com/docs/guides/auth/redirect-urls).
8. Leave Google signups enabled so new people can authenticate; the application
   creates their profile as `pending` and restricts use to three trial links until
   an admin approves them. Set the verified owner's email privately on Render as
   `LINKSIFTY_ADMIN_EMAIL`. The API grants admin role only from that server value.

## 4. Configure the API on Render

### 4.1 Create or fix the Docker web service

The requested Docker path is now defined by the root `Dockerfile`. Render builds
the backend image; Vercel still builds the frontend separately.

1. For your existing failed Docker service, open **Settings** and keep Docker.
   For a new service: **New → Web Service → Git Provider → linksifty**.
2. Branch: `main`. Runtime/Language: **Docker**.
3. **Root Directory: leave blank**. Docker build context must be the repository
   root, which contains `uv.lock` and both workspace manifests.
4. **Dockerfile Path: `./Dockerfile`**; **Docker Build Context Directory: `.`**
   (or leave at the repository-root default).
5. Leave **Docker Command** unset, so the image's CMD starts the API. Native-Python
   Build/Start command fields do not apply to this path.
6. Health Check Path: `/health`.
7. Keep the server-only environment variables from section 4.2 on the service.
8. After the Docker commit is on GitHub, use **Manual Deploy → Deploy latest commit**
   for the existing service, or **Create Web Service** for a new one.
9. Inspect the build logs, then check `/health`. The image runs as UID 10001 and
   honors Render's runtime `PORT` without baking keys into the image.

[Docker on Render](https://render.com/docs/docker). Python 3.11.16 and uv 0.12.17
are controlled by Dockerfile image tags. Production dependencies come from
`uv.lock`; no development tools are installed in the image. The `.dockerignore`
allows only the backend source/build metadata and excludes env files, frontend,
Git history, local sessions and virtual environments.

**Local Docker, when installed:**

```sh
docker build -t linksifty-api .
docker run --rm -p 8000:8000 --env-file .env linksifty-api
```

Use an existing private `.env` (section 9), not build arguments. Open
`http://127.0.0.1:8000/health`. To verify a different port:

```sh
docker run --rm -p 8123:8123 -e PORT=8123 linksifty-api
```

GitHub CI builds the actual image and checks health, anonymous 401, a non-default
port and the non-root user without any Supabase/provider credentials.

**Optional native-Python fallback:** set runtime Python, keep Root Directory
blank, use Build Command `uv sync --locked --package linksifty --no-dev` and
Start Command `uv run --locked --no-sync --package linksifty uvicorn linksifty.main:app --host 0.0.0.0 --port "$PORT"`.
Only this fallback needs platform `UV_VERSION`/`PYTHON_VERSION` settings.

### 4.2 Add Render environment variables

In the service's **Environment** settings, enter raw values without surrounding
quotes. Keep secret values in the host's secret/environment storage.

| Variable | Value/source | Needed now? |
| --- | --- | --- |
| `SUPABASE_URL` | Your Supabase project HTTPS URL | Yes for authenticated persistence |
| `SUPABASE_ANON_KEY` | Supabase publishable key or legacy anon JWT | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase secret key or legacy service_role JWT | Yes; server-only |
| `LINKSIFTY_DEMO_MODE` | `false` | Yes; real environment |
| `FRONTEND_ORIGIN` | `https://linksifty.fmazurkiewicz.dev` with no trailing slash | Set after step 5, then restart/redeploy |
| `LINKSIFTY_ADMIN_EMAIL` | Verified Google account email for the initial administrator | Yes for owner admin access; private server setting |
| `RESEND_API_KEY` | Resend API key with permission to send from the verified sender domain | Yes for approval email; server-only |
| `RESEND_FROM_EMAIL` | Sender identity on a domain verified in Resend, e.g. `Linksifty <noreply@example.com>` | Yes for approval email |
| `OPENROUTER_API_KEY` | Server-only OpenRouter inference key | Required for assessment; missing key yields an explicit not-configured state |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | This verified model is supported; other IDs fail closed before inference |
| `X_API_BEARER_TOKEN` | Official X app-only bearer token | Optional preparation; X adapter is unfinished |
| `PORT` | Supplied by Render | Do not manually set |

On Docker, changing Render `UV_VERSION` or `PYTHON_VERSION` does not change the
image; edit the pinned Dockerfile tags instead. Those platform settings are
only for the native-Python fallback. [Render version settings](https://render.com/docs/python-version).

### 4.3 Deploy and check health

Deploy the service and inspect build/start logs. Its base URL is:
`https://linksifty.onrender.com`.

Open that URL with `/health` appended. Expected response:

```json
{"status":"ok"}
```

`/docs` should display FastAPI's API documentation. `/v1/items` without a user
Bearer token should return **401**. Supabase API keys are not user access tokens.

Free Render web services currently sleep after 15 minutes without inbound
traffic and may take about a minute to wake. An initial slow response is not
proof of a bad key. Persist data in Supabase; process memory/local disk is not
your database. [Free-service behavior](https://render.com/docs/free).

## 5. Configure the frontend on Vercel

1. Vercel → **Add New → Project** → import the same GitHub repository.
2. Framework Preset: **Vite**.
3. **Root Directory: `frontend`**.
4. Install Command: `npm ci`.
5. Build Command: `npm run build`.
6. Output Directory: `dist` (relative to `frontend`, not `frontend/dist` here).
7. Node.js Version: **22.x**, matching local/CI's major version.
8. Add these environment variables to **Production**:

   ```dotenv
   VITE_API_BASE_URL=https://linksifty.onrender.com
   VITE_SUPABASE_URL=https://<project-ref>.supabase.co
   VITE_SUPABASE_ANON_KEY=<supabase-publishable-or-anon-key>
   ```

   Use the API base origin, without `/v1`, `/health`, or a trailing slash. Get
   the Supabase URL and browser-safe publishable/anon key from the project's
   API settings. These three `VITE_` values are public and are compiled into the
   browser bundle; never put a service-role key here.
9. Deploy. Production uses `https://linksifty.fmazurkiewicz.dev`; the Vercel
   project URL is `https://linksifty.vercel.app`.
10. If Preview builds are needed, configure the variable separately for Preview.
    Use a staging API/data set; the current API accepts only one frontend origin.

Vercel hosts the static frontend; the Python API stays on Render.
[Vite deployment](https://vercel.com/docs/frameworks/frontend/vite).

Vite's `VITE_` values are included in the browser bundle. Do not add service-role,
OpenRouter or X keys to Vercel for this static frontend, and never give them a
`VITE_` prefix. Changing `VITE_API_BASE_URL` requires a new deployment/build.
[Vite env behavior](https://vite.dev/guide/env-and-mode.html),
[Vercel environment scopes/redeployment](https://vercel.com/docs/environment-variables).

The frontend starts Google OAuth through Supabase and returns to the exact Vercel
origin. Supabase restores the session in the browser; private API calls include
its short-lived bearer token. There is no separate `/auth/callback` route.

## 5.1 Enable Google sign-in in Supabase

1. In Supabase, open **Authentication → Sign In / Providers → Google** and enable
   Google. Copy the Supabase callback URL displayed in that provider settings.
2. In Google Cloud Console, configure an OAuth client of type **Web application**.
   Add the Supabase callback URL to **Authorized redirect URIs**. Add your
   production site to **Authorized JavaScript origins** if Google requests it.
   Copy the Google client ID and client secret into the Supabase Google provider
   fields and save. Keep the client secret in Supabase only.
3. In Supabase **Authentication → URL Configuration**, set **Site URL** to
   `https://linksifty.fmazurkiewicz.dev` and add these redirect allowlist
   entries: `https://linksifty.fmazurkiewicz.dev/` and
   `http://localhost:5173/` for local development. Use the custom domain as the
   production entry point so the API's exact CORS origin matches.
4. In **Authentication → Users**, confirm the owner's Google account uses the
   address configured privately as `LINKSIFTY_ADMIN_EMAIL`. Supabase must report
   the email as verified. Do not place that address in frontend settings.
5. Save Vercel's three `VITE_` values and redeploy. Sign in from the production
   domain and confirm `/v1/me` reports the admin role before inviting other users.

## 5.2 Configure approval email in Resend

1. Verify a sending domain in Resend and publish the DNS records Resend provides.
2. Create an API key with sending access and set `RESEND_API_KEY` on Render.
3. Set `RESEND_FROM_EMAIL` to a sender on that verified domain. The app sends
   email only after an administrator approves an account; a failed delivery does
   not undo approval and can be retried from the admin panel.
4. Set `LINKSIFTY_ADMIN_EMAIL` to the verified owner Google email and set
   `FRONTEND_ORIGIN` to `https://linksifty.fmazurkiewicz.dev`. Save and redeploy
   Render after changing server variables.

The root `.env.example` lists variable names only. The frontend Supabase values
are browser-visible; Supabase service-role and Resend keys remain on Render.

## 6. Connect the final origins and Auth URLs

1. On Render set `FRONTEND_ORIGIN` to the exact production frontend origin:
   `https://linksifty.fmazurkiewicz.dev`.
2. Save and restart/redeploy Render so the API reads the new setting.
3. In Supabase **Authentication → URL Configuration**, set **Site URL** to
   `https://linksifty.fmazurkiewicz.dev`.
4. Keep the exact Supabase redirect destinations documented in step 5.1. Do not
   broadly allow every Vercel preview domain.
5. When adding a custom domain later, update all three together: Vercel domain,
   Render `FRONTEND_ORIGIN`, and Supabase Site URL/redirect destinations.

Supabase Auth URL configuration controls redirects. Render CORS controls browser
API access; changing one does not configure the other.
[Site URL and redirect allowlist](https://supabase.com/docs/guides/auth/redirect-urls).

After these settings and the migrations are in place, Google sign-in creates an
authenticated browser session and the frontend sends its user token to the API.
A valid CORS response alone does not replace authentication.

## 7. Prepare OpenRouter (calls activate after C3)

1. Create an account at [OpenRouter](https://openrouter.ai/).
2. Open [API Keys](https://openrouter.ai/settings/keys), create an inference key
   named `linksifty-staging`, and save it once in your password manager.
3. Set a key-level credit limit. For this product's intended ceiling, choose
   **USD 10 with a monthly reset** if that option is available. Disable automatic
   top-ups unless you deliberately want them. Review the current billing screen
   before adding credits; funding is not needed just to prepare this guide/setup.
4. Put the inference key in Render as `OPENROUTER_API_KEY`.
5. Never use a management/provisioning key as the application inference key.
6. Set `OPENROUTER_MODEL=openai/gpt-4o-mini`. Other model IDs are blocked until their context/cost contract is verified and added to the adapter.

Key credit limits can reject further requests at the limit.
[OpenRouter authentication and key limits](https://openrouter.ai/docs/api_reference/authentication).
Schema support depends on the model/provider.
[Structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs).

The application enforces a per-user UTC calendar-month budget with exact
PostgreSQL numerics. Before inference it reserves **0.14848 USD**: the full verified
128,000-token context at the enforced 1 USD/M input ceiling plus 4,096 output tokens
at 5 USD/M. This includes framing without estimating token counts from source
bytes. Actual cost is settled from `usage.cost`; the reservation is not the bill.
The request disables fallback, plugins/tools and per-request fees (`max_price.request=0`).
Unknown model bounds fail before payment. A missing/uncertain cost remains reserved;
no implicit repeat of that paid attempt occurs. Key-level limits are a separate,
shared-provider-account control, not the app's per-user budget.

Sources checked 2026-10-15: [model context](https://openrouter.ai/openai/gpt-4o-mini),
[provider price ceilings](https://openrouter.ai/docs/guides/routing/provider-selection),
[usage cost and generation lookup](https://openrouter.ai/docs/cookbook/administration/usage-accounting).

## 8. Prepare official X access (optional until C7)

1. Open the [X Developer Console](https://console.x.com/), sign in, and complete
   developer onboarding/use-case details.
2. Create an application and obtain an **app-only Bearer Token** for public-data
   reads. Save it in your password manager.
3. Review access to the required post/thread read endpoints and current billing
   in the console. Do not purchase access merely to finish unrelated coding.
4. Store that token only on Render as `X_API_BEARER_TOKEN`.
5. This app does not currently require user OAuth posting permissions, access-token
   secrets, or an OAuth callback for reading public posts.

[Official X access/credential guide](https://docs.x.com/x-api/getting-started/getting-access).

The X adapter is unfinished. Having a token does not activate X ingestion;
C7.1 will implement official reads and explicit manual-content fallback for
inaccessible posts/access limits. If you are deferring X, leave this variable unset.

## 9. Local development environment

### Backend

From the repository root, copy `.env.example` to an untracked `.env` **only if
`.env` does not already exist**. Edit it locally with your staging values:

```dotenv
LINKSIFTY_ADMIN_EMAIL=<verified-owner-google-email>
RESEND_API_KEY=<resend-key>
RESEND_FROM_EMAIL=<verified-sender>
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<sb_publishable-key-or-legacy-anon-JWT>
SUPABASE_SERVICE_ROLE_KEY=<sb_secret-key-or-legacy-service-role-JWT>
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
X_API_BEARER_TOKEN=
LINKSIFTY_DEMO_MODE=false
FRONTEND_ORIGIN=http://localhost:5173
```

The API uses `os.getenv`; it does not automatically read `.env`. Load your own
trusted dotenv file through uv and run the API:

```sh
uv run --env-file .env --package linksifty uvicorn linksifty.main:app --reload
```

For an isolated UI demo instead, set `LINKSIFTY_DEMO_MODE=true` locally; it uses
sample records and does not prove authenticated persistence or real assessment.

### Frontend

Create untracked `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<sb_publishable-key-or-legacy-anon-JWT>
```

Inside `frontend/`:

```sh
npm ci
npm run dev
```

Open the exact origin configured by `FRONTEND_ORIGIN` (normally
`http://localhost:5173`). Restart Vite after changing local env values.

### Variables you do not need to invent

The current code does not read `DATABASE_URL`, `SUPABASE_JWT_SECRET`,
`SUPABASE_DB_PASSWORD`, `OPENROUTER_BASE_URL`, `X_API_KEY`,
or `X_API_SECRET`. The Vite variables above are consumed by the frontend;
Render's `PORT`, `PYTHON_VERSION` and `UV_VERSION` are hosting settings, not
fields in `Settings`.

## 10. Verify Stage 1 in staging

1. Check Render `/health` returns `{"status":"ok"}`.
2. Check unauthenticated `/v1/items` returns 401, with demo mode false.
3. Open `https://linksifty.fmazurkiewicz.dev` and sign in with Google. Confirm
   `/v1/me` returns `role: admin` for the verified owner account.
4. Sign in with a second verified Google account. It should show `pending` and
   three trial links remaining. Submit three staging URLs, then confirm another
   submission is rejected without creating partial rows.
5. From the admin account, approve the second user. Confirm the account becomes
   approved and the Resend approval message arrives. If delivery fails, retry from
   the admin panel and verify approval remains active.
6. In the second account, confirm `/v1/items` shows only its own records. In the
   admin account, verify the admin panel lists account metadata only.
7. In Supabase Table Editor confirm submitted items and jobs have the second
   user's UUID. Run the repository's Supabase SQL tests before release.

The local API now runs queued work after submission or an authenticated visit. Successful sign-in alone does not prove the processing/database/provider gates; use the Stage 2 checks below.

8. Before release, use executable SQL/RLS tests to verify cross-owner reads/writes
   and child ownership. Do not infer RLS safety from a successful service-role API
   request; service_role bypasses RLS.

## 11. Troubleshooting

| Symptom | Check |
| --- | --- |
| Render build cannot find workspace/lockfile | Root Directory must be blank, repository contains root `uv.lock` and `backend/` |
| Dockerfile missing | Runtime Docker; root/context repository root; Dockerfile Path `./Dockerfile`; deploy revision containing the file |
| `uv` missing or wrong version | Docker uses the version copied in Dockerfile; native Python uses `UV_VERSION` |
| Render fails to bind a port | Keep Docker Command empty; image CMD binds `0.0.0.0` and runtime `PORT` |
| Browser requests localhost after deployment | Set `VITE_API_BASE_URL` in the correct Vercel environment and redeploy |
| Browser CORS error | Render `FRONTEND_ORIGIN` exactly matches browser origin; no trailing slash; restart API |
| Vercel preview URL fails but stable URL works | Current backend allows one configured origin; previews need a separate staging arrangement |
| API 401 | Missing/expired user access token; sign in again and check Supabase Auth settings |
| API 503 for auth | Supabase URL/key configured; project awake/reachable; token verification available |
| API 503 for persistence | Compatible server key; all five migrations applied; DB/API reachable |
| Submitted item never leaves queued | Matching backend build and migration 000005; API awake; verify worker heartbeat and error stage |
| First Render request is slow | Free-service cold start; wait for service health before diagnosing credentials |
| No OpenRouter/X calls | OpenRouter needs a server key, supported model and available budget; X adapter remains deferred |

## 12. Release checklist after the remaining coding phases

- [ ] Latest deployable code is committed/pushed and GitHub CI succeeds.
- [ ] All required local quality gates pass, including `agent-toolkit check`.
- [ ] C1 database constraints, server-only privileges and two-user SQL/RLS tests pass.
- [ ] Supabase key migration is compatible with current provider key requirements.
- [ ] C2 acquisition safeguards and manual fallback work end to end.
- [ ] C3 provider schema/citations and atomic monthly cap work; no ambiguous retry spends twice.
- [ ] C4 durable runner/restart/retry/lease fencing work on the chosen hosting plan.
- [ ] Stage 1 Google login, approval, trial cap and Resend pass the hosted staging flow above.
- [ ] Remaining C5/C6 Inbox/detail, paste recovery, deletion and settings work.
- [ ] C7 chat/X work, or any scope change is explicitly accepted and recorded.
- [ ] 30-day cleanup actually executes and cascade-deletes; an expiry field alone is insufficient.
- [ ] Logs omit tokens, provider credentials and source bodies.
- [ ] Correct CORS/Auth URLs, cold-start smoke checks and the 20-link evaluation pass.

This document prepares manual E1 setup. It does not mark E1 or C8.3 complete:
no account, migration, deployment or paid call was executed when writing it.


## 13. Processing, usage, retention and recovery

Apply migration **000005 before deploying the matching API/UI**. It revokes client
mutations on content/settings/usage tables; writes go through owner-scoped API and
server-only RPCs. Apply only new migrations to an existing project. Do not replay
old scripts or reset an existing project to resolve a migration error.

The runner is opportunistic in the API: three simultaneous owners, up to five jobs
per wake. Submitting or visiting the queue wakes work. Closing the browser does not
cancel accepted work; a sleeping/restarted API requires a later visit to resume.
Workers heartbeat every 15 seconds; leases last 60 seconds. After 45 seconds
without a heartbeat the UI labels the durable last stage as paused. SSE connections
renew after 50 seconds with a bearer header, account rechecks and a new snapshot.

Cost details expire after **30 days**; current UTC-month totals survive detail
cleanup, and unresolved reservations survive until reconciled. To clean data even
with no visits, explicitly enable [the retention schedule](../../supabase/retention.sql)
in the target database after testing it. It deletes expired content and settled
cost detail and never calls a paid provider. Verify the cron job is active. The
API also performs scoped cleanup when waking work; that alone does not guarantee
retention for inactive accounts.

Unknown calls with a saved generation ID are looked up with `GET /generation` and
settled idempotently in their original month. Calls without an ID remain reserved.
An operator must first establish the outcome/cost in provider records; never clear
or rerun an unknown paid attempt by guessing zero. After verification, an authorized
operator may invoke `settle_analysis(owner_uuid, reservation_uuid, verified_cost)`
through the server/database maintenance path. Do not grant this RPC to browsers.
There is no automatic administrative access to the user's source or prompts.

### Database gate on an existing disposable local runtime

Use an already-migrated Supabase-compatible database with pgTAP, on loopback with
a name ending `_test`. Set `LINKSIFTY_TEST_DATABASE_URL` privately; never commit or
print it. The gate refuses remote/non-test destinations and installs nothing:

```sh
uv run --package linksifty python backend/tests/integration/check_processing_database.py
```

This runs account/processing/recovery pgTAP (63 assertions) and two overlapping 0.60 USD reservations under
a 1 USD cap. Only one may be admitted. It cleans up only the random test-owned UUID.
Exit **77** means unavailable runtime, not a pass. No database gate has passed just
because the mocked API suite passed.

### Prepared local test runtime (2026-10-15)

The owner-approved local gate (through migration 000006) passed on PostgreSQL 17.11 with pgTAP 1.3.4.
Homebrew PostgreSQL is keg-only at `/opt/homebrew/opt/postgresql@17/bin`;
pgTAP was built from its checksum-verified official PGXN 1.3.4 archive using
that installation's `pg_config`. No service starts at login.

The temporary cluster `/private/tmp/linksifty-processing-pg17` is stopped. To
rerun its synthetic fixtures, start it explicitly on loopback, run the gate,
then stop it:

```sh
/opt/homebrew/opt/postgresql@17/bin/pg_ctl -D /private/tmp/linksifty-processing-pg17 -l /private/tmp/linksifty-processing-pg17/server.log -o "-h 127.0.0.1 -p 55439 -k /private/tmp/linksifty-processing-pg17" -w start
PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH" LINKSIFTY_TEST_DATABASE_URL=postgresql://linksifty_test_runner@127.0.0.1:55439/linksifty_processing_test uv run --package linksifty python backend/tests/integration/check_processing_database.py
/opt/homebrew/opt/postgresql@17/bin/pg_ctl -D /private/tmp/linksifty-processing-pg17 -m fast -w stop
```

This URL contains only the synthetic local role and disposable database, no
credential. Temporary directories may be removed by the OS. To recreate, use
`initdb` with a fresh dedicated cluster, create a database ending `_test`, load
`backend/tests/integration/bootstrap_local_auth.sql` as its owner, then apply
all `supabase/migrations/*.sql` in lexical order with `psql -v ON_ERROR_STOP=1 -1`.
The bootstrap requires a fresh `auth` schema and cluster roles. It mirrors the
minimal auth/table-grant contract only; it does not run GoTrue, PostgREST or JWT
verification. Never apply this fixture to hosted Supabase or an existing cluster.

### Stuck at checking readable content after 000005

Apply `supabase/migrations/20261015_000006_source_hash.sql` in Supabase SQL Editor.
It replaces extension-schema-dependent `digest()` calls in fetched/pasted source
writes with built-in SHA256; it preserves the fixed search path and permissions.
An `extensions`-schema pgcrypto fixture reproduces the old SQLSTATE 42883 error.
Refresh afterward: interrupted jobs without an uncertain paid call can recover
after their 60-second lease expires. Do not resubmit the URL or reset reservations.
This fix requires SQL only, without a frontend/backend redeploy.

### Hosted Stage 2 acceptance (explicit paid approval required)

1. Verify each user sees only their own usage, settings, links, events and result.
2. Set a staging user's cap to 0 USD: inference must not start. Restore its chosen cap.
3. With approved paid-test scope, submit one ordinary complete article and compare
   provider actual cost against app spend, reservation and remaining balance.
4. Observe source acquisition, analysis and saved result with eight criteria/citations.
5. Use a blocked source: paste is requested without a model call; paste full content.
6. Close the tab during work, reopen, then restart the API during a staged attempt.
   Confirm truthful paused/recovery state and no duplicate paid request.
7. Disconnect/reconnect SSE and expire/reject the account; stale private data clears.
8. Verify threshold affects new analyses only and admin edits enforce the new budget.
9. Verify cron execution, 30-day cleanup, UTC reset and prior-month reconciliation in staging fixtures.

Code completion does not itself authorize production migration, deployment or
unbounded paid tests. Record those acceptance results separately.

## Brave source discovery and Langfuse tracing (migration 000007)

Apply `supabase/migrations/20261015_000007_brave_research.sql` after 000006, then deploy the matching backend/frontend. It adds opt-in job research state, separate search reservation/provider metadata, source IDs and stronger exact citation checks. No migration or external configuration has been applied to hosted services by this agent.

Configure these **server-only Render** variables (never VITE variables):

| Variable | Purpose |
| --- | --- |
| `BRAVE_SEARCH_API_KEY` | Brave Search API project key |
| `BRAVE_SEARCH_PRICE_PER_REQUEST_USD` | Positive USD/request rate verified against your subscribed plan; default 0 disables search |
| `LANGFUSE_ENABLED` | `true` enables tracing; default `false` |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | Langfuse project credentials |
| `LANGFUSE_BASE_URL` | Project region URL; EU default `https://cloud.langfuse.com` |
| `LANGFUSE_TRACING_ENVIRONMENT` | e.g. `production` |

Brave uses one Web Search API query per opted-in public link, at most ten transient URL candidates and at most five extra page fetch attempts. The unchecked Add checkbox discloses query transfer and plan charge. Pasted text is not sent to Brave. Missing key/rate disables this capability; ordinary single-source analysis remains available. We do not infer a free tier or inspect your account/subscription. Search queries are short terms from a public article URL (fallback: initial source words); they are sent only to Brave. Search response snippets/payloads are not persisted or used as proof. Retain plan rights appropriate for your use; article passages are fetched separately with existing source guards.

One host per candidate and identical normalized-content hashes reduce duplicates; this does not establish publisher independence. Only successfully fetched readable content enters comparison, bounded to 12K characters per source. Detail shows which pages were supplied and warns when extra sources were unavailable/unverified. Corroboration cannot receive a high score from primary-only evidence. URL/ID/excerpt offsets are validated against stored text; no search snippet alone counts as confirmation. Official X API and grounded chat remain separate work.

Usage totals now combine **actual OpenRouter cost and Brave requests at the configured plan rate**. The latter is plan-derived, not a returned invoice amount. Both consume the same per-user monthly USD cap. Search reserves before sending; confirmed successful HTTP responses settle at configured rate, even if no usable URLs returned. Unknown/non-successful outcomes stay reserved conservatively; no automatic paid search repeat. If needed, verify outcome in Brave billing first, then use the existing authorized settle_analysis maintenance path with the original reservation. Never clear or resend by guessing zero. Repeating model analysis reuses stored research instead of buying another search.

When `LANGFUSE_ENABLED=true` and project keys are configured, Langfuse now records relevant analysis events **including article content by default**, without a second content toggle. This replaces the initial metadata-only implementation. Traces include primary text, supporting passages (up to 12K characters each), URLs/query and candidate decisions, model messages/raw completion content and validated output, citation checks, stage writes, reservations/settlement, recovery, heartbeat and final save outcomes. The generation includes timings, tokens, safe rejection reason and known cost. Opaque job/item IDs correlate attempts; account IDs, lease tokens and authentication headers are never passed to tracing. Configured provider credentials are scrubbed from text, with additional common credential/email/URL-userinfo redaction. Redaction is defense in depth, not a guarantee that arbitrary personal information in an article is anonymous. Each text field is capped at 200K characters with an explicit truncation marker. Additional-source traces include the passage supplied to analysis, not an assertion of full-page completeness. Explicit spans/events avoid blanket HTTP/database logging and never export Brave response snippets. Exceptions reduce to class names; SDK failures do not affect processing or trigger provider retries, and shutdown flushes in a worker thread. Use SDK 5 with current Cloud or a compatible v4 server; self-hosted v3 requires a separately reviewed older compatible SDK.

Test with mocks first. Before an authorized paid hosted test, apply migration, configure keys/rate/region and deploy, then opt one public link into search. Verify stages, source provenance, configured search charge plus actual model cost, redacted article/model trace, invalid-output reason and no duplicate request on recovery. No key values should be pasted into chat. See [official Brave reference](https://api-dashboard.search.brave.com/api-reference/web/search/get) and [Langfuse SDK documentation](https://langfuse.com/docs/observability/sdk/overview).

## Duplicate links and whitespace-only citation repair (000008)

Apply `supabase/migrations/20261016_000008_duplicate_links.sql` after 000007, then deploy matching code. Both ordinary and Brave submission are guarded in PostgreSQL under the existing owner-profile lock; racing equivalents create one item/job. A duplicate in a batch rejects the entire batch before trial use, jobs or worker wake. API returns 409; frontend also disables known duplicates and preserves input. Matching considers only the owner's unexpired links and ignores fragment, host/scheme case, default port and empty root-path differences. Path case and query semantics stay significant. Other users can independently analyze the same URL. Expired records do not prevent a new submission.

Existing duplicate records are not deleted, merged or charged again by migration. Resume is guarded against another unexpired matching link that is queued, processing or completed. If both legacy items have failed, explicitly resuming one is allowed; trying to resume the other concurrently is blocked. Use an existing item rather than submitting a duplicate. Current in-flight paid attempts are not silently cancelled or reset.

Citation matching now re-anchors whitespace-only differences (including line breaks/non-breaking spaces) to the exact original source substring before storing offsets. No fuzzy, case-insensitive, paraphrase or cross-source substitution is accepted. `unknown_citation_source` separately identifies an ID not in the supplied source set. The reported hosted `invalid_citation` cannot be conclusively diagnosed without its actual response; a truly unmatched passage still fails. No paid retry happens automatically.

The later live trace showed an appended `...` on the rejected quote. After deploying
the trailing-omission repair, a final `...` or `…` may be removed only if the entire
remaining quote (at least 10 characters) matches the attributed source, allowing
the existing whitespace re-anchoring. Literal source ellipses are matched first
and preserved. Internal omissions, changed words/case and wrong-source quotes
still fail. The prompt now explicitly forbids added omission markers, translations
and joined passages. `citation.result.trailing_ellipsis_removed` distinguishes
this repair from whitespace-only re-anchoring. No migration or model switch is
required. This does not repair stored failed results or trigger paid retries;
new output must be processed by the updated backend.

### No Brave dashboard usage after setup

Configuration does not opt old items into search. Resume preserves original consent/context; old model-only items stay model-only. For an authorized live test, submit a new public URL with **Search additional sources with Brave** checked. If disabled, inspect `/v1/capabilities` through the authenticated app and verify the deployed backend has `BRAVE_SEARCH_API_KEY` plus positive `BRAVE_SEARCH_PRICE_PER_REQUEST_USD`. Redeploy/restart after setting variables. Primary content must also pass fetch/completeness guards before search can run. Do not use dashboard absence alone to infer a billing/telemetry failure or automatically retry paid calls.

## Inspecting complete analysis traces

Deploy the matching backend; no new environment flag or database migration is required for expanded tracing. Existing duplicate-link migration 000008 is a separate requirement for that earlier feature. In your Langfuse project, open a new `processing` trace: `processing.started` identifies the item/public URL; root metadata carries `job_id`. Each execution/resume has a separate trace correlated by that job ID. `source.fetched` / `source.reused` show primary article text; `search.finished` / `search.reused` show the actual supporting passages; `openrouter.assessment` shows model input and validated output. `model.response` retains raw completion content even if schema/citation validation fails. `citation.check` and `citation.result` explain the attributed source, quoted passage and match/re-anchoring result.

For missing Brave usage, inspect `search.skipped` (not requested, not configured, previous uncertain request), `budget.reserved` (admitted or budget exhausted), `search.request`, `brave.http_response`, `search.response` and `source.skipped`. A failure before research appears in source validation/stage events. `stage.persisted` records actual stage-write success, and `assessment.saved` distinguishes saved output from lost ownership. `processing.finished` reports execution return, cancellation, lease loss or interruption; a normal return can still be a business failure, so inspect the final persisted stage and generation failure reason. Orphaned-cost recovery uses a separate `orphan.reconciliation` trace with reservation ID.

Trace storage is best effort, not a durable audit ledger: a crash/network outage may lose buffered observations. Supabase remains authoritative for jobs and charges. Existing traces cannot be backfilled. Article/model content is visible to authorized Langfuse project members; restrict access and configure Langfuse retention separately—Supabase's 30-day cleanup does not remove external traces. No paid hosted request or hosted retention setting was changed during local verification.

### Sessions per analysis job

After deploying session grouping, each processing attempt propagates
`session_id=linksifty:job:<job_id>` to its root observation, nested spans, events
and model generation. Executions/resumes of the same job remain separate traces
but appear together under **Sessions**. Different jobs have different sessions;
no account identifier or email is used. Standalone orphan reconciliation remains
separate because it has a reservation ID rather than a job ID. Session context
is released when the processing scope exits, including failures.

No new environment variable or migration is required. New attempts populate
sessions; old traces are not backfilled. To reduce the Tracing table to attempts,
filter **Is Root Observation** to **True** only, then open a processing trace for
its individual steps. Instrumented processing attempts are exported when tracing
is enabled; ordinary page loads/API polling are not. Sessions organize telemetry
and do not add conversation memory to the model. Export remains best effort.


## Editable assessment rubric (000009)

Apply `supabase/migrations/20261016_000009_assessment_rubric.sql` after 000008.
Coordinate the migration, backend and frontend deployment: pause new processing
and let active old workers finish before enabling edited rubrics, apply the
migration, deploy the matching backend, then the frontend. Do not run mixed old
and new workers with custom rules enabled: an old worker does not consume rubric
snapshots. No environment variable or model change is required. No hosted
migration or deployment was performed by this local implementation.

GET `/v1/settings` returns `valuable_threshold` and `rubric.criteria`, each entry
containing the fixed `name`, editable `description` and integer `weight`.
PUT saves threshold and rubric atomically for the authenticated account. A
threshold-only PUT preserves its existing rubric. Unknown fields, incomplete or
duplicate criterion IDs, blank/NUL/over-1000-character descriptions and noninteger
or out-of-range weights are rejected. The new frontend requires all eight rules
from GET; an older/malformed response disables saving instead of using guessed
values. The editor explains point scale and relative weights, with the formula
in **How scoring works**. A save does not start an analysis or a paid request.

The first model reservation snapshots rubric and threshold in one transaction;
that snapshot supplies both the model descriptions and deterministic scorer.
Cached output and lease recovery retain it, even after account settings change.
An explicit fresh-analysis reset clears both snapshots only under existing
settlement and duplicate-link guards. Assessments store their original rubric;
detail displays those descriptions/weights without recomputing history. Legacy
completed/reserved records are backfilled with the original default rules. User
descriptions are rubric data, subordinate to fixed grounding/schema constraints;
all citations and independent corroboration checks remain enforced. Descriptions
are included in model input and existing redacted Langfuse tracing when enabled.

Local verification uses synthetic accounts and mocked providers. The disposable
SQL gate now includes `assessment_rubric.test.sql` and a concurrent settings-save/
model-reservation check. Production acceptance remains manual: verify owner
isolation, save a changed description/weight, authorize a new analysis if desired,
and inspect its stored rubric/model input; confirm an earlier assessment retains
its original score and rules. Never retry an uncertain paid attempt automatically.
