# Multi-user access, account approval and spend controls Implementation Plan

> **For agentic workers:** After owner approval, execute this plan task-by-task in the current session (native execution). Keep the change-local `progress.md`, `evidence.md` and derived Kanban current. Do not use subagents.

**Goal:** Add Supabase Google sign-in, pending-account approval and Resend notifications, then record and enforce real per-user OpenRouter spend limits.

**Architecture:** Supabase Auth supplies verified identities; a server-owned account profile stores approval and trial state, while account-admin endpoints expose no user content. The backend reserves and reconciles OpenRouter cost in PostgreSQL before/after paid calls, and the frontend displays only the signed-in user's or admin's authorized account summaries. Delivery is split into an independently usable identity/approval stage and a spend stage that depends on a complete source-safe assessment path.

**Tech Stack:** React 19, TypeScript, Vite, `@supabase/supabase-js`; FastAPI, Pydantic v2, HTTPX, Supabase Auth/PostgREST/PostgreSQL, OpenRouter HTTP API, Resend HTTP API; pytest, mypy, Ruff, frontend behavior tests and Vite build.

**Execution:** Code, mock-based validation, migrations, docs and local diagrams are automated. Filip's manual work is limited to supplying private deployment values, configuring Google OAuth/Supabase redirects, verifying a Resend sender identity, applying hosted migrations, and running live acceptance after the code is reviewed.

**Spec:** [2026-10-14-multi-user-access-admin-design.md](../specs/2026-10-14-multi-user-access-admin-design.md)

## Global Constraints

- **AR-01:** Google OAuth through Supabase is the only sign-in method. Request identity scopes only (`openid`, email, profile); no Gmail mailbox scopes.
- **AR-04:** Enforce account status in the API before any private-data read, link submission, or paid action. Hiding a button is not authorization.
- **AR-05:** The pending allowance is three accepted link submissions per account lifetime. The API checks and increments it atomically. A batch larger than the remaining allowance is rejected as a whole.
- **AR-07:** Admin endpoints are limited to account approval/rejection and budget management. Every content endpoint remains scoped to the authenticated owner's user ID, including for admins.
- **AR-10:** Resend sends one approval confirmation to the affected user after an approval transition. It sends no signup notice or rejection notice.
- **AR-13:** Every billable OpenRouter request is attributed to the authenticated user and recorded in a durable usage ledger in USD with enough precision to represent sub-cent calls.
- **AR-14:** The monthly budget is stored and enforced per account. The default is $10.00 per UTC calendar month. Admins may set a non-negative per-user amount, including zero.
- **AR-15:** Budget reservation is atomic across concurrent requests. A request cannot proceed unless its conservative reservation fits within actual month-to-date cost plus outstanding reservations.
- **AR-18:** Usage totals exclude shared Render, Vercel, Supabase and Resend costs; they represent OpenRouter inference only.
- Keep Supabase secret/service-role, Resend, and OpenRouter keys server-only; commit only example variable names and no real values.
- Scope every content operation to the authenticated owner's ID, including for administrators.
- Use `uv` for Python commands and npm only in `frontend/`; Python is 3.11+, FastAPI/Pydantic v2, strict mypy, and all Python functions have full annotations.
- HTTP routes contain transport concerns only; account and budget policy live in application/database operations. Value scoring stays deterministic and provider/database independent.
- A failed or partial fetch never creates an assessment; request pasted content instead.
- Mock every paid or remote integration in tests. Never make a real provider call or send an email from automated tests.

## Review Focus

- Concurrent pending submissions or reservations racing at the last remaining allowance: database transactions permit only the requests that fit; covered in Tasks 1 and 7.
- Expired, unverified, or wrong-account Supabase session during a user switch: clear private UI and return 401; covered in Tasks 2 and 5.
- An ordinary user guessing admin URLs or a user ID: return 403/404 without account or content leakage; covered in Tasks 3 and 5.
- Resend timeout after approval has committed: account stays approved, delivery is retryable without accidental duplicate sends; covered in Task 4.
- OpenRouter timeout or missing/over-reservation usage fields: keep an outstanding reservation and block unsafe further spend; covered in Tasks 7 and 8.

