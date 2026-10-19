# Chat quality implementation review

Outcome: approve local implementation with the stated deployment/quality limits.
No actionable findings remain; no finding disposition or derived board needed.

The owner selected Sonnet 5.5 after being shown its $2/$10 per-million token
prices. The pinned default is isolated to chat; the adapter retains assessment
and classifier paths. Known model bounds use full context and enforced provider
prices, with combined reasoning/output capped. Invalid chat configuration fails
before any provider request. Budget settlement, unknown-cost retention, citations,
user scope, search cap and idempotency retain their established protections.

The language signal is server-derived and forwarded through both generation
steps. Prompt changes target the observed summary repetition, wrong language
and missed comparison intent; ambiguity handling asks for clarification while
retaining evidence requirements. These remain model instructions, not guaranteed
semantic validation. No automatic provider fallback or confidence bypass added.

Tests cover routing, startup, price/reservation separation, rollback, unsupported
models, explicit language with English history, post-search language, failure
costs, one-request behavior and Langfuse model identity. A deliberate wrong-model
change turns the regression test red. Available backend/type/lint/format gates
pass. Toolkit and Graft are unavailable. No real credentials were read and all
model calls were mocked; no hosted activation or comparative quality result is
claimed. Deployment documentation explains the $2.08192 temporary reservation,
rollback and required live acceptance. No frontend, dependency, migration or
architectural topology change was needed. Unrelated active workspace edits remain.
