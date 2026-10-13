# Progress: Linksifty personal MVP

Updated 2026-10-14. **Status: coding in progress; MVP incomplete.** Canonical remaining work: [completion plan](../../../../docs/superpowers/plans/2026-10-13-linksifty-completion.md).

## Verified slices

| ID | Outcome | Scope of Done evidence |
| --- | --- | --- |
| D1 | Backend foundation | Health/config, domain rubric/scoring/threshold snapshot; local Python tests |
| D2 | UX/API preview | Frontend shell and API listing/submission; production build, not complete UI behavior |
| D3 | Auth/item persistence | Supabase server auth, owner predicates, transactional submission and real API list/detail; mock HTTP verified, database execution pending |

## Active completion cards

Jednostką wykonania jest 40 mniejszych zadań w completion plan. **C2.1 Done:** URL/DNS validation i przypięte połączenie HTTP/TLS, zweryfikowane mock DNS/socket. C8.1 pozostaje Done lokalnie (GitHub pending). C1.1 Blocked: brak lokalnego PostgreSQL do obowiązkowego testu SQL. Ready: C2.2, C3.1, C6.1; pozostałe 34 Planned. WIP = 0/1. Następne: C2.2 (bezpieczne przekierowania).

| Card | Status | Next evidence |
| --- | --- | --- |
| C1 Database integrity and retention | In progress | Composite ownership, server-only writes, retry-safe claims, cleanup and SQL tests |
| C2 Safe source acquisition | In progress | C2.1 URL/DNS Done; redirects/body/extraction/completeness remain |
| C3 Assessment/citations/budget | Ready | Provider schema, citation bounds, atomic reservation, incomplete-source rejection |
| C4 Durable execution | Planned | Lease fencing, restart/resume, atomic finalization |
| C5 Product API | Planned | Paste/duplicates/read/delete/settings and owner tests |
| C6 Authenticated frontend | Planned | Login, detail/recovery/filters/settings, behavior tests |
| C7 Grounded chat/X | Planned | Saved-evidence chat, official X, cited-source cap |
| C8 Release tooling | In progress | C8.1 CI Done locally; logging/deploy docs/full audit remain |
| E1 External activation | Blocked (live verification only) | Filip's Supabase/X/OpenRouter configuration and hosted acceptance |

## Login preference — 2026-10-14

Google OAuth through Supabase is the requested C6.2 login method. Setup instructions are in docs/deployment/setup.md, section 3.4. C6.2 remains Planned; no provider settings or login UI were activated.

## Docker deployment slice — 2026-10-14

User requested Docker packaging for the existing Render service. Dockerfile, deny-by-default context and CI container smoke are implemented; image validation is pending GitHub CI because no local Docker runtime is installed. C8.3/E1 remain incomplete. Native Python is now a fallback.

## Known gaps

Jobs are persisted but not executed by a runner. Retry rules and SQL claims need reconciliation. The fetcher validates all DNS answers and pins the actual connection with original Host/SNI. Redirect validation, streaming/content-size limits and complete extraction remain C2.2–C2.5. Assessment completeness, citation validation and budget enforcement are missing. RLS has not been tested in a database, child ownership constraints need hardening, and 30-day cleanup is not implemented. Frontend still lacks production sessions, detail/chat/paste/settings workflows.

## Verification

73 backend tests (38 fetcher/security cases), strict mypy and Ruff passed for C2.1 on 2026-10-13. Frontend lint/build and locked installs passed earlier for C8.1; no frontend changes in C2.1. C8.1 workflow YAML and failure propagation checks passed locally; GitHub execution is pending. No frontend behavior test runner exists yet (C6.1). See evidence.md. The agent-toolkit executable is missing, so its gate has not passed. Diagrams and boards are planning artifacts; their verification is recorded separately. No real provider calls, hosted migrations or deployments were performed.
