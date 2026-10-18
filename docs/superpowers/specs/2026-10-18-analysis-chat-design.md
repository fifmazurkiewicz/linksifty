# Analysis and topic chat

## Intent and scope

The user can discuss a completed analysis and investigate its topic. They explicitly require search only when necessary and at most one search per question. The owner instructed the agent to finish the task on 2026-10-18. Delivery uses native execution in this chat. Product code uses Python 3.11+, FastAPI/Pydantic v2, strict types, uv, and the existing React interface and npm dependencies.

## User experience

Add a Chat about this analysis section below the result. Load its saved conversation. The user enters a question and sends it with a button or Ctrl/Cmd+Enter. Disclose that answering uses the existing AI budget and may send a short public-topic query to Brave when evidence is missing. The send action consents to that bounded operation. Show pending, failed, insufficient-evidence, and completed states. Preserve a question after a failed request; do not silently repeat paid work. Use safe plain-text rendering, accessible labels/statuses and responsive layout.

## Answering and sources

Use the stored assessment (including its original rules), original source, saved research, recent conversation and sources from previous chat turns. Existing answers are conversational context, never independent evidence. The model must answer from supplied passages or request exactly one targeted search if fresh/external evidence is necessary. Every substantive answer paragraph selects real passage IDs. The application restores exact text and URLs; unknown IDs fail closed. An insufficient-evidence answer explains the gap without invented facts.

If research is requested and configured, reserve its charge, issue one Brave request, and safely fetch up to 20 returned URLs with bounded concurrency/time/content. Deduplicate URLs and content. Search snippets, failed fetches and incomplete pages are never evidence. Persist successful bounded sources for follow-ups. Run one final generation with search disabled. There is no recursive search, pagination, query rewrite or automatic paid retry. If search fails, is unavailable, or finds no readable evidence, answer only what existing evidence supports and disclose the limitation.

## State, costs and trust

Each question carries a client-generated request UUID, reused after network uncertainty. Atomically create/claim a durable turn under owner/item scope; duplicate submissions return its stored state and do not execute again. Allow one active turn per item. Interrupted turns expire to an explicit failure; uncertain charges remain reserved. Model decision, model final answer and search each have a distinct unique reservation slot per turn, admitted under the existing per-user settings lock and shared monthly ledger. Persist generation IDs before cost reconciliation. Explicit non-inference rejection can settle zero; unknown outcomes must not. Provider calls have fixed timeouts and no implicit retry. Deletion fences subsequent source/answer writes and cascades all turn content; billing metadata can still settle.

Authenticated owner scope applies to all reads and writes, including administrators. Require an unexpired completed item with saved supporting source content. Source text, questions, model output and stored conversation cannot override system grounding/security rules. New tables use RLS, composite ownership references and server-only mutation privileges. Credentials stay server-only. No live provider call or hosted migration is part of local verification.

## Acceptance

1. Completed analysis exposes saved chat, keyboard submission and passage evidence.
2. A saved-context answer makes zero searches; research makes exactly one, even after duplicate requests or timeout.
3. Follow-up questions receive previous conversation and saved research; additional-source claims cite fetched passages.
4. Missing/foreign/expired/incomplete items cannot start chat or expose history.
5. Shared budget exhaustion prevents the relevant paid call; actual costs settle idempotently and uncertain costs remain reserved.
6. Fabricated citations and invalid/truncated provider output cannot become a successful answer.
7. A failed request preserves the question; duplicate sends, unmount and account changes cannot leak state or trigger another paid attempt.
8. Item deletion/expiry removes chat content and fences late writes while retaining charge accounting.

## Verification and rollout

Mock all remote services in unit/API/frontend checks. Run local PostgreSQL ownership, uniqueness, reservation, deletion and RLS checks when the disposable runtime is available. Run backend tests, strict mypy, Ruff lint/format, frontend tests/lint/build and agent-toolkit check. Produce editable English workflow JSON and HTML with Archify; record unavailable gates honestly. Deploy migration 000013 with matching backend/frontend; existing OpenRouter and optional Brave configuration is reused. Hosted activation and paid acceptance remain operator actions.