---

## File structure and ownership

- `backend/src/linksifty/api/auth.py` and `infrastructure/supabase_auth.py` authenticate a token and return a verified identity (UUID and verified email); neither reads editable user metadata for roles.
- `application/account_service.py` owns self-profile, account-state, trial and admin account use cases; `api/accounts.py` and `api/admin.py` translate HTTP inputs/outputs only.
- `infrastructure/supabase_repository.py` owns service-role REST calls with explicit owner predicates and calls transactional RPCs for trial submission, profile state and usage accounting.
- `infrastructure/resend_client.py` and `infrastructure/openrouter_client.py` own remote HTTP protocols; provider DTOs do not leak into domain rules.
- New Supabase migrations own account profiles, notification delivery state, per-call usage, UTC-month rollups/reservations and restricted RPC grants.
- `frontend/src/auth/` owns Supabase session lifecycle; `frontend/src/lib/api.ts` owns bearer-token API calls; `frontend/src/features/` owns login, account status, admin and usage views. Keep existing visual tokens in `App.css` and `index.css`.
- `frontend/tests/` verifies observable auth and account flows with mocked Supabase/API boundaries; backend tests remain in `backend/tests/unit/` and migration integration tests in `backend/tests/integration/`.
- `docs/deployment/setup.md` and `docs/deployment/supabase.md` document exact environment variable names and hosted dashboard setup; `.env.example` contains placeholders only.
- `.agent/context/changes/multi-user-access-admin/architecture.json` and `architecture.html` are editable and rendered architecture artifacts; `progress.md` and `evidence.md` remain canonical execution records.

## Stage 1 — Google sign-in and account approval

### Task 1: Account profile and atomic pending-trial database rules

**Files:**
- Create: `supabase/migrations/20261014_000003_account_approval.sql`
- Modify: `supabase/migrations/20261013_000002_submission_rpc.sql`
- Test: `supabase/tests/account_approval.test.sql`
- Test: `backend/tests/unit/test_supabase_repository.py`

**Interfaces:** `account_profiles(user_id uuid primary key references auth.users, status text, trial_links_used integer, created_at timestamptz, updated_at timestamptz)`; status values are `pending`, `approved`, `rejected`. The migration adds server-only profile creation/read/update helpers and updates `submit_fetch_items(p_user_id uuid, p_urls text[])` so it locks the profile, checks status and remaining trial allowance, inserts all item/job rows or none, and increments the counter only for accepted pending submissions. Approved/admin accounts are not trial-limited. Authenticated and anon roles cannot directly write approval or trial fields.

- [ ] **Step 1: Write failing SQL integration cases** for a new pending profile, exact three-link allowance, rejected fourth link, whole-batch rejection, parallel batches racing for the final allowance, approved account unrestricted submission, and anon/authenticated attempts to forge status/counter.
- [ ] **Step 2: Run `supabase test db`** against the local Supabase PostgreSQL fixture with rollback isolation and two distinct auth users. Confirm each fails for the missing migration behavior; if Supabase CLI/Docker is unavailable, record the exact missing runtime and still run repository contract tests.
- [x] **Step 3: Add the migration and update the submission RPC** with a row lock and transaction-level all-or-nothing behavior; revoke direct client grants and grant execution only to the server role.
- [x] **Step 4: Implement a failing-then-passing repository contract test** asserting the account status response and the exact RPC name/payload used for submission; ensure a 4xx rule violation maps distinctly from persistence outage.
- [ ] **Step 5: Run the SQL integration cases and focused repository tests.** Verify two concurrent submissions cannot both consume the same remaining trial slots and a rejected batch creates no rows or count increment.

### Task 2: Verified identity, account session contract and access enforcement

**Files:**
- Modify: `backend/src/linksifty/infrastructure/supabase_auth.py`
- Modify: `backend/src/linksifty/api/auth.py`
- Modify: `backend/src/linksifty/config.py`
- Modify: `backend/src/linksifty/main.py`
- Create: `backend/src/linksifty/application/account_service.py`
- Create: `backend/src/linksifty/application/account_contracts.py`
- Create: `backend/src/linksifty/api/accounts.py`
- Test: `backend/tests/unit/test_auth.py`
- Test: `backend/tests/unit/test_accounts_api.py`

