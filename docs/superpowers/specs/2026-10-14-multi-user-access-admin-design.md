# Multi-user access, account approval and cost controls

**Date:** 2026-10-14
**Status:** proposed for owner review
**Product decision:** restore the earlier multi-user approval model for the deployed Linksifty application. This specification supersedes the personal-only scope for this change.

## 1. Problem and context

The deployed frontend is still a prototype. It has no sign-in or session handling, calls authenticated API routes without a bearer token, and displays a Vite starter page title plus a stale local-preview label. Linksifty is now intended to accept additional users under account approval and per-user spending limits.

The previous product notes specify open signup, pending approval, three trial links, and a $10 monthly cost limit per user. The newer personal-MVP PRD deferred those features. The owner has now requested Google sign-in through Supabase, an admin panel, approval emails through Resend, per-user usage in USD, and admin-managed limits. The owner confirmed three trial links, approval email only, and a two-stage delivery.

## 2. Goals and non-goals

### Goals

- Let visitors create an account by signing in with Google through Supabase Auth.
- Require admin approval for regular use while allowing three pending-account trial link submissions.
- Give the owner an in-app account approval panel and initial admin access through server-side configuration.
- Send an approval email to the user through Resend after the approval has been committed.
- Measure real OpenRouter inference cost per user and enforce an admin-managed monthly budget atomically.
- Keep user content private from administrators and other users.
- Replace prototype browser labels with truthful Linksifty/session UI.

### Non-goals

- Email/password login, social providers other than Google, teams, user-to-user sharing, or admin access to another user's content.
- Charging users, collecting payment methods, or allocating shared hosting, database, or email-provider bills to individual accounts.
- Sending email for a pending signup or rejected account.
- Showing fabricated spend before model calls are metered.
- Making paid API credentials available to the browser.

## 3. Users and end-to-end flows

### Visitor and pending user

1. A visitor chooses **Continue with Google**.
2. Supabase Auth creates or restores the Google-backed session and redirects to the Linksifty callback.
3. The API verifies the bearer token with Supabase and provisions a server-controlled account record if this is a new identity.
4. A new non-admin account starts as `pending`. The user sees an awaiting-approval screen and the remaining trial allowance.
5. The user may submit up to three links in total while pending. The server accepts or rejects each batch atomically: if the batch exceeds the remaining allowance, no item is created and the trial counter is unchanged.
6. After the third accepted link, further submissions remain disabled until an admin changes the account status.

### Approved and rejected user

- An approved user can use their own account within the current monthly OpenRouter budget.
- A rejected user can sign in to see an access-denied state, but cannot access private items, submit links, use paid processing, or call account-only APIs.
- Repeating Google sign-in does not reset approval status or trial usage.
- Users can see their own current-month USD spend, outstanding reservation amount, and configured limit.

### Administrator

1. The configured initial administrator signs in through the same Google flow.
2. The admin panel lists accounts with email, creation time, access state, and pending trial usage. In the second delivery stage it also shows month-to-date cost, outstanding reservations, and the user's limit.
3. The administrator can approve or reject accounts and set a non-negative monthly USD limit per account. The default is $10.00.
4. Account management endpoints never read or return another user's links, notes, sources, assessments, citations, or chats. The administrator's own personal inbox remains available under the same owner-only rules.
5. On approval, the state change commits before Resend is called. A successful send is recorded. A failed send leaves the account approved, surfaces a delivery failure in the panel, and can be retried explicitly by the admin.

### Paid request and cost-limit flow

1. Before each paid OpenRouter request, the server atomically reserves a conservative upper-bound cost against that user and the current UTC calendar month.
2. If actual spend plus outstanding reservations would exceed the configured budget, the server rejects the request before making a paid provider call and returns a clear budget-limit response.
3. When OpenRouter returns usage and cost, the server records the actual USD amount and reconciles the reservation. The ledger stores no prompts or source text.
4. If the outcome or cost is unknown, the reservation remains counted until it can be reconciled; it is never silently released in a way that could permit overspending.
5. Reducing a budget below already-recorded spend or reservations does not erase history or cancel existing work; it blocks new paid reservations until the account is under the new limit.

## 4. Functional requirements

### Authentication and access

- **AR-01:** Google OAuth through Supabase is the only sign-in method. Request identity scopes only (`openid`, email, profile); no Gmail mailbox scopes.
- **AR-02:** Restore the Supabase session on page load, include its access token on API requests, and clear private UI data on sign-out or session expiration.
- **AR-03:** Persist account status on the server as `pending`, `approved`, or `rejected`. New regular accounts start pending. Repeated sign-in cannot reset state or counters.
- **AR-04:** Enforce account status in the API before any private-data read, link submission, or paid action. Hiding a button is not authorization.
- **AR-05:** The pending allowance is three accepted link submissions per account lifetime. The API checks and increments it atomically. A batch larger than the remaining allowance is rejected as a whole.
- **AR-06:** The initial administrator is identified by a server-only `LINKSIFTY_ADMIN_EMAIL` setting whose value is supplied privately during deployment. The API trusts only the verified Supabase identity returned by the Auth user endpoint; no user-editable metadata or frontend state grants admin access.
- **AR-07:** Admin endpoints are limited to account approval/rejection and budget management. Every content endpoint remains scoped to the authenticated owner's user ID, including for admins.

