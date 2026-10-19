# Verified chat facts — 2026-10-19

Graft unavailable; focused source/document reads used.

## Repository

- main.py shares one OpenRouterClient between ProcessingService and ChatService.
- config.py defaults OPENROUTER_MODEL to openai/gpt-4o-mini. Its estimate() rejects
  unknown models and reserves the full verified context plus output under caps.
- reply() uses structured ChatDraft output, at most 110K serialized request bytes,
  4096 output tokens, no provider fallback and $1/$5 per million token caps.
- The current prompt says latest question and user language, but English history
  and a full saved analysis appear together in a single JSON user message.
- Classification provides validated pl/en language; relevant answer payloads do
  not carry that explicit result. The service reconstructs payload after research.
- Frontend AnalysisChat submits the current question with a UUID and renders
  turn.answer; no replacement with the saved article summary was found.

## External primary sources checked today

- https://openrouter.ai/anthropic/claude-sonnet-5.5 — pinned ID
  anthropic/claude-sonnet-5.5, 1,000,000-token context, standard $2/M input and
  $10/M output, JSON schema response_format supported.
- https://openrouter.ai/docs/cookbook/evaluate-and-optimize/model-migrations/claude-5-5
  — Sonnet 5.5 mandatory adaptive thinking; no effort defaults high. Use explicit
  low effort for responsiveness. Disabling thinking fails. Reasoning token budget
  settings are not forwarded; effort is the supported control.
- https://openrouter.ai/docs/guides/best-practices/reasoning-tokens — thinking and
  visible output share max_tokens and are billed as output. Too-small budgets can
  return length with no visible answer; no automatic resend is appropriate.
- https://openrouter.ai/docs/guides/routing/provider-selection — max_price filters
  provider prices (USD per million tokens) and can fail closed; request cap supported.

Alternatives considered: prompt-only fix; newer budget model (GPT-6 Luna, owner
declined); Sonnet 5.5 (owner selected). No comparative live quality evidence exists.
Prices/capabilities are current published facts, not a guarantee of an available
provider or actual response quality.

Implementation decision: dedicated OPENROUTER_CHAT_MODEL defaults to selected
Sonnet; the existing adapter keeps separate analysis/chat model fields and bounded
chat estimation. Preserve legacy gpt-4o-mini as an explicit rollback. Reuse the
full-context reservation strategy rather than invent a tokenizer estimate. Sonnet
gets 8192 combined thinking/output tokens at low effort and $2/$10 caps, reserving
USD 2.08192 per answer call. Known actual cost settles as before. The conservative
reservation can deny a call with less available budget even when actual usage
would cost less. No automatic fallback or change to classifier cutoff.