**Interfaces:** `AuthenticatedIdentity(user_id: UUID, email: str, email_verified: bool)` is returned by `SupabaseAuthenticator.verify(token)`. `CurrentIdentity` is a FastAPI dependency; application methods take `user_id: UUID` and return typed account profile/status DTOs. `GET /v1/me` returns only the caller's identity, status, trial count, and role (`user` or `admin`). `LINKSIFTY_ADMIN_EMAIL` is normalized server configuration. A verified identity matching it receives admin role and approved access; all other first-seen identities are pending.

- [ ] **Step 1: Write failing auth tests** for missing/invalid token, verified Google identity, absent email, unverified email, case-insensitive initial-admin email match, and repeated sign-in preserving existing status/trial count. Assert frontend/user metadata cannot grant admin role.
- [x] **Step 2: Run focused auth tests** and confirm the current UUID-only verifier cannot satisfy the identity contract.
- [x] **Step 3: Extend Supabase verification** to validate the returned user id, email and verification timestamp; return `AuthenticatedIdentity`. Preserve fail-closed 401/503 behavior and keep server keys out of responses/logs.
- [x] **Step 4: Add profile bootstrap and `GET /v1/me`** through an application service and repository operation. Admin identity bypasses pending state without exposing other account content. Gate all existing private item routes on active account status before storage access; preserve owner UUID predicates.
- [ ] **Step 5: Add API tests** showing pending/rejected users cannot list/detail/private items or submit beyond the trial rule, approved users can use private APIs, and admin content queries still use only the admin's own UUID.
- [ ] **Step 6: Run `uv run --package linksifty pytest backend/tests/unit/test_auth.py backend/tests/unit/test_accounts_api.py -q`.**

### Task 3: Admin account review API and account-state actions

**Files:**
- Create: `backend/src/linksifty/api/admin.py`
- Modify: `backend/src/linksifty/application/account_service.py`
- Modify: `backend/src/linksifty/application/account_contracts.py`
- Modify: `backend/src/linksifty/infrastructure/supabase_repository.py`
- Modify: `backend/src/linksifty/config.py`
- Modify: `backend/src/linksifty/main.py` (admin routes and CORS methods)
- Test: `backend/tests/unit/test_admin_api.py`
- Test: `backend/tests/unit/test_supabase_repository.py`

**Interfaces:** `GET /v1/admin/accounts` returns account identity, status, created time and trial usage only. `PATCH /v1/admin/accounts/{user_id}` accepts only `{status: "approved" | "rejected"}`. Admin access is checked from `AuthenticatedIdentity` plus server config at every request, not from frontend state, user metadata, or a caller-supplied role. The initial admin cannot be changed through these account controls. No admin route selects or returns links, notes, assessments, citations or chats.

- [ ] **Step 1: Add failing API tests** for admin list, approve, reject, self-protection, non-admin 403, malformed UUID 404, invalid transition payload 422, and response schemas that contain no content fields.
- [ ] **Step 2: Run the admin tests** and confirm `/v1/admin/*` is currently absent.
- [x] **Step 3: Implement typed account repository methods** with `account_profiles` queries only and an atomic status update that returns the prior/new status needed for notification decisions.
- [x] **Step 4: Implement transport-only admin routes**, authorize every route from the verified server identity, and allow only required `PATCH`/`PUT` methods through the existing CORS policy. Keep content access predicates unchanged.
- [x] **Step 5: Run admin API and repository tests**, including owner-isolation checks with two users and a configured initial admin.

### Task 4: Resend approval email with durable status and safe retry

**Files:**
- Create: `supabase/migrations/20261014_000004_account_notifications.sql`
- Create: `backend/src/linksifty/infrastructure/resend_client.py`
- Modify: `backend/src/linksifty/application/account_service.py`
- Modify: `backend/src/linksifty/api/admin.py`
- Modify: `backend/src/linksifty/config.py`
- Modify: `backend/src/linksifty/main.py`
- Test: `backend/tests/unit/test_resend_client.py`
- Test: `backend/tests/unit/test_admin_api.py`

