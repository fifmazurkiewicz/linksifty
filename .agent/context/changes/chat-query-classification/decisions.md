# Decisions

- Extend the existing chat provider with a Jev classification operation. Keep
  orchestration in ChatService, HTTP at the edge, and concrete wiring unchanged.
- Use the pinned Decisions model, not OPENROUTER_MODEL (which remains the answer
  model). Reuse HTTPX and the existing server-only key; add no dependencies.
- One request asks scope (relevant/off_topic/unsafe, unsafe takes precedence) and
  refusal language (Polish/English fallback). Refusals are fixed application text,
  with no citations, research, or answer-generation call. Other languages receive
  the English fallback. Context includes saved analysis/topic and recent history.
- Reserve a unique classification slot in the shared ledger before calling Jev.
  Bound the entire request below 32K UTF-8 bytes and conservatively reserve two
  full 32K contexts at a provider-enforced $0.042/M input, zero output/request cap.
  Unknown costs remain reserved; preserve generation IDs for reconciliation.
- Require a valid, complete choice distribution and scope confidence >= 0.8.
  This is a provisional conservative routing threshold, not a measured accuracy
  guarantee. Provider/classification failures never fall back to answering.
- Add migration 000015; keep historical turns compatible. Deploy migration before
  matching backend. No frontend contract change is needed for uncited refusals.
- This is a bounded extension of the existing chat flow; the approved in-chat
  design is the plan. No separate implementation-plan document is created.
