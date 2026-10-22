# Feature and rollout reference

Preserved from the previous README on 2026-10-22, including the existing admin-count update.
For the current guided documentation, start at [the documentation index](../README.md).
Migration and hosted-verification statements below describe their individual rollout, not current hosting status.

## Processing and usage

New AI previews, topic titles and assessment prose use Polish for Polish sources
and English for all other source languages. Chat replies use Polish or English
according to the user's question, defaulting to English for other languages.
These are model instructions; proper names, code and verbatim source quotations
are preserved. Saved results are not automatically translated or regenerated.

Queue entries use concise AI topic titles in All, Needs action and Ready, with
clickable original URLs. New analyses generate titles in the same model call;
titles survive assessment validation failures. Existing untitled ready/failed
items offer **Generate title**, with confirmation before using the monthly AI
budget. This uses complete saved source text and leaves assessments unchanged.
Apply migration `20261019_000020_ai_titles.sql` before the matching backend/UI.
See [title rollout](../deployment/setup.md#ai-topic-titles-migration-000020).

The queue now shows persisted live stages, source-backed results, manual-content
recovery and actual OpenRouter USD spend/reservations. Settings saves the future
valuable threshold; administrators can edit per-user monthly caps, including zero.
The Admin tab shows the number of accounts awaiting approval, refreshed on
navigation and after account decisions. The count is hidden when zero or unavailable.

Links awaiting pasted content also offer **Retry**, which fetches the source again
and starts analysis on the same item. It uses the monthly analysis budget; X reads
may incur separate charges. **Paste content** remains available. Uncertain X
attempts and unresolved charges cannot be retried. Deploy migration
`20261018_000014_retry_fetch.sql` before the matching frontend; no new API is required.

Settings also shows the eight assessment criteria. Each account can edit descriptions and integer weights (1–10), saved together with its valuable threshold. New model analyses capture those rules; completed and interrupted analyses keep their original rubric, visible in detail. Requires migration `20261016_000009_assessment_rubric.sql` and matching backend/frontend.

New analyses select numbered source passages. The backend supplies each saved
citation’s original text and source, preventing model transcription and attribution
errors. Existing stored results remain compatible; deploy the backend to activate.

Use server-only `OPENROUTER_API_KEY` and `OPENROUTER_MODEL=openai/gpt-4o-mini`.
Other model IDs fail closed until their cost bounds are verified. Default monthly
budget is 10 USD per user; inference first reserves a conservative maximum and
then settles provider-reported cost.

Migration 000005 and the matching frontend/backend must ship together. Workers
are bounded and resume on authenticated visits; no paid always-on worker is used.
Cost records retain 30 days, with unresolved reservations and current-month totals
preserved. Enable and verify the database retention schedule for inactive users.
See [setup section 13](../deployment/setup.md#13-processing-usage-retention-and-recovery)
for database gates, activation and recovery. No hosted readiness is implied.

### Optional Brave + Langfuse

The Add screen supports explicit Brave + Jev source checking for public links (one topic-based search, one budgeted relevance-selection call, then up to 20 relevant page fetches; migration 000017), after migration `000007` and server-only key/verified plan-rate configuration. Search charges share the USD cap with actual OpenRouter costs. Langfuse diagnostics are opt-in and cannot block processing; enabled tracing includes bounded article/model content with documented redaction. No secret goes into the frontend. See [setup](../deployment/setup.md#brave-source-discovery-and-langfuse-tracing-migration-000007). Real provider activation remains an operator step; source deduplication is heuristic, not proof of independent fact verification.

### Calibrated assessment rules

Migration `20261017_000010_assessment_calibration.sql` introduces purpose-aware
learning value, explicit Not applicable / Not verified states, and hype judgments
requiring cited primary-source evidence. New results show scored-criterion
coverage and explain the verdict; historical results keep their original rules.
Future settings upgrade default descriptions while preserving custom wording and
weights. Deploy database, backend and frontend together; see the
[rollout instructions](../deployment/setup.md#calibrated-assessment-and-20-source-checking-migration-000010).

### Delete links and analyses

Each queue entry has **Delete**. Use the checkboxes and **Delete selected** to
remove a group (up to 50 visible links). Confirm permanent removal of the links,
source text, analyses, citations, chats and jobs. Billing records remain for
charge reconciliation; deleting content does not refund charges or trial usage.
Requires migration `20261017_000011_delete_items.sql`; see the
[activation notes](../deployment/setup.md#permanent-link-deletion-migration-000011).

### Chat about an analysis and its topic

Completed analyses now include a saved conversation with inspectable source
passages. Chat uses the analysis, original article, saved research and recent
conversation first. Only missing evidence triggers web research: at most two
distinct Brave searches per question (one query and one evidence-gap refinement),
followed by safe page reads and a final answer. Ambiguous subjects prompt clarification.
Model and search calls share the existing monthly budget. Request IDs prevent
duplicate paid work after a network error. Deleting/expiring the item removes
chat content while preserving charge reconciliation.

Requires `20261018_000013_analysis_chat.sql` and matching backend/frontend.
Existing OpenRouter and optional Brave configuration is reused; chat works
with saved material when Brave is unavailable. See [rollout and recovery](../deployment/setup.md#analysis-and-topic-chat-migration-000013).

New questions first pass a `typesafe/jev-1.13` relevance/safety gate through
OpenRouter. Relevant questions continue to the answer model; unrelated or unsafe
requests receive an uncited Polish/English refusal without research or answer
generation. Invalid or uncertain classification stops the request. Classification
uses the same monthly budget and server key. Apply migration
`20261018_000015_chat_classification.sql` before deploying the matching backend;
`OPENROUTER_MODEL` remains the assessment model. Chat independently uses
`OPENROUTER_CHAT_MODEL=anthropic/claude-sonnet-5.5` (default), with low reasoning
effort, explicit reply language and direct follow-up instructions. Set the chat
variable to `openai/gpt-4o-mini` for rollback. Sonnet reserves up to $2.08192 per
answer call before settling actual reported cost; the conservative reservation
can block calls with a smaller available budget. No additional migration. See
[classification rollout](../deployment/setup.md#chat-query-classification-migration-000015).

Two-search chat requires `20261020_000022_chat_research.sql` before the matching
backend/frontend. Each search and up to three answer-model calls reserve separately;
uncertain requests are never retried. Older clients remain limited to one search.
See [research rollout](../deployment/setup.md#chat-evidence-gap-research-migration-000022).

### Text-only source analysis

X posts, connected threads, full Article bodies/code and ordinary web pages are
analyzed as text. Images, video, GIFs and audio are not downloaded or read by AI;
results show known media types and explicitly disclose the text-only scope.
Missing, short, truncated or otherwise incomplete text still requests paste.
With migration 000021 and the matching app, readable partial text also gets an
automatic one-sentence **Partial preview**, using the monthly AI budget disclosed
at submission or Retry. It carries no score and does not unlock assessment.
Old jobs default off; old failures need an explicit Retry. No extra button or
automatic paid resend is introduced. [Preview rollout](../deployment/setup.md#automatic-partial-previews-migration-000021).
Article embeds accept both X field names (`tweets` and `posts`). Missing embedded
text is fetched once and deduplicated within the shared twelve-request,
hundred-post and sixty-second acquisition limits. Unavailable embedded text still
requests paste; extra X reads can incur the existing disclosed X charges.
Migration `20261019_000019_text_only_sources.sql` must follow 000018 before the
matching backend/UI deployment. Historical analyses are not relabeled or rerun;
existing uncertain image charges retain their accounting safeguards.
See [text-only rollout](../deployment/setup.md#text-only-operation-migration-000019).
The embedded-text compatibility fix needs only the matching backend deployment,
with no additional migration. See the [source workflow](../../.agent/context/changes/x-rich-sources/text-only-workflow.html)
and [verification evidence](../../.agent/context/changes/x-rich-sources/evidence.md#embedded-article-text-verification--2026-10-19).


Jev selects comparison pages before downloads, using article and candidate
metadata; unrelated numeric-ID search matches are rejected. The Add opt-in
shows the separate maximum USD 0.02688 selection hold and data sharing. Apply
[migration 000017 and coordinated rollout](../deployment/setup.md#topic-relevant-source-selection-migration-000017)
before deploying the matching backend/UI. Existing saved assessments remain unchanged.
