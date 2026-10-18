# Verified context and API facts — 2026-10-18

- ChatService currently claims a durable turn, runs the model decision, optionally
  searches once, validates passage IDs, and saves. ChatDraft cannot express refusal.
- Existing ChatParagraph permits zero citations and the frontend renders it safely.
- Migration 000013 has unique decision/search/answer slots; a new classification
  slot requires an additive migration and generation-recording support.
- OpenRouter Decisions uses POST /api/alpha/decisions with model/state/questions;
  choice answers carry type/choice/probabilities/confidence; usage.cost and id are
  returned separately. Provider routing preferences are supported.
- Jev 1.13 is text-only with a documented 32K context and $0.042/M input, free output.
  Keep each question within that bound; reserve both contexts conservatively.

Primary sources:
- https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request
- https://openrouter.ai/typesafe/jev-1.13
- https://docs.typesafe.ai/concepts/system-one

No live inference or secret access was used to establish these facts.
