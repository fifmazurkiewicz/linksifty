# Linksifty architecture

Updated 2026-10-14. The repository is a monorepo: `backend/` is the uv-managed FastAPI package, `frontend/` is React/TypeScript/Vite with npm. Root documentation and `uv.lock` are shared.

## Implemented request path

1. The browser starts Google OAuth through Supabase and restores its session. Every API request sends that session's access token. `api/auth.py` asks Supabase's authenticated user endpoint to validate it and returns the verified UUID and email. Missing/rejected tokens return 401; unavailable authentication returns 503.
2. FastAPI routes pass that UUID to `ItemService`. The service uses the application repository contract; concrete Supabase HTTP integration is wired in the entrypoint.
3. Every repository query includes an owner predicate. Submission calls the server-only `submit_fetch_items` transaction to insert item and job together before returning 202. List and detail routes are wired; read/delete repository methods still need routes.
4. `/v1/me` creates a pending profile for new users and reports the verified owner as admin only when `LINKSIFTY_ADMIN_EMAIL` matches. Pending users may submit three trial links; rejected users are blocked. The admin API returns account metadata only and never exposes another user's content. Approval mail is sent through Resend after the status transaction commits.
5. Explicit `LINKSIFTY_DEMO_MODE=true` enables sample responses. Demo responses carry `demo: true`; production defaults to false.

This path is verified using mocked HTTP and frontend tests; no hosted migration or RLS test has run.

## Planned processing path

A bounded runner atomically leases queued or expired work, obtains complete content, reserves model cost, validates structured criteria and citations, computes the pure verdict, and commits the final result under the lease token. A failed/partial acquisition stops at `awaiting_manual_content`. Later authenticated visits resume claimable jobs. This runner is not yet implemented.

C2.1 hardens the generic HTTP adapter: reject malformed/credential URLs, resolve and validate every DNS answer, then connect to a pinned public IP with the original Host and TLS SNI. A fresh client per fetch disables environment proxies and prevents inherited credentials/cookies or cross-host TLS pooling. Only tests inject a transport; the production path uses the standard HTTPX transport. The former borrowed-client signature had no production callers. Redirects remain disabled; safe redirect handling, streaming limits, extraction quality and completeness still need C2.2–C2.5. `AssessmentService` currently converts an injected draft into a scored result; it does not yet enforce completeness, citations or budget. OpenRouter/X/chat adapters remain planned.

## Data and trust

Supabase migrations define items, content, jobs, assessments, citations, chat and settings. RLS policies and expiry fields exist; cross-owner foreign keys, client write privileges, retry/lease safety, cleanup execution and database validation remain C1 work. An expiry timestamp does not perform deletion.

Provider credentials remain on the server. Application orchestration depends on contracts; deterministic scoring has no FastAPI/database/provider imports. All fetched/pasted/provider text is untrusted. Every operation, including future chat/read/delete endpoints, must preserve verified owner scope.

## Diagrams

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
