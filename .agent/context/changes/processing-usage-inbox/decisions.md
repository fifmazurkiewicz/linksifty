# Decisions

- Owner approved preparing the five-part scope on 2026-10-15. Written specification approval and implementation-plan approval remain pending.
- Reuse current API runtime and PostgreSQL persistence rather than add worker/broker services.
- Prefer authenticated SSE for durable progress, with snapshot recovery; confirm hosting behavior during technical research.
- Never infer free usage from unknown costs; keep reservations until reconciled.
- Protect budget from direct owner writes as well as non-admin API calls.
- Persist 40–100% threshold and snapshot at analysis start; preserve existing assessments.
- Keep the established English product language; Polish spec labels express behavior.
- Owner set detailed cost ledger retention to 30 days on 2026-10-15, replacing the proposed 90 days. Current-month aggregate survives until UTC reset; unresolved reservations remain until reconciled so cleanup cannot reopen spent budget.
- No parallel plan or board exists before technical plan approval. This change refines M3–M5/M9, not a new milestone.

## Execution and pause

- Owner subsequently instructed “CODE this”: native execution began after scope approval and the 30-day correction; do not treat the older written-spec-review gate as still pending.
- Owner explicitly stopped work on 2026-10-15 and requested remaining/not-started tasks to be saved. Current phase is paused, not complete. Implementation remains uncommitted; `progress.md` is canonical and `tasks.md` is the resume checklist.

## Resumed execution — verified bounds and liveness

Owner resumed work on 2026-10-15. Replace the byte/token heuristic with a full-context upper bound for the verified `openai/gpt-4o-mini` model (128,000 prompt-token ceiling plus 4,096 output tokens, at enforced $1/$5 per-million caps). Reserve $0.14848, then settle the actual cost; an unverified model fails closed. This intentionally reserves more than the typical call and removes tokenizer/framing assumptions without a new dependency.

Add a 15-second worker heartbeat and a 60-second fenced lease. Persist liveness independently of stage; list snapshots expose whether the last heartbeat is fresh (45 seconds). UI must display paused/interrupted work instead of claiming that a stale stage is running. Existing paid-attempt reservations remain authoritative after lease loss.

## Approved Brave/Langfuse extension

Owner approved both scopes and requested implementation/docs/diagrams/main push. See brave-langfuse-plan.md. Brave chosen because it was the discussed engine; HTTPX reused, no search framework or broker. Official Langfuse SDK added through uv with <6 major bound. Metadata-only explicit spans preserve content isolation. Shared monetary cap includes search charges at a configured plan rate, clearly distinct from actual OpenRouter cost. External search requires an informed per-submission checkbox; disabled without key/rate. No server-key entry in UI or committed secret. Native SHA256/owner/lease fences preserved.

## Duplicate blocking and citation repair — 2026-10-16

Owner requests blocking repeated link analysis and checking invalid-citation failure. This is bounded maintenance of existing submission/resume and validation paths. The explicit hard-block request supersedes the historical duplicate-choice proposal: no hidden force/reanalysis path is added. Reject the whole batch before creating items/jobs/trial usage when one normalized URL repeats within batch or exists for the owner before expiry. Normalize fragment, scheme/host case, default port and empty root path only; preserve path case and query semantics. Serialize submission/resume under existing owner profile lock; retain legacy duplicates, charges, content and reservations. Legacy duplicate resumes are blocked if a matching other item is queued/processing/completed; failed items remain explicitly retryable when no such item exists.

For citations, preserve exact-source evidence. Accept only whitespace-equivalent variants by resolving back to the exact original stored substring before calculating offsets. Never fuzzy-match, alter words/case, borrow another source or accept fabricated text. Report unknown source IDs separately. This addresses a reproduced failure category; the precise hosted provider response has not been inspected or proven to be a whitespace case. No paid automatic retries.

## Complete relevant Langfuse traces — 2026-10-16

Owner requested all relevant logs after the content-export distinction was explained, declining a separate content-debug toggle. This supersedes the metadata-only observability decision: when existing LANGFUSE_ENABLED is true, record processing events and bounded, redacted model inputs/outputs, source passages and search diagnostics. Never export credentials, authentication headers, account identity or lease tokens. Keep failure isolation, no provider retries and existing business/retention rules. Scope is the analysis pipeline; no blanket HTTP/database logging. Historical traces cannot be backfilled. Langfuse retention/access is operator-managed separately from Supabase's 30-day cleanup.