### Account administration and email

- **AR-08:** The admin panel lists account identity, account status, creation time, and pending-trial usage; cost fields are added in stage two.
- **AR-09:** Admins can approve or reject regular accounts. Decisions are enforced by the API and are visible to the affected user on their next authenticated page load.
- **AR-10:** Resend sends one approval confirmation to the affected user after an approval transition. It sends no signup notice or rejection notice.
- **AR-11:** Email failure does not roll back approval. The admin sees send status and can retry; repeated request handling must avoid accidental duplicate messages.
- **AR-12:** Resend failure details are safe, concise, and contain no credentials or user content.

### Usage and budgets

- **AR-13:** Every billable OpenRouter request is attributed to the authenticated user and recorded in a durable usage ledger in USD with enough precision to represent sub-cent calls.
- **AR-14:** The monthly budget is stored and enforced per account. The default is $10.00 per UTC calendar month. Admins may set a non-negative per-user amount, including zero.
- **AR-15:** Budget reservation is atomic across concurrent requests. A request cannot proceed unless its conservative reservation fits within actual month-to-date cost plus outstanding reservations.
- **AR-16:** Successful provider responses reconcile to provider-reported actual cost. Unknown outcomes remain reserved and visible until reconciled.
- **AR-17:** Users can view only their own current-month usage and limit. Admins can view the same cost summary for every account but no content.
- **AR-18:** Usage totals exclude shared Render, Vercel, Supabase and Resend costs; they represent OpenRouter inference only.
- **AR-19:** The UI distinguishes actual cost, outstanding reservations, configured limit, and remaining available amount. A limit error explains when the budget resets or that an admin may raise the limit.

### Deployed frontend identity

- **AR-20:** The browser document title is `Linksifty`.
- **AR-21:** Remove the static `LOCAL API PREVIEW` label. Show truthful signed-out, pending, approved, rejected, and admin states where applicable.
- **AR-22:** Login, waiting, denied, admin, empty, loading, error, and limit-reached states are usable by keyboard and screen readers and adapt to mobile widths.

## 5. Edge cases, errors and recovery

- Invalid or expired Supabase tokens return 401 and clear the prior user's data before returning to sign-in.
- Supabase Auth or account-profile storage outages fail closed for private and admin operations; the app explains that access could not be checked.
- Pending or rejected users cannot bypass restrictions by calling the API directly.
- A batch that exceeds remaining trial links is rejected without partial inserts or counter changes.
- An admin cannot approve or reject the initial admin account through ordinary user-management controls.
- A normal user calling an admin endpoint receives 403 without account data.
- A Resend timeout or rejection does not undo an approval; the admin can retry the approval notification from the panel.
- If a provider call fails before any billable request, its reservation may be released only when the result proves no spend occurred. If billable outcome is unknown, retain the reservation and surface it.
- If actual provider cost exceeds the conservative reservation, record the actual cost and block later calls until under budget; do not discard or cap the reported amount.
- If usage data is missing from a successful provider response, do not silently treat it as free. Retain the reservation and flag the request for reconciliation.
- If an administrator lowers a cap below current use, existing history remains intact and further paid requests are blocked.
- OAuth callback URLs and browser origin must be allowlisted for the production custom domain and local development.

## 6. Constraints

- Preserve Supabase RLS and explicit API owner predicates for all user content.
- Keep admin identity, account status, trial counts, and budgets in server-controlled state; never trust frontend claims or user-editable Supabase `user_metadata`.
- Keep Supabase secret/service-role, Resend, and OpenRouter keys server-only. The frontend may use only the Supabase publishable/legacy anon key protected by correct RLS and the API bearer session.
- FastAPI routes remain transport-only. Account, trial, and budget rules belong in application/database operations. Provider adapters remain at the infrastructure edge.
- Use exact decimal or integer sub-cent accounting; the existing whole-cent assessment field alone is not sufficient for a per-request ledger.
- All provider and email calls are mocked in automated tests; no real paid call or email is sent by tests.
- Keep the currently accepted 30-day retention rule for user content. Usage data contains no source content; retention and audit-history duration should be decided before deployment if the implementation needs a policy beyond current-month reporting.
- The free-tier hosting plan and the existing Google OAuth setup remain; production activation requires the user to configure provider credentials, sender-domain verification, and redirect URLs in Supabase, Resend, Render, Vercel and Cloudflare as documented.

