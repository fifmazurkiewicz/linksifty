# Verified context — 2026-10-18

Graft is unavailable; focused repository reads used.
- processing_service.py:235-244 constructs a nonempty numeric X query from URL path;
  lines 259-315 retain unique readable fetched pages without semantic relevance.
- BraveSearch requests twenty results and currently discards title/description.
- Existing chat Jev integration uses OpenRouter Decisions, typed choice confidence,
  server-only OpenRouter credentials, provider price caps and durable call admission.
- Reusing that gate requires a distinct job reservation purpose/pointer, generation
  recording, orphan reconciliation and migration coverage. Chat turn slots cannot
  safely be reused for processing jobs.
- Existing search consent covers Brave plan price plus AI analysis; it must disclose
  the additional Jev selection charge before activation. No new credential needed.
- Search snippets may be transient selection metadata, never evidence or persisted
  passages. Existing fetched-page, duplicate-host/content and source-offset guards
  remain necessary after classification.

Official sources read 2026-10-18:
https://openrouter.ai/typesafe/jev-1.13 lists structured decisions, a 262144-token
context and $0.042/M input with zero output price. This differs from historical
repository research that listed 32K context; the new operation can still enforce
its own smaller request bound with a conservative framing margin.
https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request
supports multiple named typed questions, shared state, choice/confidence/
probabilities and generation ID plus usage cost.
https://docs.typesafe.ai/concepts/system-one describes typed decisions rather
than free-form text. Jev therefore selects supplied candidate URLs, not invented
websites or generated search prose.

Approved bounded design: use public article title/text for query,
retain bounded candidate URL/title/snippet, ask Jev a relevance choice per candidate
in one bounded request, fetch only relevant choices above the provisional 0.8
confidence threshold. Record decisions/skip reason/confidence in job tracing without
persisting snippets. Missing/invalid/uncertain choices admit no site. Keep analysis
primary-only when no source qualifies; never label this independent verification.
Reserve/settle Jev separately under the same monthly budget and retain uncertain
holds without resending. Add mocked provider/service and owner/lease/budget/recovery
SQL checks. Real classification accuracy and hosted migration remain external.
