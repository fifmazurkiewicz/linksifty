# Frame: Linksifty personal MVP

## Observed problem

Filip has a backlog of saved web links and lacks time to decide which deserve attention. A conventional summary is insufficient: the useful outcome is a source-grounded, explainable value verdict that helps prioritize reading.

## Intended outcome

Linksifty is a domain-agnostic personal web application. A signed-in user submits up to five ordinary web links or supplies pasted content, then receives a source-grounded note, an eight-criterion assessment, a deterministic score, and one verdict: **valuable**, **to review**, or **hype**. X is the sole specialized source adapter and uses the official X API through a server-side credential.

The app must make it clear when it cannot access enough content. Paywalls, login walls, script-only pages, PDFs, videos, newsletters, and incomplete fetches never receive a summary or assessment; the user sees the reason and can paste the content instead.

## Affected users

- **MVP user:** Filip only, using one normal Supabase account.
- **Future users:** explicitly out of scope for this MVP; there is no public signup, trial, admin approval, or multi-user product flow in the first release.

## Product decisions confirmed in planning quiz

- Submission offers a direct choice between fetching a link and pasting content.
- The inbox opens first, with Inbox, Add, and Settings as the three primary navigation destinations.
- A submission accepts up to five links in one large input; duplicate submissions ask what to do.
- Processing status is visible in the inbox. Default order is unread first, then higher score; verdict filtering is included, full-text search is deferred.
- Item detail contains the verdict, note, eight criteria with justifications, source excerpts, and source-bounded chat.
- Verdicts use text labels with supplementary color, never color alone. Destructive deletion requires confirmation and is permanent.
- Chat is included in v1, opened from the specific item's detail page, and may use only the item's saved content and source excerpts.
- Link assessment checks up to five cited sources when available.
- Every material claim in the note identifies the supporting source excerpt and its position in the saved content.
- Success is 20 real submitted links, each ending in either a result or a manual-content request, with at least 60% agreement with Filip's judgment.
- No explicit feedback control is needed in v1.
- Incomplete content never produces a result. Transient errors get one safe retry, then a visible status.
- Results and saved source content are automatically deleted after 30 days; Filip may permanently delete an item earlier.
- Paid processing is capped at 10 USD per month.

## Technical decisions confirmed in planning quiz

- Frontend: React, TypeScript, and Vite.
- Backend: FastAPI with Pydantic v2.
- Identity and persistence: Supabase Auth plus PostgreSQL with RLS, using its free plan.
- Normal web fetching: HTTP plus text extraction. JavaScript-only, paywalled, login-gated, unsupported, and incomplete pages route to pasted content.
- X fetching: dedicated official-API adapter; the credential is server-only.
- Model access: OpenRouter, server-only credential, returning schema-validated JSON.
- Deployment: Vercel for the static frontend; Render for the API.
- Verification: focused tests, strict mypy, ruff, formatting, and CI.
- Diagnostics: structured logs for errors and task status; no full analytics/APM platform in v1.

## Free-tier operating constraints

- Supabase free-plan projects may pause after low activity over roughly a week; restoring the project is acceptable for this personal MVP.
- Render free web services sleep after 15 minutes without inbound traffic and can take about a minute to wake. That cold start is accepted.
- No paid background worker will be used.
- Processing work is persisted as a task in Supabase and opportunistically run by the API after submission. If Render stops during a task, its persisted queued state is resumed on the next application visit. The UI must represent this truthfully as queued or processing; it must never imply a completed assessment.

## Constraints and non-negotiables

- Value scoring and verdict derivation remain pure and deterministic; provider, database, and FastAPI imports stay outside that domain code.
- All user data remains scoped to the authenticated user ID, even though v1 has one account.
- Failed or partial fetches must not create a note, score, verdict, or chat-ready assessment.
- External credentials remain server-only and are never committed.
- Remote and paid integrations are mocked in tests.
- The app must work on phone and desktop browsers, with semantic controls, keyboard access, visible focus, and accessible status/error states.

## Assumptions to validate during research

- A request-triggered, persisted-task model is sufficient for the expected processing time and user workflow on Render's free tier.
- The selected LLM can reliably return source excerpts with usable positions in extracted content.
- The official X API plan supplied by Filip supports the required post/thread retrieval within the monthly cost cap.

## Success criteria for this change

- The resulting product specification removes the old multi-user/admin/trial scope from the MVP and resolves its background-processing model.
- The implementation plan contains a testable route to the 20-link evaluation, not merely component scaffolding.
- The plan identifies every deployed component that must persist state across a Render sleep.
