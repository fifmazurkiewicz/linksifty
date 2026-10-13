# Linksifty personal MVP — technical design

**Status:** proposed for review  
**Date:** 2026-10-11  
**Product contract:** [PRD](../../../context/foundation/prd.md)  
**Roadmap:** [canonical roadmap](../../roadmap.md)

## 1. Purpose and boundaries

Linksifty is a private, domain-agnostic inbox for deciding whether a submitted link is worth attention. A single authenticated user submits up to five URLs or pasted texts, receives an evidence-backed assessment, and can ask follow-up questions grounded only in the stored source material and cited references.

The product produces `valuable`, `to_review`, or `hype`; it does not claim to be a universal fact-checker. It does not create an assessment from incomplete or inaccessible source content.

MVP excludes public signup, teams, administration over another user's content, scheduled crawling, browser extensions, notifications, any paid always-on worker, and System One/Jev classification.

## 2. System shape

```text
React/Vite client (Vercel)
        │ authenticated requests
        ▼
FastAPI (Render Free) ── server-only adapters ── generic HTTP / X API / OpenRouter
        │
        ▼
Supabase Auth + PostgreSQL + RLS
```

The FastAPI entrypoint wires concrete integrations. Routes do transport work only. Application services orchestrate submission, task execution, assessment, and chat. Pure domain code performs completeness decisions, scoring, and verdict derivation without FastAPI, Supabase, or provider imports.

The full editable diagrams are the [architecture source](../../../.archify/architecture-linksifty-personal-mvp-20261011-194418/candidate.json) and [task lifecycle source](../../../.archify/lifecycle-linksifty-task-20261011-194418/candidate.json).

## 3. Primary user flow

1. The user opens **Inbox** and selects **Add**.
2. They paste one to five URLs into one input area and select the source mode for each: `fetch` or `paste content`.
3. The API validates the authenticated owner, batch size, URL/content shape, duplicate choice, and monthly 10 USD provider budget. It persists every accepted item and its work job before responding.
4. While the API process is awake, it claims a small number of persisted queued jobs. A generic URL is fetched and extracted; X uses its dedicated official adapter. Pasted content bypasses fetching.
5. If content is blocked, paid, partial, unsupported, or otherwise insufficient, the item becomes `awaiting_manual_content`. The detail view asks for pasted text and no assessment exists.
6. Complete content is assessed, citations are stored, the deterministic score and verdict are produced, and the item becomes `completed`.
7. The inbox sorts unread items before score and supports verdict filtering. The detail view shows the short note, eight criteria, citations, and grounded chat.

## 4. Durable processing without a worker

Jobs must survive Render Free idling or restarts. The database is the queue authority; a running worker process is not required.

| State | Meaning | Next states |
| --- | --- | --- |
| `queued` | Persisted and waiting to be claimed | `processing`, `failed` |
| `processing` | Leased by one API process | `completed`, `awaiting_manual_content`, `queued`, `failed` |
| `awaiting_manual_content` | Source cannot be assessed without user text | `queued` after pasted text, `failed` after explicit terminal error |
| `completed` | Assessment, citations, and threshold snapshot exist | terminal |
| `failed` | Retry allowance has been exhausted or request is invalid | terminal |

The claim is atomic and records a lease expiry. A later request may reclaim only an expired lease, preventing a sleep/restart from losing work. One transient retry is permitted. On an authenticated API request, the application may drain a tightly bounded number of jobs after sending the response or through its in-process task facility. The UI must never promise immediate completion: it shows the persisted state and refreshes while the user is present.

No task is executed until its owning user can be identified. All job reads and writes are ownership-scoped even though this MVP has one intended user.

## 5. Data model

Each table has an immutable primary key, creation timestamp, `user_id`, and an expiry timestamp where it holds personal content. Foreign keys use cascade deletion from the parent item.

