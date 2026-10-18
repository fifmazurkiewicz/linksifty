# Approved source relevance decisions

Owner approved the five-step in-chat design with “yes lets do it”. Native
execution in this chat; no separate design approval is pending.

- Derive one bounded query from readable public source title/prose, excluding X
  IDs and provenance labels. No extra query-generation model/call or blacklist.
- Preserve at most twenty URL/title/snippet candidates transiently. Jev 1.13 makes
  one typed relevant/irrelevant choice per candidate, in one bounded request.
  Accept relevant only at confidence >=0.8 (provisional, not measured accuracy).
- Reuse existing Jev choice validation, HTTPX, credentials and price caps. No
  model-generated URLs; IDs map only to supplied candidates. Invalid/missing
  decisions or unknown costs admit no candidate. No fallback to fetch-all.
- Reserve at most 20 * 32000 * $0.042/M = $0.02688 for the bounded selection
  request. Record generation and actual cost separately in the shared monthly
  ledger. Unknown costs stay held; durable job pointer prevents another attempt.
- Add migration 000017 for purpose/pointer/admission/recording/claim shape. Reuse
  existing source_context persistence, safe downloads and fetched-text evidence.
  If selection is unavailable/uncertain/budget blocked, analyze primary only.
- Snippets are classifier input only, never citations, database passages or
  Langfuse payloads. Trace query, candidate URL/decision/confidence and skip reason.
- Disclose selection cost and public article/metadata sharing beside existing
  opt-in. Correct generic uncertainty wording for any research call. Existing
  saved results stay unchanged; no automatic reprocessing or paid acceptance.
- Deployment requires the owner to apply migration 000017 before matching code.
  No production DB/environment mutation is authorized by local implementation.

Rollout consent refinement: migration 000017 disables web_search on pre-existing
jobs without saved research. Those opt-ins predate Jev's charge/data disclosure.
Saved research remains reusable. Pause old workers and submissions before migration,
then deploy the matching UI/backend before allowing new opt-ins; no mixed versions.