**Interfaces:** `ResendApprovalMailer.send_approval(user_email: str, idempotency_key: str) -> DeliveryResult`. Configuration uses server-only `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, and `FRONTEND_ORIGIN`. `account_notifications` records account id, approval event id, delivery state, provider message id, attempt timestamps and a sanitized failure code. Approval commits first; only a real transition to approved schedules the effect. `POST /v1/admin/accounts/{user_id}/approval-email/retry` explicitly retries a failed delivery.

- [x] **Step 1: Write failing mocked HTTP tests** for valid send, provider rejection, timeout, malformed response, safe idempotency key reuse, and redaction of recipient/provider details from public errors.
- [x] **Step 2: Write failing admin flow tests** proving approval persists when email fails, repeat approval does not send a duplicate, and explicit retry can resend only a failed notification.
- [x] **Step 3: Add notification migration and Resend HTTP adapter** using the existing `httpx.AsyncClient`; store no message body or credentials. Use a stable idempotency key tied to the approval transition.
- [x] **Step 4: Wire the post-commit notification effect** through the account application service, return approval state even on mail failure, and expose delivery status/retry action only to admin.
- [x] **Step 5: Run focused mail/admin tests.** Confirm no test performs network I/O and no secret or provider body appears in logs/responses.

### Task 5: Supabase login, account experience and admin frontend

**Files:**
- Modify: `frontend/package.json` and `frontend/package-lock.json`
- Modify: `frontend/index.html`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.css`
- Modify: `frontend/src/index.css`
- Create: `frontend/src/auth/supabase.ts`
- Create: `frontend/src/auth/AuthProvider.tsx`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/features/auth/LoginScreen.tsx`
- Create: `frontend/src/features/accounts/AccountStatusScreen.tsx`
- Create: `frontend/src/features/admin/AdminPanel.tsx`
- Create: `frontend/tests/auth-flow.test.tsx`
- Create: `frontend/vitest.config.ts`
- Modify: `docs/deployment/setup.md`
- Modify: `docs/deployment/supabase.md`
- Modify: `.env.example`

**Interfaces:** The frontend creates one Supabase browser client from `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`. `AuthProvider` restores/observes sessions and exposes `signInWithGoogle`, `signOut`, `session`, and loading/error state. `api.ts` attaches `session.access_token`, clears private state on 401, and calls `/v1/me`; it never reads a service key. UI states: signed out, loading, pending with remaining trial links, rejected, approved, admin. Admin panel lists/changes account state and shows mail delivery/retry status. Browser title is `Linksifty`; remove the static local-preview label and show an environment/API status only when it is truthful.

- [x] **Step 1: Add frontend behavior-test tooling and write failing tests** for Google sign-in request with identity-only scopes, session restoration, bearer token attachment, 401 data clearing, pending trial screen, rejected screen, admin-only view, approve/reject, failed-mail retry and keyboard-operable loading/error states.
- [x] **Step 2: Run `npm --prefix frontend test -- --run`** and confirm the requested test cases fail before implementation.
- [x] **Step 3: Add Supabase browser auth and API client**; restrict OAuth request to identity scopes, persist no extra profile secrets, and clear cached data whenever user id changes or session expires.
- [x] **Step 4: Build the login, account-status and admin screens** in the existing visual system. Keep regular item access owner-scoped through the bearer-authenticated API; guard admin controls in UI for clarity while relying on API authorization for security.
- [x] **Step 5: Set document title and truthful status copy;** remove `LOCAL API PREVIEW` and the hard-coded port-8000 failure message from the deployed experience.
- [x] **Step 6: Document Vercel variables (`VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`), Render variables (`LINKSIFTY_ADMIN_EMAIL`, Supabase server keys, `FRONTEND_ORIGIN`, Resend variables), Google provider setup, Supabase redirect URLs and allowed production/local origins.** Keep `.env.example` placeholders only and clearly distinguish browser-safe keys from server secrets.
- [x] **Step 7: Run frontend tests, `npm --prefix frontend run lint`, and `npm --prefix frontend run build`.** Verify production build has no server credentials and the UI fits mobile and keyboard navigation.

### Task 6: Stage 1 integration, architecture artifacts and deployment validation

**Files:**
- Modify: `.agent/context/changes/multi-user-access-admin/progress.md`
- Create: `.agent/context/changes/multi-user-access-admin/evidence.md`
- Create: `.agent/context/changes/multi-user-access-admin/architecture.json`
- Create: `.agent/context/changes/multi-user-access-admin/architecture.html`
- Modify: `docs/architecture/overview.md`
- Modify: `docs/roadmap.md`
- Modify: `docs/roadmap-kanban.html`

- [ ] **Step 1: Add an end-to-end mocked API/frontend test** for Google-authenticated identity → pending state → three accepted links → admin approval → Resend success/failure/retry → approved access, and verify admin cannot retrieve the other account's content.
- [ ] **Step 2: Run focused backend and frontend suites** plus the migration/RLS SQL tests from Tasks 1–5.
- [ ] **Step 3: Create and validate an Archify architecture JSON/HTML pair** showing verified browser session, API trust boundary, profile/admin state, item ownership and Resend post-commit effect. Cite committed source paths/lines only; label unimplemented stage-two components as planned. The local artifact passes schema, delivery and strict checks; committed-source evidence and browser review remain unavailable before this work is committed.
- [x] **Step 4: Update deployment and architecture docs** with validated artifact links and the exact stage-one setup checklist. Mark the changed product roadmap source first and then regenerate/verify its derived Kanban.
- [x] **Step 5: Run the full required repository checks** and record exact commands/results and any hosted-only limitations in `evidence.md` and `progress.md`. Local code checks pass; `agent-toolkit check` is unavailable.

## Stage 2 — Per-user USD usage and admin limits

### Task 7: Atomic USD reservation, settlement and monthly usage ledger

**Files:**
- Create: `supabase/migrations/20261014_000005_openrouter_usage_ledger.sql`
- Create: `backend/src/linksifty/application/usage_contracts.py`
- Create: `backend/src/linksifty/application/usage_service.py`
- Modify: `backend/src/linksifty/infrastructure/supabase_repository.py`
- Modify: `backend/src/linksifty/config.py`
- Test: `backend/tests/unit/test_usage_service.py`
- Test: `backend/tests/unit/test_supabase_repository.py`
- Test: `backend/tests/integration/test_usage_ledger_sql.py`

**Interfaces:** `reserve_usage(user_id: UUID, request_id: UUID, month_start: datetime, reserved_usd: Decimal) -> ReservationResult`; `settle_usage(request_id: UUID, actual_usd: Decimal) -> UsageRecord`; `retain_unknown_usage(request_id: UUID) -> None`; `usage_summary(user_id: UUID, month_start: datetime) -> UsageSummary`. The ledger stores exact provider-reported USD at micro-dollar-or-better precision, request id, UTC month, reserved/actual amounts, status, timestamps and provider/model identifiers only. An admin-set budget is non-negative and has cent precision (integer cents, including $0.00); provider costs/reservations have sub-cent precision. A Postgres RPC locks the user's budget row and atomically checks actual plus outstanding reservations against `settings.monthly_budget_cents` (default 1000 cents). Client roles cannot write or read the ledger directly.

- [ ] **Step 1: Write failing service and SQL tests** for $10 default, zero cap, sub-cent amount, month boundary UTC, concurrent reservations at cap, repeated settlement idempotency, actual cost exceeding reservation, lower-than-current cap, and retained ambiguous outcome.
- [ ] **Step 2: Run the focused tests** and confirm no usage-ledger/RPC implementation exists.
- [ ] **Step 3: Add ledger schema, grants and transaction RPCs** for reserve, settle, safe release only when no billable request occurred, unknown retention and owner/admin summary reads.
- [ ] **Step 4: Implement typed usage contracts/service and repository RPC calls** with `Decimal`; reject negative, NaN/infinite and malformed values before persistence.
- [ ] **Step 5: Run SQL concurrency and repository tests.** Prove overspend is blocked under parallel transactions and prior monthly history cannot be rewritten by a limit edit.

### Task 8: OpenRouter cost contract and bounded provider adapter

**Files:**
- Create: `backend/src/linksifty/infrastructure/openrouter_client.py`
- Create: `backend/src/linksifty/application/provider_contracts.py`
- Modify: `backend/src/linksifty/config.py`
- Test: `backend/tests/unit/test_openrouter_client.py`

**Interfaces:** `OpenRouterClient.create_assessment(source_text: str, *, request_id: UUID, max_cost_usd: Decimal) -> ProviderAssessmentResult`; result contains validated structured assessment data and a positive exact `actual_cost_usd: Decimal`. Adapter always requests provider usage/cost metadata, pins supported model/configuration server-side, applies timeouts and bounded response size, validates schema, and never logs prompt or source content. Before implementation, verify the current official OpenRouter response cost contract and record the endpoint/model assumptions in `research.md` and setup documentation.

- [ ] **Step 1: Verify the provider's current primary documentation** for the selected endpoint, cost field, token/usage inclusion option and failure/timeout behavior; add dated citations and a captured sanitized response fixture shape to `research.md` (no key or user content).
- [ ] **Step 2: Write failing mocked HTTP tests** for successful cost response, sub-cent cost, missing cost, invalid JSON/schema, provider 4xx/5xx, timeout after send, and oversized response.
- [ ] **Step 3: Implement the HTTP adapter** using the existing `httpx.AsyncClient`; ensure cost absence and unknown timeouts are explicit and cannot be treated as zero.
- [ ] **Step 4: Run provider tests with mock transports only** and assert authorization values are redacted and never included in error messages.

### Task 9: Source-safe assessment execution with budget reconciliation

**Files:**
- Create: `backend/src/linksifty/application/job_runner.py`
- Modify: `backend/src/linksifty/application/assessment_service.py`
- Modify: `backend/src/linksifty/domain/jobs.py`
- Modify: `backend/src/linksifty/infrastructure/http_fetcher.py`
- Modify: `backend/src/linksifty/infrastructure/supabase_repository.py`
- Modify: `backend/src/linksifty/main.py`
- Test: `backend/tests/unit/test_job_runner.py`
- Test: `backend/tests/unit/test_http_fetcher.py`
- Test: `backend/tests/unit/test_production_items_api.py`

**Interfaces:** `JobRunner.process_user_queue(user_id: UUID, *, max_jobs: int = 2) -> list[JobOutcome]`. It claims a bounded number of jobs with a lease token; obtains complete source text using the safe fetcher or returns `awaiting_manual_content`; reserves worst-case cost before OpenRouter; validates provider result and source evidence; settles actual cost; and writes assessment/item state only if the lease is current. A provider timeout or missing cost retains the reservation and produces an explicit reconciliation-needed outcome. Integrate rather than duplicate the accepted C2–C4 safe-fetch, lease and assessment contracts in `2026-10-13-linksifty-completion.md`.

- [ ] **Step 1: Write failing runner tests** for successful full flow, private/redirect fetch rejection, partial/paywall content requesting paste with no assessment/provider call, budget denial before provider call, claim lease fencing, bounded queue, successful actual-cost settlement, and ambiguous timeout retaining reservation.
- [ ] **Step 2: Run runner tests** and verify current code has no job execution entry point.
- [ ] **Step 3: Implement a typed runner** by composing existing job lease rules, safe fetcher, `AssessmentService`, OpenRouter adapter and `UsageService`; keep routes as triggers only.
- [ ] **Step 4: Add the minimal database writes** to atomically commit assessment, citations, item state and lease completion after provider success; reject stale lease writes.
- [ ] **Step 5: Run mocked end-to-end tests** proving failed/partial fetch never creates assessment, budget failure prevents the provider call, and each provider call has one durable user-attributed usage record/reservation.

### Task 10: User/admin usage APIs, caps and frontend views

**Files:**
- Modify: `backend/src/linksifty/api/admin.py`
- Modify: `backend/src/linksifty/api/accounts.py`
- Modify: `backend/src/linksifty/application/account_service.py`
- Modify: `backend/src/linksifty/application/usage_service.py`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/features/admin/AdminPanel.tsx`
- Create: `frontend/src/features/usage/UsageSummary.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/tests/auth-flow.test.tsx`
- Test: `backend/tests/unit/test_admin_api.py`
- Test: `backend/tests/unit/test_accounts_api.py`
- Modify: `docs/deployment/setup.md`

