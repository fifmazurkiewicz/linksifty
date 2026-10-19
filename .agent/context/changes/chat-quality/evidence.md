# Chat quality verification — 2026-10-19

## Red / green / deliberate break

- Initial selected regression run before implementation: 29 failed / 13 passed;
  missing chat_model setting/constructor, chat-specific estimate and language
  propagation were detected (autospec failures affected existing service tests).
- Added separate early-config rejection test: failed because classification ran
  before discovering the unsupported chat model. After the guard: 1 passed.
- Deliberate regression: temporarily changed only the chat HTTP payload model
  from _chat_model back to _model. The Sonnet/Polish/latest-question regression
  failed (1 failed, 12 deselected). Restored only that line in finally, preserving
  any independent edits; green run uses restored implementation.
- Full backend suite after restoration: **564 passed**, one existing
  Starlette/httpx deprecation warning, 7.61 seconds.
- Strict mypy: pass, 50 source files. Ruff check and format check: pass,
  132 files. git diff --check: pass.
- agent-toolkit check: unavailable, command not found. No installation attempted.
- Commands use uv from repository root and a writable UV_CACHE_DIR under
  /private/tmp; no new environment/dependency or lockfile edit.

## Protected behavior

Mocked HTTP tests verify Sonnet's exact model ID, 8192 combined token cap,
low-effort/excluded reasoning, JSON-schema provider requirement, $2/$10 ceilings,
zero request fee and no fallback. Its USD 2.08192 reservation is independent of
the unchanged assessment estimate. Unknown model IDs cannot make HTTP calls.
The early application guard prevents even paid classification under invalid
chat configuration. Existing rejection/malformed/truncated-response/cost tests
now run against both the legacy model and Sonnet, with one HTTP request only.

Startup/config tests verify the independent default/rollback and composition.
Application tests verify the classifier's Polish language reaches an answer
despite English context and that both pre/post-search payloads carry language.
The adapter test sends a Polish follow-up plus an earlier repetitive English
answer, verifies the exact latest question, language and focused prompt contract,
and parses a grounded Polish fixture. It also verifies Langfuse names Sonnet as
the model used. Existing citation, refusal, duplicate, budget and owner-scope
tests remain passing.

Prompt assertions and a provider fixture verify configuration and contracts;
they do not prove actual model language adherence, conversational quality or
comparison accuracy. Live paid evaluation was not performed. The historical
classification uncertainty gate stays unchanged and may still reject a turn
before the answer model. Backend deployment is required to activate the default;
no deployment or new push performed during this change.

## Review scope

Only chat configuration/contract/orchestration/adapter/tests and directly relevant
documentation changed. The working tree also contains concurrent admin and
partial-preview implementation, including shared main.py, openrouter_client.py,
README and docs; those changes were preserved and not claimed as this task's work.
No frontend changes by this task. No architectural topology or schema change;
existing diagrams use generic provider boundaries and need no topology update.
