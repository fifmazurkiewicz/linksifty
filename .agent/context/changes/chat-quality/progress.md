# Chat quality progress

2026-10-19: owner selected Claude Sonnet 5.5 for quality. Bounded scope: independent
chat model configuration/cost bound and direct, concise, language-aware answers.
frame.md records the observed failure; research.md records verified API constraints.

- [x] Inspect transcript, frontend/provider/service paths and published model details.
- [x] Resolve model preference with owner.
- [x] Write failing regression checks for model routing, budget and language/context.
- [x] Implement independent model selection and focused answer instructions.
- [x] Run available gates and review; toolkit unavailable, live quality unverified.

Existing concurrent admin and partial-preview edits must be preserved. Paid
quality evaluation, deployment and external publication remain separate actions.

Implemented: dedicated OPENROUTER_CHAT_MODEL default Sonnet 5.5, separate verified
chat full-context cost bound, low reasoning effort with 8192 combined output
tokens, explicit validated language through both reply steps, concise/direct
comparison and clarification instructions. Assessment model and Jev are unchanged.
Unknown chat configurations stop before classification; caps, owner isolation,
citations, one search, settlement and no retries stay enforced. gpt-4o-mini rollback
is supported. `.env.example`, README, setup and architecture docs are current.

Verified: 564 backend unit tests, strict mypy, Ruff lint/format and diff whitespace
checks pass. Deliberately routing chat back to the assessment model makes its
regression test fail, then restored source passes. `agent-toolkit check` unavailable
(command not found); Graft unavailable. No new dependency or migration. No frontend
changes by this task; concurrent partial-preview/admin edits preserved.

Limit: all provider calls were mocked. A correct request, prompt contract and
validated Polish fixture do not establish Sonnet's live quality. No paid call,
hosted config change, push or deployment performed. See evidence.md and review.