| Entity | Essential fields | Notes |
| --- | --- | --- |
| `settings` | `user_id`, `verdict_threshold`, budget settings | One row per user. Threshold changes apply only to future assessments. |
| `items` | `user_id`, original/canonical URL, source kind, input mode, status, title, unread/read timestamps, expires at | An item is the user-visible unit. |
| `source_contents` | `item_id`, acquisition method, normalized content, content hash, fetched timestamp | Written only when complete enough to assess or retained pasted text. |
| `jobs` | `item_id`, status, attempts, lease token/expiry, error code, queued timestamp | Durable execution state; one active job per item. |
| `assessments` | `item_id`, short note, criteria JSON, score, verdict, threshold snapshot, model metadata/cost | Created only from complete source content. |
| `citations` | `assessment_id`, claim/criterion reference, URL, excerpt, start/end position | Supports auditable assessment and chat answers. |
| `chat_messages` | `item_id`, role, content, citation references | The assistant may cite only the item content and stored citations. |

Provider secrets and raw access credentials are never fields in these records. Provider cost and model metadata are stored only to make the monthly budget enforceable and explain results.

## 6. Assessment contract

The assessment adapter returns strict Pydantic-validated JSON. It includes a concise note, eight named criteria with rationale and score, claim-level citations, and no unsupported free-form verdict. Domain code computes the weighted total and verdict deterministically from this validated structure.

The eight criteria and weights come from the PRD. `assessment.threshold_snapshot` stores the exact active threshold at completion. Reopening or changing Settings must not recompute historic verdicts.

Up to five relevant external sources may be checked when a claim needs corroboration. Each cited external source stores an excerpt and position. If no sufficient evidence is available, the criterion must say so rather than invent certainty.

## 7. Adapters and failure handling

| Adapter | Responsibility | Failure behavior |
| --- | --- | --- |
| Generic web adapter | Fetch, extract readable source text, detect access/content completeness | Stop at `awaiting_manual_content`; do not call assessment. |
| X adapter | Retrieve X content using the user's future official API credential | Same fallback; no generic scraping workaround. |
| OpenRouter adapter | Structured assessment, source checking, and grounded chat | Validate JSON; count cost; permit one transient retry. |
| Supabase repository | Authenticated persistence, RLS-compatible access, transactional state transitions | Return explicit application errors; never widen user access. |

A blocked or paywalled source is a normal product state, not a silent failure. The item clearly names the required action: paste the relevant content. A malformed batch reports per-item validation errors and preserves valid, accepted entries where that can be done without ambiguity.

## 8. Security, privacy, and retention

Supabase RLS covers every table containing user data. API services additionally scope every query by the authenticated user ID; administrators must not bypass that content boundary. The browser receives no Supabase service-role key, OpenRouter key, or X credential.

Links, fetched data, pasted text, LLM output, and provider responses are untrusted. Validate them at every boundary, constrain outbound fetches to safe URL schemes and SSRF protections, log no source text or secrets, and escape all rendered content.

Explicit deletion cascades to content, task, assessment, citations, and chat. A scheduled-or-opportunistic cleanup removes expired records after 30 days. Expiry is visible in the product privacy copy.

## 9. UI contract

- **Inbox:** default route; shows unread first then score, status, supplemental verdict color plus text, verdict filter, and item deletion with confirmation.
- **Add:** one large batch input, per-link `fetch` / `paste content` choice, max-five guidance, individual validation errors, and clear submit progress.
- **Item detail:** status and recovery actions; then completed note, verdict, score, eight criteria, and citations; chat is available only when supporting content exists.
- **Settings:** account session, the threshold for future assessments, 10 USD budget status, and the 30-day retention policy.

Every status has text in addition to color. Controls are keyboard accessible, have accessible names and focus states, and preserve useful loading, empty, error, and disabled states.

## 10. Observability and validation

Structured logs correlate request, item, and job IDs without source body content. Essential counters are jobs by status, fetch-to-manual-content fallbacks, provider failures/retries, assessment cost, and budget rejections.

The implementation must include unit tests for URL/content policy, scoring, verdict thresholds, historic threshold snapshots, lease/retry transitions, access scoping, and no-assessment-on-incomplete-content. Adapter and provider calls are mocked. The release gate includes a 20-link evaluation with at least 60% acceptable verdicts, plus `uv run mypy src`, Ruff check/format, relevant tests, and `agent-toolkit check`.

## 11. External decisions still required

- The X API tier and credential availability before the adapter can be activated.
- The selected OpenRouter model and concrete per-request cost assumptions within the 10 USD monthly cap.

These decisions affect configuration and rollout, not the domain contracts above.
