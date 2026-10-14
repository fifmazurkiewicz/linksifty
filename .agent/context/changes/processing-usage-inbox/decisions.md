# Decisions

- Owner approved preparing the five-part scope on 2026-10-15. Written specification approval and implementation-plan approval remain pending.
- Reuse current API runtime and PostgreSQL persistence rather than add worker/broker services.
- Prefer authenticated SSE for durable progress, with snapshot recovery; confirm hosting behavior during technical research.
- Never infer free usage from unknown costs; keep reservations until reconciled.
- Protect budget from direct owner writes as well as non-admin API calls.
- Persist 40–100% threshold and snapshot at analysis start; preserve existing assessments.
- Keep the established English product language; Polish spec labels express behavior.
- Proposed cost ledger retention: 90 days except unresolved reservations. Owner accepts or changes it at written-spec review.
- No parallel plan or board exists before technical plan approval. This change refines M3–M5/M9, not a new milestone.
