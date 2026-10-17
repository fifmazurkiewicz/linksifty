# Linksifty architecture

Updated 2026-10-16. The repository is a monorepo: `backend/` is the uv-managed FastAPI package, `frontend/` is React/TypeScript/Vite with npm. Root documentation and `uv.lock` are shared.

## Implemented request path

1. The browser starts Google OAuth through Supabase and restores its session. Every API request sends that session's access token. `api/auth.py` asks Supabase's authenticated user endpoint to validate it and returns the verified UUID and email. Missing/rejected tokens return 401; unavailable authentication returns 503.
2. FastAPI routes pass that UUID to `ItemService`. The service uses the application repository contract; concrete Supabase HTTP integration is wired in the entrypoint.
3. Every repository query includes an owner predicate. Submission calls the server-only `submit_fetch_items` transaction to insert item and job together before returning 202. List and detail routes are wired; read/delete repository methods still need routes.
4. `/v1/me` creates a pending profile for new users and reports the verified owner as admin only when `LINKSIFTY_ADMIN_EMAIL` matches. Pending users may submit three trial links; rejected users are blocked. The admin API returns account metadata only and never exposes another user's content. Approval mail is sent through Resend after the status transaction commits.
5. Explicit `LINKSIFTY_DEMO_MODE=true` enables sample responses. Demo responses carry `demo: true`; production defaults to false.

This path is verified using mocked HTTP/frontend tests and local pgTAP/RLS gates. The owner reports hosted migrations through 000006 applied; this agent has not independently run hosted acceptance.

## Locally implemented processing path

`main.py` composes the owner-scoped `ProcessingRepository`, `OpenRouterClient` and
`ProcessingService`. Routes in `api/processing.py` translate HTTP; orchestration
lives in the application service, exact budget/lease concurrency in PostgreSQL,
and the deterministic score/verdict remains in pure domain code.

1. Submission persists item/job together and wakes bounded API work (three owners
   concurrently, up to five jobs per wake). A later authenticated queue visit
   resumes claimable work. No paid always-on worker or broker is used.
2. Each redirect is validated and pinned to public DNS answers. Fresh proxy-free
   clients isolate cookies, Host and TLS SNI. Time/MIME/body limits and content
   checks reject partial/blocked/unsupported sources into manual paste before any
   paid call. Text acquisition skips scripts, navigation and other boilerplate.
3. SQL reserves against current UTC-month actual spend plus all unresolved
   reservations under an owner settings lock. Only the verified model's context
   bound is supported: full context + bounded output at enforced provider price
   ceilings, without a tokenizer-size heuristic. Unknown models fail closed.
4. The adapter supplies bounded, ID-labelled source passages and validates structured
   eight-criterion output selecting those IDs. It restores the exact original excerpt
   and source itself; model-written quotes/source IDs are not accepted.
   A response is saved under its lease before settlement; a late response's
   generation ID remains bound to its original reservation. Actual provider USD
   is settled idempotently into the reservation's original month. A missing cost
   remains reserved, never treated as free or automatically sent again.
5. The pure scorer computes the final result using the threshold captured by the
   atomic reservation. Fenced SQL commits result/citations/completed state together.
   A saved result can be recovered after interruption without repeating inference.
6. Workers heartbeat every 15 seconds, with 60-second fenced leases. Snapshots
   expose freshness (45 seconds) separately from durable stage. After a crash the
   UI shows paused work; a later visit claims an expired lease. A reserved attempt
   resumes reconciliation rather than starting another model call.
7. Bearer-authenticated SSE publishes owner-only snapshots and usage with bounded
   50-second connections, account access rechecks and reconnect recovery. Frontend
   session expiration/sign-out clears private state and aborts the prior stream.

These paths have mocked application/API/adapter tests; PostgreSQL/hosted checks
are separate gates. The older standalone `AssessmentService` remains a draft-to-
score utility; it is not the runtime provider orchestration path. Dedicated X,
chat and additional-source enrichment remain planned.

## Data and trust

