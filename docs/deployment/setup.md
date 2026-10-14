# Linksifty setup: Supabase, Render, Vercel, OpenRouter and X

Checked against repository code and official documentation on **2026-10-14**. Google OAuth is the requested login method.
Follow the steps in order. Example names and URLs below must be replaced with
your own. Keep actual keys in your password manager and platform environment
settings; do not put them in Git or this document.

## 1. Decide what you are setting up now

Use a **development/staging environment** while the remaining coding tasks are
completed. You can prepare accounts and configure hosting now, but the current
code does not yet provide the complete authenticated browser workflow.

| Component | What works now | What still needs implementation |
| --- | --- | --- |
| Supabase | Server token verification, owner-filtered item API, transactional item/job submission | Ownership constraints, client write restrictions, SQL validation, retention cleanup |
| Render API | `/health`; authenticated item list/detail/submission | Job runner, provider calls, complete product routes |
| Vercel frontend | Inbox/Add/Settings preview; configurable API URL | Supabase login/session handling and bearer tokens, detail/chat/recovery/settings |
| OpenRouter | Environment variable is read | Model configuration, provider adapter, citation validation, atomic cost cap |
| X | Environment variable is read | Official acquisition adapter and access-error fallback |

With demo mode off, the current Vercel frontend will get **401** when listing
items because it does not send a user token yet. That is an implementation gap,
not a missing hosting setting. Real submitted jobs currently stay `queued`.
Do not enable demo mode on the real-data service to bypass this.

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

Open **Settings → API Keys**. For the current repository configuration, obtain:

- Legacy **anon** JWT → `SUPABASE_ANON_KEY`.
- Legacy **service_role** JWT → `SUPABASE_SERVICE_ROLE_KEY`, server-only.

The repository currently sends its service key as both `apikey` and a Bearer
JWT. Therefore **do not substitute an `sb_secret_...` key into the service-role
variable without updating the adapter first**. The anon variable is used only
as `apikey`, but the documented current baseline uses the matching legacy pair.

Supabase now recommends publishable/secret keys and says legacy keys are being
deprecated by the end of 2026. Migrating the adapter is required before relying
on this setup long term. If legacy keys are unavailable/disabled, pause backend
activation and update key handling; do not weaken authentication to work around it.
[API key types and header rules](https://supabase.com/docs/guides/getting-started/api-keys).

### 3.3 Apply the development schema

On a **fresh staging project**, open **SQL Editor → New query**. Paste the entire
contents of each migration and run them in this order:

1. [`20261012_000001_personal_mvp.sql`](../../supabase/migrations/20261012_000001_personal_mvp.sql)
2. [`20261013_000002_submission_rpc.sql`](../../supabase/migrations/20261013_000002_submission_rpc.sql)
3. [`20261014_000003_account_approval.sql`](../../supabase/migrations/20261014_000003_account_approval.sql)
4. [`20261014_000004_account_notifications.sql`](../../supabase/migrations/20261014_000004_account_notifications.sql)

These scripts are not all rerunnable. If a migration has already succeeded,
do not run it again or delete existing tables to silence an error. Check the
project's migration history/SQL query history first. Future migrations must be
applied afterward in filename order; never edit an already-applied migration.

Check Table Editor for `settings`, `items`, `source_contents`, `jobs`,
`assessments`, `citations`, `chat_messages`, `account_profiles`, and
`account_notifications`. Check Database Functions for `claim_next_job`,
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
| `SUPABASE_ANON_KEY` | Supabase legacy anon JWT | Yes for the documented baseline |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase legacy service_role JWT | Yes; server-only |
| `LINKSIFTY_DEMO_MODE` | `false` | Yes; real environment |
| `FRONTEND_ORIGIN` | `https://linksifty.fmazurkiewicz.dev` with no trailing slash | Set after step 5, then restart/redeploy |
| `LINKSIFTY_ADMIN_EMAIL` | Verified Google account email for the initial administrator | Yes for owner admin access; private server setting |
| `RESEND_API_KEY` | Resend API key with permission to send from the verified sender domain | Yes for approval email; server-only |
| `RESEND_FROM_EMAIL` | Sender identity on a domain verified in Resend, e.g. `Linksifty <noreply@example.com>` | Yes for approval email |
| `OPENROUTER_API_KEY` | OpenRouter inference key | Optional preparation; no provider calls are wired yet |
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
6. For C3.3, choose a model that supports JSON-schema structured output and record
   its exact model ID and current pricing. This choice can wait until the adapter
   is implemented; do not assume a particular model from an older guide.

Key credit limits can reject further requests at the limit.
[OpenRouter authentication and key limits](https://openrouter.ai/docs/api_reference/authentication).
Schema support depends on the model/provider.
[Structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs).

There is **no `OPENROUTER_MODEL` env variable read by the code yet**, and no
implemented application monthly budget enforcement. The `settings` database
has a default 1000-cent budget field, but a field alone does not reserve/enforce
spending. Key-level limits are an additional control; C3.4 must implement the
atomic application cap before provider activation.

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
SUPABASE_ANON_KEY=<legacy-anon-JWT>
SUPABASE_SERVICE_ROLE_KEY=<legacy-service-role-JWT>
OPENROUTER_API_KEY=
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
VITE_SUPABASE_ANON_KEY=<supabase-publishable-or-anon-key>
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
`SUPABASE_DB_PASSWORD`, `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`, `X_API_KEY`,
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

The API still does not process queued jobs into completed assessments. A successful
sign-in and account approval do not prove the unfinished assessment runner.

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
| API 503 for persistence | Correct legacy service-role JWT; both migrations applied; DB/API reachable |
| Submitted item never leaves queued | Runner C4 is not implemented yet; credentials do not start it |
| First Render request is slow | Free-service cold start; wait for service health before diagnosing credentials |
| No OpenRouter/X calls | Adapters are unfinished, even if env variables are present |

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
