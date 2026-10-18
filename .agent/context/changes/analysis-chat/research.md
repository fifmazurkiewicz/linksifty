# Repository facts — 2026-10-18

- `frontend/src/features/queue/AssessmentDetail.tsx` displays the completed assessment and expandable evidence, but has no chat.
- `ProcessingRepository.assessment` loads owner-filtered analysis, citations and saved research identities. Job `search_context` retains fetched research excerpts.
- `BraveSearch.search` makes one request for up to 20 URLs; no retry. Search snippets are not evidence.
- `fetch_public_text` validates public URLs/redirects and content completeness.
- `OpenRouterClient.estimate` fails closed outside the verified model and bounds one structured generation. Generation metadata supports cost reconciliation.
- SQL `settle_analysis` works on owner-filtered reservations and preserves original-month accounting. Reservations without a job can use the same ledger.
- Item deletion and expiry cascade child data; billing reservations remain. New chat content must reference both item ID and owner ID.
- Existing `chat_messages` has no generation state/idempotency or search accounting. A durable turn record is required to prevent duplicate search/generation across retries and replicas.

Alternatives: source-only chat cannot investigate the topic; unconditional research wastes a search on answerable questions; an unrestricted tool loop violates the one-search limit. A structured answer-or-search response followed by one bounded research pass fits the requirement without an agent framework or dependency.