Migration `20261015_000005_processing_usage.sql` adds exact numeric USD totals and
reservations, server-controlled monthly caps, stage/result/heartbeat fields and
owner-scoped processing RPCs. Browser mutation privileges on settings/content/
usage are revoked; even admins cannot use content APIs for another user. The
admin endpoints expose account usage/limits only, without source access.

Cost details expire after 30 days; current-month totals and unresolved
reservations survive detail cleanup. The API performs owner-scoped cleanup on
wake/read; `supabase/retention.sql` defines the explicit database schedule required
for inactive accounts. Expired-source reservations with a generation ID can be
reconciled without source content. No-ID outcomes require verified operator
reconciliation before further paid attempts. The cron script is provided, not
activated by the agent.

Database tests include pgTAP and a local disposable-database concurrent-reservation
gate. No database validation is inferred from service-role HTTP mocks; cross-owner
foreign-key hardening and the remaining broader C1/MVP work retain their own gates.
Provider credentials stay server-only. Source/provider text is untrusted; all
private reads and writes carry verified owner scope. Existing read/delete
repository helpers still need product routes outside this change's scope.

## Diagrams

- [Processing/recovery contract HTML](../../.agent/context/changes/processing-usage-inbox/lifecycle.html) · [editable JSON](../../.agent/context/changes/processing-usage-inbox/lifecycle.json). Includes cost uncertainty and heartbeat/lease behavior; not proof of hosted execution. Automated browser evidence remains separate from deterministic artifact checks.

- [Account access and approval HTML](../../.agent/context/changes/multi-user-access-admin/architecture.html) · [editable JSON](../../.agent/context/changes/multi-user-access-admin/architecture.json) (Stage 1 target and local implementation; hosted activation remains manual)

The new diagrams are planning views: solid current request relationships and labelled planned relationships. They are not evidence of deployment. Earlier diagrams are retained as historical design artifacts.

- [Architecture HTML](../../.archify/architecture-linksifty-status-20261013-010804/linksifty-status.html) · [editable JSON](../../.archify/architecture-linksifty-status-20261013-010804/candidate.json)
- [Target lifecycle HTML](../../.archify/lifecycle-linksifty-target-20261013-010804/linksifty-target.html) · [editable JSON](../../.archify/lifecycle-linksifty-target-20261013-010804/candidate.json)

See [completion plan](../superpowers/plans/2026-10-13-linksifty-completion.md) and [Supabase setup](../deployment/supabase.md) for tasks and activation steps.


## Docker deployment slice — 2026-10-14

The Render backend is packaged by the root Dockerfile (Python 3.11.16, uv
0.12.17, locked production dependencies, UID 10001). Runtime PORT and server
credentials are supplied by Render; Vercel remains frontend-only. GitHub CI
builds the same Dockerfile and smoke-checks the actual image. A successful image
build does not prove hosted Supabase/provider or complete MVP behavior.

- [Deployment HTML](../../.archify/architecture-linksifty-docker-20261014-005227/docker-deployment.html)
- [Editable JSON](../../.archify/architecture-linksifty-docker-20261014-005227/candidate.json)

Archify validation, delivery and strict artifact checks pass. Browser check is
skipped because Chrome/Chromium is unavailable; no visual QA is claimed.

## Optional source discovery and diagnostics

`main.py` additionally composes BraveSearch (existing HTTPX) and LangfuseTelemetry (official SDK at the infrastructure edge). The application only depends on SearchProvider and a scope/event Protocol. No new worker/broker or general agent framework.

An explicit unchecked Add checkbox discloses a short public-article query and the configured request charge. `/v1/capabilities` enables it only with a server key and positive verified plan rate. `/v1/items` carries `web_search`; a server-only transaction persists consent with the original item/job trial accounting. Pasted content remains outside search. Migration 000007 is required before activation.

The job first validates/acquires the primary source. Research reserves a separate provider-tagged amount under the same owner budget lock, sends one query, then checks at most 20 additional pages through the safe fetcher. Transient search responses/snippets are not evidence or stored. Normalized content hashes and host checks reduce duplicates; these heuristics do not prove independence. Bounded fetched passages and source identities are owner-scoped in job search_context and expire with the item. A confirmed search response settles at operator-configured plan price; uncertain outcomes remain reserved and are never automatically resent. Model retries reuse persisted research. Usage labels disclose actual OpenRouter cost versus plan-derived Brave charge.

