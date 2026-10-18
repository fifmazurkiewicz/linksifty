# Analysis chat implementation plan

Goal: deliver the [approved conversational scope and design](../../../../docs/superpowers/specs/2026-10-18-analysis-chat-design.md) in this session. Execution: native, authorized by “finish task”. No new dependencies, provider calls, hosted migrations or deployments.

## Tasks

- [x] 1. Add failing service/API/provider behavioral tests for saved-context answers, exactly one search, duplicate request IDs, foreign/incomplete items, budget denial, and invalid evidence.
- [x] 2. Add typed chat contracts and application orchestration; reuse provider/fetch/search boundaries. Keep transport and concrete integrations at the edge.
- [x] 3. Add migration 000013 with owner-consistent turns, server-only begin/reserve/record/finish operations, unique call slots and deletion fences. Add Supabase adapter and SQL tests. Wire composition and authenticated GET/POST chat endpoints.
- [x] 4. Add accessible persisted chat UI in AssessmentDetail, question preservation, idempotency, pending recovery and evidence. Add frontend interaction tests.
- [x] 5. Verify relevant tests, full backend suite/strict mypy/Ruff, frontend tests/lint/build, SQL gate, agent-toolkit and Archify. Review implementation, update README/setup/architecture/roadmap and derived boards, record evidence.

## Review focus

Cross-owner references; refresh/duplicate requests during a paid call; interrupted or deleted turns; concurrent shared-budget reservations; malicious source/model content; unavailable or partial research; old analysis shapes; oversized context and long histories.

## Interfaces

ChatService.history(owner,item) and ask(owner,item,request_id,question) return typed history/turns. ChatStore owns durable owner-scoped claims and reservations; ChatProvider.reply returns a structured answer or a search query, preserving cost/generation metadata on invalid answers. Server alone controls whether search is allowed. Each answer paragraph references restored passage evidence. All provider/search/fetch calls are mocked in tests.

## Checks

`uv run --package linksifty pytest backend/tests`; `uv run --package linksifty mypy --strict backend/src`; `uv run --package linksifty ruff check .`; `uv run --package linksifty ruff format --check .`; frontend `npm test -- --run`, `npm run lint`, `npm run build`; disposable PostgreSQL gate; `agent-toolkit check`. Preserve unavailable-check evidence, no production-readiness claim.
