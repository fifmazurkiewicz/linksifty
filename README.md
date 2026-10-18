# Linksifty

Linksifty is an agent-toolkit-assisted personal web app that turns saved web links, including X posts, into source-grounded notes and a repeatable value verdict.

It is deliberately paired with a separate implementation of the same product that does not use agent-toolkit. The product contract is shared; workflow, evidence, and delivery process are the comparison surface.

## Start here

- [Product vision](docs/product/vision.md)
- [Architecture overview](docs/architecture/overview.md)
- [MVP roadmap](docs/roadmap.md)
- [Detailed completion tasks](docs/superpowers/plans/2026-10-13-linksifty-completion.md)
- [Step-by-step service and environment setup](docs/deployment/setup.md)
- [Implementation Kanban](.agent/context/changes/linksifty-personal-mvp/plan-kanban.html)
- [Architecture diagram](docs/architecture/overview.md)
- [Agent instructions](AGENTS.md)

## Local checks

The top-right appearance button switches the entire interface between light and
dark mode, including sign-in. It initially uses the system preference and saves
an explicit choice in this browser. If browser storage is blocked, switching still
works for the current visit.

```sh
uv run --package linksifty pytest backend/tests
uv run --package linksifty mypy --strict backend/src
uv run --package linksifty ruff check .
uv run --package linksifty ruff format --check .
```

If the local agent-toolkit checkout is available, also run `agent-toolkit check` for configuration drift.

## Continuous integration

[CI](.github/workflows/ci.yml) runs on pushes, pull requests, and manual dispatch.
The backend job installs `uv.lock` with `uv sync --locked --package linksifty --group dev`
and runs the Python checks above. The frontend job runs `npm ci`, lint, and the
production build inside `frontend/`, using `frontend/package-lock.json`.
CI uses Python 3.11, uv 0.12.17, and Node 22.23.2; no provider credentials are needed.
A third job builds the Docker backend and smoke-checks health, runtime PORT,
anonymous authentication and the non-root user.

The frontend test step runs `npm test -- --run` and fails on missing/failing tests.
`agent-toolkit check` remains a separate required local gate because its runtime is
not installed or bootstrapped here. SQL/RLS/concurrency and hosted acceptance are
separate gates; a green mocked suite does not certify them.

## Run the API

Copy `.env.example` to `.env` and set server-side values when integrating real providers. The health endpoint runs without provider credentials:

Environment values must be exported in the shell or provided by the hosting platform; copying the file alone does not load it. For local preview only, set `LINKSIFTY_DEMO_MODE=true`. Without this setting, `/v1/` endpoints require a Supabase-verified bearer token. Configure the Supabase URL, anon key, and server-only service-role key and apply all migrations in filename order to enable real item submission, listing, and detail retrieval. Set `FRONTEND_ORIGIN` to the deployed frontend origin for CORS.

```sh
uv run --package linksifty uvicorn linksifty.main:app --reload
```


## Docker backend

The root Dockerfile packages only the backend, with Python 3.11.16, uv 0.12.17
and locked production dependencies. Build from the repository root:

```sh
docker build -t linksifty-api .
docker run --rm -p 8000:8000 --env-file .env linksifty-api
```

The API runs as a non-root user, defaults to port 8000 and honors `PORT`.
Credentials are supplied at runtime; `.env` never enters the build context.
On Render choose Docker, root context `.`, Dockerfile `./Dockerfile`, leave
Docker Command unset and set the health path to `/health`.
See the [setup guide](docs/deployment/setup.md) for environment values and current
MVP limitations. The frontend remains a separate Vercel build.


## Processing and usage

The queue now shows persisted live stages, source-backed results, manual-content
recovery and actual OpenRouter USD spend/reservations. Settings saves the future
valuable threshold; administrators can edit per-user monthly caps, including zero.
Settings also shows the eight assessment criteria. Each account can edit descriptions and integer weights (1–10), saved together with its valuable threshold. New model analyses capture those rules; completed and interrupted analyses keep their original rubric, visible in detail. Requires migration `20261016_000009_assessment_rubric.sql` and matching backend/frontend.

New analyses select numbered source passages. The backend supplies each saved
citation’s original text and source, preventing model transcription and attribution
errors. Existing stored results remain compatible; deploy the backend to activate.

Use server-only `OPENROUTER_API_KEY` and `OPENROUTER_MODEL=openai/gpt-4o-mini`.
Other model IDs fail closed until their cost bounds are verified. Default monthly
budget is 10 USD per user; inference first reserves a conservative maximum and
then settles provider-reported cost.

Migration 000005 and the matching frontend/backend must ship together. Workers
are bounded and resume on authenticated visits; no paid always-on worker is used.
Cost records retain 30 days, with unresolved reservations and current-month totals
preserved. Enable and verify the database retention schedule for inactive users.
See [setup section 13](docs/deployment/setup.md#13-processing-usage-retention-and-recovery)
for database gates, activation and recovery. No hosted readiness is implied.

### Optional Brave + Langfuse

The Add screen supports explicit Brave source checking for public links (one search, up to 20 additional page fetch attempts (migration 000010)), after migration `000007` and server-only key/verified plan-rate configuration. Search charges share the USD cap with actual OpenRouter costs. Metadata-only Langfuse diagnostics are opt-in and cannot block processing. No secret goes into the frontend. See [setup](docs/deployment/setup.md#brave-source-discovery-and-langfuse-tracing-migration-000007). Real provider activation remains an operator step; source deduplication is heuristic, not proof of independent fact verification.

### Calibrated assessment rules

Migration `20261017_000010_assessment_calibration.sql` introduces purpose-aware
learning value, explicit Not applicable / Not verified states, and hype judgments
requiring cited primary-source evidence. New results show scored-criterion
coverage and explain the verdict; historical results keep their original rules.
Future settings upgrade default descriptions while preserving custom wording and
weights. Deploy database, backend and frontend together; see the
[rollout instructions](docs/deployment/setup.md#calibrated-assessment-and-20-source-checking-migration-000010).

### Delete links and analyses

Each queue entry has **Delete**. Use the checkboxes and **Delete selected** to
remove a group (up to 50 visible links). Confirm permanent removal of the links,
source text, analyses, citations, chats and jobs. Billing records remain for
charge reconciliation; deleting content does not refund charges or trial usage.
Requires migration `20261017_000011_delete_items.sql`; see the
[activation notes](docs/deployment/setup.md#permanent-link-deletion-migration-000011).

### Chat about an analysis and its topic

Completed analyses now include a saved conversation with inspectable source
passages. Chat uses the analysis, original article, saved research and recent
conversation first. Only missing evidence triggers web research: at most one
Brave search per question, followed by safe page reads and a final answer.
Model and search calls share the existing monthly budget. Request IDs prevent
duplicate paid work after a network error. Deleting/expiring the item removes
chat content while preserving charge reconciliation.

Requires `20261018_000013_analysis_chat.sql` and matching backend/frontend.
Existing OpenRouter and optional Brave configuration is reused; chat works
with saved material when Brave is unavailable. See [rollout and recovery](docs/deployment/setup.md#analysis-and-topic-chat-migration-000013).