The model receives primary/additional source texts, not a browsing tool. The model selects a supplied passage ID per criterion. The adapter derives the original source and exact text; application and SQL validate offsets against stored material. For v2, cross-source confirmation is not_verified without an external supporting citation; legacy v1 retains its minimum-score guard. Detail exposes checked-source URLs and unavailable/uncertain status. No claim of complete factual verification, official X integration or grounded chat.

Langfuse root/fetch/research/generation observations and discrete events capture the complete relevant analysis flow: stages, search/skip/fetch decisions, source passages, model messages and completion, citation validation, budget changes, persistence, heartbeat and recovery. Article/model content is included by default when existing LANGFUSE_ENABLED is enabled, per the owner’s revised decision. Trace fields are bounded and redacted; configured secrets, account identity, lease tokens and authentication headers are excluded. Exceptions are reduced to class names; telemetry errors neither repeat nor stop business work. This is best-effort observability, not a durable charge ledger. SDK shutdown is flushed outside the event loop. Langfuse defaults off; its access and retention are operator-managed independently of Supabase cleanup.

- [Brave/Langfuse workflow HTML](../../.agent/context/changes/processing-usage-inbox/brave-langfuse.html) · [editable JSON](../../.agent/context/changes/processing-usage-inbox/brave-langfuse.json). Repository-backed at local code commit c844819. Validate/deliver/strict artifact checks pass; automated browser check skipped because Chrome unavailable; no fresh perceptual inspection claimed. All diagram labels, explanations and viewer controls are in English. Latest workflow receipts are under brave-langfuse.content-tracing/; lifecycle English receipts remain under lifecycle.english/. Prior receipts are historical.

Submission/resume maintenance (000008): owner-profile lock serializes duplicate URL decisions before creating new items/jobs/trial usage; existing rows remain. UI preflight is advisory, server guard authoritative. The original citation-format repair has been superseded by passage-ID selection within the OpenRouter adapter; existing exact source/offset fences remain. These are guards within existing steps, with unchanged topology and no new external calls.

## Assessment calibration — local change, 2026-10-17

Migration 000010 adds rubric version compatibility, unscored criteria, nullable
aggregate scores and separately cited hype signals. Existing owner/lease/budget
RPC fences remain in place. New settings use the revised eight descriptions;
reserved jobs and saved results retain their snapshots. Default descriptions
upgrade by criterion ID while custom wording and all weights survive.

The provider receives source URL identities and the UTC analysis date as
untrusted metadata. It selects exact supplied passages for each explanation and
for up to three primary-source hype signals. Both application and SQL retain
exact source-offset checks. Pure scoring excludes unscored criteria and gates
valuable on four key criteria; hype depends on grounded signals, not a low sum.
The detail view presents statuses, coverage, verdict reasons and hype citations.

One opted-in Brave request asks for 20 candidates; research attempts at most 20
additional pages, with existing host/content deduplication and no implicit paid
retry. Stored comparison material is bounded to 12,000 characters per source
and 1.2 MB per research context. Provider input further apportions a conservative
UTF-8 budget across additional excerpts, preserving the entire primary text.
Oversized inputs fail before a paid model HTTP request with zero model cost;
no full-page or comprehensive verification is claimed.

- [Calibrated assessment workflow](../../.agent/context/changes/assessment-calibration/assessment-workflow.html)
  · [Editable diagram source](../../.agent/context/changes/assessment-calibration/assessment-workflow.json)
The diagram's validation, delivery and strict artifact checks pass; browser
inspection is skipped because Chrome/Chromium is unavailable. The editable
source pins an isolated working-tree evidence snapshot preserved in
`diagram-source.bundle`; it does not claim an uncommitted change exists at the
main repository's HEAD.

- [Canonical progress](../../.agent/context/changes/assessment-calibration/progress.md)

Coordinated database/backend/frontend rollout and live model calibration remain
external activation steps; local mocked tests cannot establish model agreement
on live articles.
