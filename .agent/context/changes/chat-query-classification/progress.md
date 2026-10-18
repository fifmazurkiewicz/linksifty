# Chat query classification

2026-10-18 — Owner approved the bounded design and pinned
`typesafe/jev-1.13` through OpenRouter.

- Context and API research complete; Graft unavailable, focused source reads used.
- Implemented: Jev before answer/search; fixed off-topic/unsafe refusals;
  strict/uncertain-failure handling; per-owner budgeting and idempotency.
- Verified: 309 backend tests, strict mypy, Ruff lint/format; 65 frontend tests,
  lint/build; 39 chat SQL assertions, five chat concurrency checks; all 12 SQL
  suites and six existing concurrency checks. TDD red/green and deliberate
  bypass failure recorded in evidence.md.
- Documentation and English editable sequence/HTML complete. Source/artifact
  validation passes; diagram browser QA unavailable (no Chrome). Failed workflow
  layout candidate retained with diagnostics; the sequence is the delivered view.
- Final native implementation review complete: no actionable findings; approved
  for local handoff with the factual external-verification limits in evidence.md.
- Graft and agent-toolkit are unavailable; no tool installation was attempted.
- Cleanup found the temporary PostgreSQL directory already absent; a final
  loopback readiness check confirmed no server responding on port 55443.
- Hosted rollout requires migration 000015 before matching backend. No frontend
  contract change or new key is needed. Live Jev accuracy/threshold and Decisions
  generation lookup remain external acceptance, not claims of local tests.
- No paid calls, hosted migration or deployment authorized by this local change.