## 7. Delivery stages and acceptance criteria

### Stage 1 — Google sign-in and account approval

- The production custom-domain login screen can start Google OAuth and restore a session.
- The initial owner account is recognized as admin through the private server configuration.
- New accounts start pending, see their status and trial balance, and can submit at most three accepted links; the fourth attempt is rejected by both UI and API.
- Admin can approve or reject accounts; normal users cannot reach admin actions; admins cannot access other users' content.
- Resend sends the approval confirmation after the database commit. A simulated failure keeps the approved state and offers an explicit retry.
- API requests include the Supabase session; sign-out and 401 clear prior account data.
- Browser title reads `Linksifty`; the local-preview label is absent.
- Documentation lists the new Vercel and Render environment variables and exact Supabase callback/origin setup without real secret values.

### Stage 2 — per-user USD usage and admin limits

- Each paid model call records an actual cost or an outstanding reservation for the correct user.
- Concurrent reservations cannot exceed the current UTC-month budget.
- New accounts default to $10.00; admin can change each user's cap, including to $0.
- Admin sees each user's actual monthly spend, reserved amount, limit, and remaining amount; a user sees only their own values.
- Budget exhaustion stops the paid provider call and produces an understandable UI/API state.
- Actual cost greater than reservation is recorded truthfully and blocks subsequent requests when the cap is exceeded.
- Tests cover month boundaries, repeated reconciliation, unknown outcomes, concurrency, ownership, admin authorization, and budget edits without real provider calls.

## 8. Risks, dependencies and open questions

- **Assessment pipeline dependency — implementation owner:** The backend currently persists jobs but does not execute them and has no OpenRouter adapter. Stage two must include or depend on the processing work needed to make real usage measurable; an empty ledger must not be presented as evidence of no spend.
- **Initial admin bootstrap — implementation owner:** The owner's verified email must be compared to private server configuration and the initial admin account must be usable even if its account profile is newly created.
- **Provider cost contract — implementation owner:** Verify the selected OpenRouter endpoint's cost fields and how to reconcile uncertain timeouts before coding the reservation contract.
- **Sender identity — Filip:** Choose a verified sender address/domain in Resend before production email can be delivered from Linksifty.
- **Email retry/idempotency — implementation owner:** Choose an idempotency key and persist enough delivery state to distinguish sent, failed, and retryable messages.
- **Rejected-account recovery — product owner:** Admin can later change a rejected account to approved; self-service appeal/re-registration is not included.
- **Cost retention — product owner:** The UI initially reports the current month. Decide before implementation whether to keep compact monthly totals beyond that month; no prompts/source content belong in the ledger.
- **Google OAuth activation — Filip:** Configure Google branding/audience/client, Supabase provider, Vercel callback/origin allowlist, and Render's production origin after the code and setup guide are ready.

## 9. Architecture decision and alternatives

The agreed delivery is staged. Stage one establishes verified identity, account status and administrator-only account actions. Stage two connects cost accounting to actual provider calls. This lets the owner test sign-in and approval before turning on paid work, while preserving the dependency that accurate spend cannot precede provider integration.

Account status and trial counters are server-controlled database state. The initial admin is derived from the verified Supabase user email and a private server-side allowlist value rather than user-editable metadata. Email delivery is an effect after the approval transaction and never controls the approval result.

Per-user cost is kept in a durable usage ledger rather than inferred only from completed assessments, because future model chat and retries may also incur cost. PostgreSQL performs atomic reservation and settlement so concurrent workers share one correct budget boundary. A dashboard-only view of OpenRouter usage was rejected because it cannot enforce the app's per-user limits.

## Sources and design approvals

- Prior product rules: `context/foundation/shape-notes.md`, access control and FR-001–FR-003.
- Current runtime facts: `frontend/index.html`, `frontend/src/App.tsx`, `backend/src/linksifty/api/auth.py`, `backend/src/linksifty/infrastructure/supabase_auth.py`, `backend/src/linksifty/infrastructure/supabase_repository.py`, `supabase/migrations/20261012_000001_personal_mvp.sql`.
- Supabase Google OAuth, authorization metadata and key safety: [Google login](https://supabase.com/docs/guides/auth/social-login/auth-google), [user data](https://supabase.com/docs/guides/auth/users), [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security), [API keys](https://supabase.com/docs/guides/getting-started/api-keys).
- OpenRouter usage: [OpenRouter support](https://openrouter.ai/support).
- Resend API and retries: [Python integration](https://resend.com/python), [async Python support](https://resend.com/changelog/python-sdk-async-support), [idempotency keys](https://resend.com/changelog/idempotency-keys).
- Owner approvals in conversation: two-stage delivery; three accepted trial links; Resend email after approval only; $10 monthly default and admin-adjustable per-user OpenRouter budget; USD tracking excludes shared infrastructure bills.