**Interfaces:** `GET /v1/me/usage` returns current UTC month actual cost, outstanding reservations, cap, remaining amount and reset time for the caller only. Admin account list adds those fields; `PUT /v1/admin/accounts/{user_id}/budget` accepts a finite non-negative USD amount with at most two decimal places and stores integer cents. A user can never request another user's usage. Budget exhaustion returns a stable 429 problem response before the provider call.

- [ ] **Step 1: Write failing API/frontend tests** for owner-only usage, admin aggregate visibility without content, zero and fractional budget edits, invalid negative/NaN/huge inputs, reducing below current spend, stable budget-exceeded state, UTC reset date and reserved-versus-actual display.
- [ ] **Step 2: Implement typed usage endpoints** and connect them to the existing account/admin access check and database summary RPC.
- [ ] **Step 3: Implement per-user cap editor and usage displays** with accessible units, clear loading/error states, zero-cap behavior, actual/reserved distinction and month reset date.
- [ ] **Step 4: Run focused backend/frontend tests** and verify budgets are checked server-side even when the UI editor or usage panel is bypassed.

### Task 11: Stage 2 integration, setup docs and full verification

**Files:**
- Modify: `.agent/context/changes/multi-user-access-admin/progress.md`
- Modify: `.agent/context/changes/multi-user-access-admin/evidence.md`
- Modify: `.agent/context/changes/multi-user-access-admin/architecture.json`
- Modify: `.agent/context/changes/multi-user-access-admin/architecture.html`
- Modify: `docs/architecture/overview.md`
- Modify: `docs/roadmap.md`
- Modify: `docs/roadmap-kanban.html`
- Modify: `docs/deployment/setup.md`
- Modify: `docs/deployment/supabase.md`

