# Analysis chat review decisions

## CHAT-001 — Chat RLS queried an inaccessible account table

- Finding: `implementation-review.md#chat-001`
- Severity: medium
- Impact: correctness; own-chat reads failed for browser role
- Decision: Fix now
- Owner: Codex
- Rationale: preserve the established owner/item RLS boundary; account checks remain in authenticated API and server RPCs.
- Status: verified
- Follow-up: plan task 3; SQL policy corrected.
- Evidence: `../evidence.md`, 33 SQL assertions including foreign invisibility and owner reads.

## CHAT-002 — Leading excerpts could omit relevant late content

- Finding: `implementation-review.md#chat-002`
- Severity: medium
- Impact: user answer quality and unnecessary research
- Decision: Fix now
- Owner: Codex
- Rationale: choose question-relevant exact passages across each source within the existing byte budget; retain source order for selected passages.
- Status: verified
- Follow-up: plan task 2; source and passage word-overlap selection.
- Evidence: `../evidence.md`, long-article anisotropy regression passes.

## CHAT-003 — Search-budget refusal must not reserve a final generation

- Finding: `implementation-review.md#chat-003`
- Severity: medium
- Impact: correctness and spend boundaries
- Decision: Fix now
- Owner: Codex
- Rationale: an unadmitted search has no durable search slot. Return an explicit evidence/budget gap without another paid call.
- Status: verified
- Follow-up: plan task 2; short-circuit on search budget refusal.
- Evidence: `../evidence.md`, budget refusal test verifies no search/second generation.

## CHAT-004 — Private chat responses need explicit cache policy

- Finding: `implementation-review.md#chat-004`
- Severity: low
- Impact: privacy
- Decision: Fix now
- Owner: Codex
- Rationale: chat transport should prevent browser/intermediary caching of private conversation data.
- Status: verified
- Follow-up: plan task 3; GET/POST set Cache-Control no-store.
- Evidence: `../evidence.md`, authenticated API test asserts no-store.
