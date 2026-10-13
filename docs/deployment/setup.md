# Linksifty setup: Supabase, Render, Vercel, OpenRouter and X

Checked against repository code and official documentation on **2026-10-13**.
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

These scripts are not all rerunnable. If a migration has already succeeded,
do not run it again or delete existing tables to silence an error. Check the
project's migration history/SQL query history first. Future migrations must be
applied afterward in filename order; never edit an already-applied migration.

Check Table Editor for `settings`, `items`, `source_contents`, `jobs`,
`assessments`, `citations`, and `chat_messages`. Check Database Functions for
`claim_next_job` and `submit_fetch_items`. The migrations enable RLS, but this
alone does not prove complete ownership isolation. C1 hardening and a two-user
SQL test remain release gates. [Supabase tables/SQL Editor](https://supabase.com/docs/guides/database/tables).

### 3.4 Create your user and restrict signup

1. In **Authentication → Sign In / Providers**, enable email/password sign-in.
2. Disable **Allow new users to sign up** and anonymous sign-ins for this personal MVP.
3. In **Authentication → Users**, use the user creation action to create your
   account with email/password. Ensure the account is confirmed before testing
   password sign-in; use the dashboard's confirmation option when available.
4. Keep public signup disabled. Existing users can still sign in.
5. Record the user's UUID if needed for SQL verification; it is not an API key.

Email confirmation/password recovery via email requires working email delivery;
configure custom SMTP if you choose those flows later. Password sign-in with an
already confirmed staging user does not require sending an email on each login.
[Supabase Auth configuration](https://supabase.com/docs/guides/auth/general-configuration).

Set final Site URL/redirect URLs after Vercel gives you the stable application URL
(step 6). No OAuth provider is required for the current email/password plan.

## 4. Configure the API on Render

### 4.1 Create the web service

1. Dashboard → **New → Web Service** → connect your GitHub repository.
2. Name it, for example, `linksifty-api-staging`.
3. Select the branch containing the deployable code and choose a nearby region.
4. Runtime: **Python**.
5. **Root Directory: leave blank** (repository root). Do not set `backend/`:
   this uv workspace needs the root `pyproject.toml` and `uv.lock`.
6. Build Command:

   ```sh
   uv sync --locked --package linksifty --no-dev
   ```

7. Start Command:

   ```sh
   uv run --locked --no-sync --package linksifty uvicorn linksifty.main:app --host 0.0.0.0 --port "$PORT"
   ```

8. Health Check Path: `/health`.
9. Choose the intended instance plan after reviewing its current limits/pricing.
   A Free web service is adequate for staging if available.
10. Keep automatic deploys disabled during initial setup if you want to inspect
    each staging revision manually; enable a CI-gated deploy policy later.

Binding to `0.0.0.0` and Render's `PORT` is required. No Dockerfile, PostgreSQL
service on Render, disk, cron or separate worker is needed for the approved model.
[FastAPI hosting](https://render.com/docs/deploy-fastapi).

### 4.2 Add Render environment variables

In the service's **Environment** settings, enter raw values without surrounding
quotes. Keep secret values in the host's secret/environment storage.

| Variable | Value/source | Needed now? |
| --- | --- | --- |
| `SUPABASE_URL` | Your Supabase project HTTPS URL | Yes for authenticated persistence |
| `SUPABASE_ANON_KEY` | Supabase legacy anon JWT | Yes for the documented baseline |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase legacy service_role JWT | Yes; server-only |
| `LINKSIFTY_DEMO_MODE` | `false` | Yes; real environment |
| `FRONTEND_ORIGIN` | Stable Vercel origin, e.g. `https://<your-app>.vercel.app`, no trailing slash | Set after step 5, then restart/redeploy |
| `UV_VERSION` | `0.12.17` | Set for reproducible builds |
| `PYTHON_VERSION` | Optional fully qualified version, e.g. `3.11.16` | Repo `.python-version` already selects 3.11; this overrides it |
| `OPENROUTER_API_KEY` | OpenRouter inference key | Optional preparation; no provider calls are wired yet |
| `X_API_BEARER_TOKEN` | Official X app-only bearer token | Optional preparation; X adapter is unfinished |
| `PORT` | Supplied by Render | Do not manually set |

The Python version env variable requires all three version components; the
repository `.python-version` may use `3.11`. Render supports `UV_VERSION` for uv
projects with a root lockfile. [Python/package-manager versions](https://render.com/docs/python-version).

### 4.3 Deploy and check health

Deploy the service and inspect build/start logs. Save the resulting base URL:
`https://<your-render-service>.onrender.com`.

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
8. Add this environment variable to **Production**:

   ```dotenv
   VITE_API_BASE_URL=https://<your-render-service>.onrender.com
   ```

   Use the base origin, without `/v1`, `/health`, or a trailing slash.
9. Deploy. Save the stable project URL, `https://<your-app>.vercel.app`.
10. If Preview builds are needed, configure the variable separately for Preview.
    Use a staging API/data set; the current API accepts only one frontend origin.

Vercel hosts the static frontend; the Python API stays on Render.
[Vite deployment](https://vercel.com/docs/frameworks/frontend/vite).

Vite's `VITE_` values are included in the browser bundle. Do not add service-role,
OpenRouter or X keys to Vercel for this static frontend, and never give them a
`VITE_` prefix. Changing `VITE_API_BASE_URL` requires a new deployment/build.
[Vite env behavior](https://vite.dev/guide/env-and-mode.html),
[Vercel environment scopes/redeployment](https://vercel.com/docs/environment-variables).

**Only `VITE_API_BASE_URL` is read by today's frontend.** Supabase frontend env
names will be finalized in C6.2; adding speculative variables now does not
create a login flow. No `/auth/callback` route currently exists either.

## 6. Connect the final origins and Auth URLs

1. On Render set `FRONTEND_ORIGIN` to the exact stable Vercel origin:
   `https://<your-app>.vercel.app`.
2. Save and restart/redeploy Render so the API reads the new setting.
3. In Supabase **Authentication → URL Configuration**, set **Site URL** to the
   stable Vercel URL.
4. Add only the redirect URLs used by the eventual login/recovery implementation.
   For local development, allow `http://localhost:5173/**` if those flows use it.
   For production, prefer exact implemented destinations. Do not invent a
   callback path or broadly allow every preview domain.
5. When adding a custom domain later, update all three together: Vercel domain,
   Render `FRONTEND_ORIGIN`, and Supabase Site URL/redirect destinations.

Supabase Auth URL configuration controls redirects. Render CORS controls browser
API access; changing one does not configure the other.
[Site URL and redirect allowlist](https://supabase.com/docs/guides/auth/redirect-urls).

At this stage the browser can reach the API origin, but an authenticated Inbox
still waits for C6.2's login and token attachment. A valid CORS response does not
replace authentication.

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
`X_API_SECRET`, or any frontend Supabase env variables. Model/login configuration
will be documented when those adapters are implemented. Render's `PORT`,
`PYTHON_VERSION` and `UV_VERSION` are hosting settings, not fields in `Settings`.

## 10. Verify staging without the unfinished login UI

1. Check Render `/health` returns `{"status":"ok"}`.
2. Check unauthenticated `/v1/items` returns 401, with demo mode false.
3. Sign your confirmed user in through a local REST client to obtain a short-lived
   Supabase **user access token**:
   - POST `https://<project-ref>.supabase.co/auth/v1/token?grant_type=password`.
   - Header `apikey`: your project's anon key.
   - Header `Content-Type`: `application/json`.
   - JSON body: your user `email` and `password`.
   - Keep the returned `access_token` private. Do not paste it into a repository,
     shared logs, screenshots or chat. Use a local client without synced history.
4. In Render `/docs`, use **Authorize** with that user token (never the service-role
   key), then GET `/v1/items`. Expect 200 and an initially empty `items` array.
5. POST `/v1/items` with a staging URL:

   ```json
   {"sources":[{"url":"https://example.com/article"}]}
   ```

   Expect 202 and status `queued`. GET `/v1/items` again and check the record
   persists. `queued` is the correct current result; processing is unfinished.
6. In Supabase Table Editor confirm the item and job have your user's UUID.
7. Before release, use a second staging user and executable SQL/RLS tests to verify
   cross-owner reads/writes and child ownership. Do not infer RLS safety from a
   successful service-role API request; service_role bypasses RLS.

The password token endpoint is the Supabase Auth API used by password sign-in;
verify sign-in failures against [password authentication documentation](https://supabase.com/docs/guides/auth/passwords).

## 11. Troubleshooting

| Symptom | Check |
| --- | --- |
| Render build cannot find workspace/lockfile | Root Directory must be blank, repository contains root `uv.lock` and `backend/` |
| `uv` missing or wrong version | Root lockfile present; set `UV_VERSION`; inspect build logs |
| Render fails to bind a port | Start command includes `--host 0.0.0.0 --port "$PORT"` |
| Browser requests localhost after deployment | Set `VITE_API_BASE_URL` in the correct Vercel environment and redeploy |
| Browser CORS error | Render `FRONTEND_ORIGIN` exactly matches browser origin; no trailing slash; restart API |
| Vercel preview URL fails but stable URL works | Current backend allows one configured origin; previews need a separate staging arrangement |
| API 401 | Missing/expired user access token; current frontend does not attach one yet |
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
- [ ] C5/C6 authenticated login, Inbox/detail, paste recovery, deletion and settings work.
- [ ] C7 chat/X work, or any scope change is explicitly accepted and recorded.
- [ ] 30-day cleanup actually executes and cascade-deletes; an expiry field alone is insufficient.
- [ ] Logs omit tokens, provider credentials and source bodies.
- [ ] Correct CORS/Auth URLs, cold-start smoke checks and the 20-link evaluation pass.

This document prepares manual E1 setup. It does not mark E1 or C8.3 complete:
no account, migration, deployment or paid call was executed when writing it.
