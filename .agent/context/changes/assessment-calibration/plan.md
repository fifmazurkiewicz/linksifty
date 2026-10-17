# Assessment calibration implementation plan

Goal: implement user-approved purpose-aware scoring and up to 20 additional source checks.
Architecture: extend existing pure domain and typed provider/persistence boundaries; no new services/dependencies. Retain old rubric IDs and versioned snapshots.
Spec: [Decisions](decisions.md), approved proposal in chat.

## Global constraints
Python 3.11+, strict types, Pydantic v2, uv; npm only frontend. Owner isolation, exact citation offsets, fail-closed acquisition and paid-call budget/recovery stay enforced. Historical results unchanged. All diagram text English.

## Review focus
- Empty/partial evaluations cannot become valuable by denominator shrinkage.
- Old reserved response recovers using v1, not today's settings.
- Hype cannot use a comparison-source quote or a missing quote.
- Twenty Unicode-heavy sources do not overflow supported model context.
- Settings migration preserves custom text and weights; frontend round-trips version and null scores.

## Tasks
- [x] T1 Domain/contracts: behavioral tests for government explainer N/A, unknown critical evidence, ungrounded low score, explicit hype, legacy score and malformed status/score. Add version, statuses, anchored rubric, pure scoring.
- [x] T2 Provider/service/search: mocked tests for source identities, status schema, hype grounding, missing corroboration, 20 candidates/attempts and prompt bound. Update adapters and orchestration with existing citation validation.
- [x] T3 Storage: forward migration for v2 settings, nullable total, hype evidence and 20 research sources; preserve v1 snapshots and owner/lease checks. Add pgTAP gates.
- [x] T4 UI: status/null/hype explanations and version-aware labels, settings help and 20-source consent. Frontend tests for legacy and v2 rendering and save round-trip.
- [x] T5 Verification/docs: backend tests, strict mypy, ruff lint/format, frontend tests/lint/build, agent-toolkit check, local SQL gate where available; deliberate-break scoring test. Update product/deployment/architecture/roadmap and derived boards; Archify source and HTML. Implementation review and dispositions.

Execution: native in this chat per user request to implement; no new approval gate for reversible implementation. No deployment or paid requests.