- [ ] **Step 1: Add one mocked end-to-end acceptance test** that submits a link as one user, reserves and settles OpenRouter spend, denies the next request at the cap, and proves a second user/admin cannot see the source content through usage/admin endpoints.
- [ ] **Step 2: Update the editable architecture pair** with the provider call, reservation/settlement flow, UTC accounting boundary and owner/admin data visibility; validate the HTML and source links with Archify.
- [ ] **Step 3: Complete setup documentation** for server-only `OPENROUTER_API_KEY`, model/cost configuration, migrations, Resend sender verification, admin bootstrap and all browser/server variables; keep values private and placeholders generic.
- [ ] **Step 4: Update canonical roadmap M8/M9 statuses and evidence first, then regenerate the roadmap and change Kanban boards.**
- [ ] **Step 5: Run all required checks:** `uv run --package linksifty pytest`, `uv run --package linksifty mypy --strict backend/src`, `uv run --package linksifty ruff check .`, `uv run --package linksifty ruff format --check .`, `npm --prefix frontend test -- --run`, `npm --prefix frontend run lint`, `npm --prefix frontend run build`, and `agent-toolkit check`.
- [ ] **Step 6: Record exact command results, SQL runtime availability, any hosted Supabase/Google/Resend/OpenRouter setup still required, and final limitations in `evidence.md` and `progress.md`.**

## Self-review and coverage

- AR-01–AR-12 map to Tasks 1–6; AR-13–AR-19 map to Tasks 7–11; AR-20–AR-22 map to Task 5. Security constraints, data ownership, error recovery and no-content admin views are exercised in the named focused and end-to-end tests.
- The five Review Focus conditions are assigned directly to the tasks that own their enforcement and tests.
- Stage 2 explicitly includes the missing safe source-to-assessment runner needed for real usage metering; it reuses and synchronizes with C2–C4 rather than claiming the ledger alone completes usage accounting.
- Initial admin address and service secrets remain deployment-only values; no real credential is written to source control.
- The open product decisions (cost-history retention and Resend sender domain/address) are deployment/configuration gates. The plan stores current-month ledger events durably but its user-facing summary is scoped to the UTC month; it does not add historical UI or delete billing records without a separate retention decision.
- No plan placeholders remain; exact app interfaces, migrations, API paths, tests and commands are specified above.
