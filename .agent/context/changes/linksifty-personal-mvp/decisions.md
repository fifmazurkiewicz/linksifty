# Decisions: Linksifty personal MVP

## D-001: Personal, domain-agnostic MVP

**Decision:** Build for Filip's single authenticated account first. Accept ordinary web links from any domain, with a dedicated X adapter. Defer public signup, account approval, trials, and admin operations.

**Why:** The main uncertainty is whether source-grounded value verdicts help clear Filip's backlog, not whether a multi-user product can be operated.

## D-002: Explicit source acquisition choice

**Decision:** The submission screen offers either fetch-link or paste-content mode. A failed or incomplete fetch produces a manual-content request, never an assessment.

**Why:** It allows manual use when the user already has the content while preserving the no-hallucination guardrail.

## D-003: Lightweight corroboration

**Decision:** Assessment may check up to five cited sources, rather than the original twenty.

**Why:** It retains corroboration as an input to value scoring while keeping processing cost and delay compatible with a personal free-tier MVP.

## D-004: No paid background worker

**Decision:** Persist jobs in Supabase and process them opportunistically from the Render-hosted API. A job interrupted by a Render sleep remains queued and resumes on the next application visit.

**Why:** Filip accepts the free-tier cold start and does not want to pay for an always-on background worker.

## D-005: Time-limited data retention

**Decision:** Stored item content, assessments, citations, and chat history expire automatically 30 days after creation. Filip can permanently delete an item sooner.

**Why:** Confirmed explicitly after the planning quiz; it limits retained personal data and avoids treating the MVP as a long-term archive.

## D-006: Explainable result and source-bounded chat

**Decision:** A completed item shows a note, eight criterion scores and rationales, a deterministic verdict, and source excerpts. Its chat is available in v1 and answers only from that item's saved source content and excerpts.

**Why:** The product must help Filip make a trustworthy reading decision rather than produce an opaque model judgment.

## D-007: No System One/Jev classifier in MVP

**Decision:** Do not add Jev or another System One decision-model provider to the MVP. Use OpenRouter only for structured evidence extraction, criterion rationales, and grounded chat; derive the final verdict with the existing deterministic scoring rule.

**Why:** The product already needs a generative model for explanation and chat. A separate classifier would add integration, evaluation, and cost complexity without removing that dependency. Reconsider it later as a shadow-mode experiment once enough user-labelled links exist.

## D-008: Monorepo and an early UX preview

**Decision:** Separate the codebase into `backend/` for the FastAPI/Python package and `frontend/` for React/Vite. Use npm only inside `frontend/`. Before persistence work, build an Inbox-first, responsive UX preview backed by explicitly labelled in-memory demo data.

**Why:** Filip wants to validate the visible product direction early while preserving independent Python and JavaScript dependency boundaries. The preview avoids pretending that unauthenticated or provider-backed behavior exists before it is implemented.


## D-009: Pin source acquisition to validated DNS answers

**Decision:** C2.1 validates every resolver answer and refuses the whole target if
any address is non-public. Use one approved numeric IP as the socket destination,
with original Host and TLS SNI. Each fetch owns a new client with environment
proxies disabled; tests inject a transport instead of a borrowed shared client.
Existing httpx and standard-library DNS/IP parsing suffice; add no dependency.

**Why:** A hostname check followed by normal resolution permits DNS rebinding.
Reusing an IP-keyed TLS pool for different hostnames risks cross-host certificate
reuse; shared clients can also carry credentials/cookies. The dedicated client
avoids both. This implements the already-approved acquisition boundary without
changing application/domain layers or deployment topology.

**Trade-offs:** Mixed DNS sets are refused conservatively; only the first approved
IP is attempted. Reserved, multicast, site-local and 6to4 addresses are rejected.
Reconsider address failover only with evidence of availability problems. C2.2
must validate every redirect and preserve the per-host connection isolation;
C2.3–C2.5 own body limits/extraction/completeness. No completed source or provider
assessment is claimed merely from this network-safety slice.

**Evidence:** 38 fetcher tests include mocked DNS, no-network HTTPX socket/TLS
checks, environment-proxy exclusion, and deliberate removal of pinning. See
`evidence.md`, C2.1.


## D-010: Google OAuth login through Supabase

**Decision (2026-10-14):** User requests sign-in with a Google/Gmail account.
Configure Google as a Supabase provider; C6.2 implements the sign-in/session
workflow. Request identity scopes only, with no Gmail mailbox access. Preserve
personal-account access: pre-create the confirmed user and keep signup disabled.

**Boundary:** Google Client ID/Secret live in Supabase provider settings. The API
still receives and verifies Supabase user tokens. This documentation change does
not implement frontend login or configure external provider permissions.

**Evidence:** Official Google/Supabase provider, callback and identity-linking
instructions are linked in docs/deployment/setup.md, section 3.4. Password staging
checks are retained only as an optional diagnostic path for configured users.


## D-011: Docker backend on Render

**Decision (2026-10-14):** User requests a Dockerfile to manage deployment after
Render's Docker runtime rejected the missing file. Root Dockerfile builds Python
3.11.16 + uv 0.12.17, locked non-editable production dependencies and non-root API
runtime. PORT is set by the host; secrets are runtime env only. Explicit COPY
and a deny-by-default Docker context exclude unrelated frontend/session/secrets.

**Trade-offs:** Tool/image versions now live in Dockerfile rather than Render's
Python settings. A single production stage keeps maintenance simple; no Compose,
container registry push, database container or paid worker. Vercel remains the
frontend host. The native-Python path remains documented as a fallback.

**Checks:** Local Docker/Podman unavailable. GitHub container job performs a real
build and checks PORT=8123, /health, unauthenticated 401 and UID 10001. Standard
backend checks pass locally; hosted smoke evidence must be recorded after push.
This is a partial C8.3 artifact, not completion of the MVP or live deployment.
