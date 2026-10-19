# Linksifty architecture

Current source policy (2026-10-19): complete **text only**, with durable metadata
for omitted media. The rich-media acquisition/vision sections below are historical;
see [the active text-only flow](#text-only-analysis--migration-000019).

Updated 2026-10-19. The repository is a monorepo: `backend/` is the uv-managed FastAPI package, `frontend/` is React/TypeScript/Vite with npm. Root documentation and `uv.lock` are shared.

## Implemented request path

1. The browser starts Google OAuth through Supabase and restores its session. Every API request sends that session's access token. `api/auth.py` asks Supabase's authenticated user endpoint to validate it and returns the verified UUID and email. Missing/rejected tokens return 401; unavailable authentication returns 503.
2. FastAPI routes pass that UUID to `ItemService`. The service uses the application repository contract; concrete Supabase HTTP integration is wired in the entrypoint.
3. Every repository query includes an owner predicate. Submission calls the server-only `submit_fetch_items` transaction to insert item and job together before returning 202. List, detail and confirmed bulk-deletion routes are wired; marking read still needs a product route.
4. `/v1/me` creates a pending profile for new users and reports the verified owner as admin only when `LINKSIFTY_ADMIN_EMAIL` matches. Pending users may submit three trial links; rejected users are blocked. The admin API returns account metadata only and never exposes another user's content. Approval mail is sent through Resend after the status transaction commits.
5. Explicit `LINKSIFTY_DEMO_MODE=true` enables sample responses. Demo responses carry `demo: true`; production defaults to false.

This path is verified using mocked HTTP/frontend tests and local pgTAP/RLS gates. The owner reports hosted migrations through 000006 applied; this agent has not independently run hosted acceptance.

## Locally implemented processing path

`main.py` composes the owner-scoped `ProcessingRepository`, `OpenRouterClient` and
`ProcessingService`. Routes in `api/processing.py` translate HTTP; orchestration
lives in the application service, exact budget/lease concurrency in PostgreSQL,
and the deterministic score/verdict remains in pure domain code.

1. Submission persists item/job together and wakes bounded API work (three owners
   concurrently, up to five jobs per wake). A later authenticated queue visit
   resumes claimable work. No paid always-on worker or broker is used.
2. Each redirect is validated and pinned to public DNS answers. Fresh proxy-free
   clients isolate cookies, Host and TLS SNI. Time/MIME/body limits and content
   checks reject partial/blocked/unsupported sources into manual paste before any
   paid call. Text acquisition skips scripts, navigation and other boilerplate.
3. SQL reserves against current UTC-month actual spend plus all unresolved
   reservations under an owner settings lock. Only the verified model's context
   bound is supported: full context + bounded output at enforced provider price
   ceilings, without a tokenizer-size heuristic. Unknown models fail closed.
4. The adapter supplies bounded, ID-labelled source passages and validates structured
   eight-criterion output selecting those IDs. It restores the exact original excerpt
   and source itself; model-written quotes/source IDs are not accepted.
   A response is saved under its lease before settlement; a late response's
   generation ID remains bound to its original reservation. Actual provider USD
   is settled idempotently into the reservation's original month. A missing cost
   remains reserved, never treated as free or automatically sent again.
5. The pure scorer computes the final result using the threshold captured by the
   atomic reservation. Fenced SQL commits result/citations/completed state together.
   A saved result can be recovered after interruption without repeating inference.
6. Workers heartbeat every 15 seconds, with 60-second fenced leases. Snapshots
   expose freshness (45 seconds) separately from durable stage. After a crash the
   UI shows paused work; a later visit claims an expired lease. A reserved attempt
   resumes reconciliation rather than starting another model call.
7. Bearer-authenticated SSE publishes owner-only snapshots and usage with bounded
   50-second connections, account access rechecks and reconnect recovery. Frontend
   session expiration/sign-out clears private state and aborts the prior stream.

These paths have mocked application/API/adapter tests; PostgreSQL/hosted checks
are separate gates. The older standalone `AssessmentService` remains a draft-to-
score utility; it is not the runtime provider orchestration path. Primary X
ingestion has an optional official adapter (see below). Analysis/topic chat is
implemented locally (see below); hosted chat/source acceptance remains separate.

## Data and trust

Migration `20261015_000005_processing_usage.sql` adds exact numeric USD totals and
reservations, server-controlled monthly caps, stage/result/heartbeat fields and
owner-scoped processing RPCs. Browser mutation privileges on settings/content/
usage are revoked; even admins cannot use content APIs for another user. The
admin endpoints expose account usage/limits only, without source access.

Cost details expire after 30 days; current-month totals and unresolved
reservations survive detail cleanup. The API performs owner-scoped cleanup on
wake/read; `supabase/retention.sql` defines the explicit database schedule required
for inactive accounts. Expired-source reservations with a generation ID can be
reconciled without source content. No-ID outcomes require verified operator
reconciliation before further paid attempts. The cron script is provided, not
activated by the agent.

Database tests include pgTAP and a local disposable-database concurrent-reservation
gate. No database validation is inferred from service-role HTTP mocks; cross-owner
foreign-key hardening and the remaining broader C1/MVP work retain their own gates.
Provider credentials stay server-only. Source/provider text is untrusted; all
private reads and writes carry verified owner scope. Marking read still needs
a product route outside this change's scope.

## Confirmed permanent deletion (migration 000011)

The queue's single and bulk actions share `POST /v1/items/delete`, with 1–50
unique item IDs and strict confirmation. `ItemService` delegates to one
owner-scoped, server-only SQL transaction. It locks profile/settings, then
reservations/jobs/items in established writer order; all IDs must belong to
the authenticated owner, and inconsistent child ownership fails closed.
Existing foreign-key cascades delete links, source text, analyses, citations,
chat and job/research/model content. Retained billing records are detached and
their custom rubric snapshots scrubbed. Current spend, unresolved reservations
and trial usage remain. Deleted jobs fence late content writes while the
original reservation can still receive late generation metadata for settlement.
The browser filters deleted IDs out of stale in-flight queue snapshots.

Editable source and artifact:
[workflow JSON](../../.agent/context/changes/link-deletion/deletion-workflow.json)
and [workflow HTML](../../.agent/context/changes/link-deletion/deletion-workflow.html).
Source/schema validation, delivery and strict artifact checks pass; diagram
browser QA is unavailable because Chrome/Chromium is absent. This is local
verification, not evidence of a hosted deletion.

## Diagrams

- [Processing/recovery contract HTML](../../.agent/context/changes/processing-usage-inbox/lifecycle.html) · [editable JSON](../../.agent/context/changes/processing-usage-inbox/lifecycle.json). Includes cost uncertainty and heartbeat/lease behavior; not proof of hosted execution. Automated browser evidence remains separate from deterministic artifact checks.

- [Account access and approval HTML](../../.agent/context/changes/multi-user-access-admin/architecture.html) · [editable JSON](../../.agent/context/changes/multi-user-access-admin/architecture.json) (Stage 1 target and local implementation; hosted activation remains manual)

The new diagrams are planning views: solid current request relationships and labelled planned relationships. They are not evidence of deployment. Earlier diagrams are retained as historical design artifacts.

- [Architecture HTML](../../.archify/architecture-linksifty-status-20261013-010804/linksifty-status.html) · [editable JSON](../../.archify/architecture-linksifty-status-20261013-010804/candidate.json)
- [Target lifecycle HTML](../../.archify/lifecycle-linksifty-target-20261013-010804/linksifty-target.html) · [editable JSON](../../.archify/lifecycle-linksifty-target-20261013-010804/candidate.json)

See [completion plan](../superpowers/plans/2026-10-13-linksifty-completion.md) and [Supabase setup](../deployment/supabase.md) for tasks and activation steps.


## Docker deployment slice — 2026-10-14

The Render backend is packaged by the root Dockerfile (Python 3.11.16, uv
0.12.17, locked production dependencies, UID 10001). Runtime PORT and server
credentials are supplied by Render; Vercel remains frontend-only. GitHub CI
builds the same Dockerfile and smoke-checks the actual image. A successful image
build does not prove hosted Supabase/provider or complete MVP behavior.

- [Deployment HTML](../../.archify/architecture-linksifty-docker-20261014-005227/docker-deployment.html)
- [Editable JSON](../../.archify/architecture-linksifty-docker-20261014-005227/candidate.json)

Archify validation, delivery and strict artifact checks pass. Browser check is
skipped because Chrome/Chromium is unavailable; no visual QA is claimed.

## Optional source discovery and diagnostics

`main.py` additionally composes BraveSearch and JevSourceSelector (existing HTTPX), plus LangfuseTelemetry (official SDK at the infrastructure edge). The application only depends on SearchProvider, SourceSelector and a scope/event Protocol. No new worker/broker or general agent framework.

An explicit unchecked Add checkbox discloses a public-article query, Brave charge, bounded article/candidate sharing and Jev maximum reservation/actual cost. `/v1/capabilities` enables it only with configured search/selection adapters and a positive verified plan rate. `/v1/items` carries `web_search`; a server-only transaction persists consent with the original item/job trial accounting. Pasted content remains outside search. Migration 000017 is required for the current pipeline; old unfinished opt-ins are disabled during coordinated rollout.

The job first validates/acquires the primary source. Research reserves a separate provider-tagged amount under the same owner budget lock, sends one query derived from readable primary title/prose (excluding URLs/provenance/long numeric IDs), then reserves one separate Jev selection call. Brave supplies at most twenty transient URL/title/snippet candidates; Jev makes a typed relevant/irrelevant decision per supplied ID. Only relevant decisions with confidence >=0.8 and known cost proceed to at most twenty safe page fetches. Invalid/missing decisions, budget denial or unknown cost yield primary-only analysis. There is no fetch-all fallback or automatic retry. The confidence threshold is provisional, not proof of relevance. Transient search responses/snippets are not evidence or stored. Normalized content hashes and host checks reduce duplicates; these heuristics do not prove independence. Bounded fetched passages and source identities are owner-scoped in job search_context and expire with the item. A confirmed search response settles at operator-configured plan price; uncertain outcomes remain reserved and are never automatically resent. Migration 000017 persists a distinct selection reservation pointer; reclaimed workers never resend it. Late generation recording and orphan reconciliation reuse the shared ledger. Model retries reuse persisted research. Usage labels disclose actual OpenRouter cost versus plan-derived Brave charge.

The model receives primary/additional source texts, not a browsing tool. The model selects a supplied passage ID per criterion. The adapter derives the original source and exact text; application and SQL validate offsets against stored material. For v2, cross-source confirmation is not_verified without an external supporting citation; legacy v1 retains its minimum-score guard. Detail exposes checked-source URLs and unavailable/uncertain status. Source discovery does not establish complete factual verification or grounded chat.

Langfuse root/fetch/research/generation observations and discrete events capture the complete relevant analysis flow: stages, search/skip/fetch decisions, source passages, model messages and completion, citation validation, budget changes, persistence, heartbeat and recovery. Article/model content is included by default when existing LANGFUSE_ENABLED is enabled, per the owner’s revised decision. Trace fields are bounded and redacted; configured secrets, account identity, lease tokens and authentication headers are excluded. Exceptions are reduced to class names; telemetry errors neither repeat nor stop business work. This is best-effort observability, not a durable charge ledger. SDK shutdown is flushed outside the event loop. Langfuse defaults off; its access and retention are operator-managed independently of Supabase cleanup.

Chat reuses this telemetry boundary: one `chat` scope per newly claimed turn,
correlated by opaque `turn_id`, contains `openrouter.chat.classification` and
`openrouter.chat.answer` generations plus redacted HTTP response events and the
persisted `chat.finished` outcome. This covers classifier confidence/probabilities,
raw and validated model output, reported token/cost details and failure reasons.
Duplicates return stored state without another generation. Backend `chat_failed`
warnings contain only turn ID and stable reason. No chat policy, owner scope,
budget rule or retry behavior changes; the same opt-in content/retention policy
applies. See [chat diagnostics](../deployment/setup.md#analysis-and-topic-chat-migration-000013).

Chat answer selection is independent: the same edge adapter uses
`OPENROUTER_CHAT_MODEL` (Sonnet 5.5 by default) for reply generations, with its own
verified full-context reservation, output cap and provider price ceilings.
Assessment/title/preview selection stays under `OPENROUTER_MODEL`; Jev stays
pinned separately. Relevant payloads explicitly carry the validated reply
language through both answer steps. No new service, storage or provider retry
path is introduced. See [chat model rollout](../deployment/setup.md#chat-answer-quality-and-model-selection--2026-10-19).

Migration 000022 extends the same chat path to two distinct searches per question:
one initial query and one evidence-gap refinement, with up to three answer-model
generations. The updated UI explicitly requests `max_searches: 2`; omitted values
retain the old one-search consent. Unique `search_refined` / `answer_final` ledger
slots preserve owner/budget/replay fences; only a confirmed settled first search
can admit refinement. Uncertain calls never retry. The model receives attempted
queries, cumulative evidence and explicit reply language. Its last generation
cannot search. New turn deadlines are eight minutes. See [research rollout](../deployment/setup.md#chat-evidence-gap-research-migration-000022)
and the [editable workflow](../../.agent/context/changes/chat-research/workflow.json)
with [HTML](../../.agent/context/changes/chat-research/workflow.html).

- [Brave/Langfuse workflow HTML](../../.agent/context/changes/processing-usage-inbox/brave-langfuse.html) · [editable JSON](../../.agent/context/changes/processing-usage-inbox/brave-langfuse.json). Repository-backed at local code commit c844819. Validate/deliver/strict artifact checks pass; automated browser check skipped because Chrome unavailable; no fresh perceptual inspection claimed. All diagram labels, explanations and viewer controls are in English. Latest workflow receipts are under brave-langfuse.content-tracing/; lifecycle English receipts remain under lifecycle.english/. Prior receipts are historical.

Submission/resume maintenance (000008): owner-profile lock serializes duplicate URL decisions before creating new items/jobs/trial usage; existing rows remain. UI preflight is advisory, server guard authoritative. The original citation-format repair has been superseded by passage-ID selection within the OpenRouter adapter; existing exact source/offset fences remain. These are guards within existing steps, with unchanged topology and no new external calls.

## Assessment calibration — local change, 2026-10-17

Migration 000010 adds rubric version compatibility, unscored criteria, nullable
aggregate scores and separately cited hype signals. Existing owner/lease/budget
RPC fences remain in place. New settings use the revised eight descriptions;
reserved jobs and saved results retain their snapshots. Default descriptions
upgrade by criterion ID while custom wording and all weights survive.

The provider receives source URL identities and the UTC analysis date as
untrusted metadata. It selects exact supplied passages for each explanation and
for up to three primary-source hype signals. Both application and SQL retain
exact source-offset checks. Pure scoring excludes unscored criteria and gates
valuable on four key criteria; hype depends on grounded signals, not a low sum.
The detail view presents statuses, coverage, verdict reasons and hype citations.

One opted-in Brave request asks for 20 candidates; research attempts at most 20
additional pages, with existing host/content deduplication and no implicit paid
retry. Stored comparison material is bounded to 12,000 characters per source
and 1.2 MB per research context. Provider input further apportions a conservative
UTF-8 budget across additional excerpts, preserving the entire primary text.
Oversized inputs fail before a paid model HTTP request with zero model cost;
no full-page or comprehensive verification is claimed.

- [Calibrated assessment workflow](../../.agent/context/changes/assessment-calibration/assessment-workflow.html)
  · [Editable diagram source](../../.agent/context/changes/assessment-calibration/assessment-workflow.json)
The diagram's validation, delivery and strict artifact checks pass; browser
inspection is skipped because Chrome/Chromium is unavailable. The editable
source pins an isolated working-tree evidence snapshot preserved in
`diagram-source.bundle`; it does not claim an uncommitted change exists at the
main repository's HEAD.

- [Canonical progress](../../.agent/context/changes/assessment-calibration/progress.md)

Coordinated database/backend/frontend rollout and live model calibration remain
external activation steps; local mocked tests cannot establish model agreement
on live articles.

## Official X acquisition — local implementation, 2026-10-18

For primary X URLs, ProcessingService selects the injected XAdapter only when
X_API_READS_ENABLED and the server token are configured. Ordinary pages and
additional research sources use the existing safe fetcher. Migration 000012
adds a private atomic begin_x_fetch RPC: verified owner, current lease, account
access and item expiry must hold, and each job may admit only one X attempt.
A recovered attempt requests paste; cached complete text is reused. Migration
000014 extends the existing explicit resume operation to fetch failures. The queue's
Retry action requeues the same job and resets X admission only after a terminal
fetch failure; an uncertain X attempt or unresolved charge remains blocked.
Owner, expiry, account-access and duplicate guards apply. The UI discloses analysis
budget use and separate X charges. Automatic recovery never resets X admission.

The adapter uses fixed api.x.com HTTPS lookup/full-archive endpoints, at most
12 HTTP requests, 100 thread/context posts, 1 MB response bodies, 100 KB source text
and a 60-second deadline. All returned pages and author/conversation identities
are checked, parents must connect to the root, and long text replaces previews.
Source URLs stay with each post. Missing/partial or unsupported source content
requests paste before assessment reservation. X may omit undisclosed deleted/hidden
posts; the result represents the accessible indexed snapshot. X billing is
operator-approved and separate from the model/Brave ledger.

Archive search also returns the author's replies to other commenters. Those
branches are excluded only when a returned parent belongs to another author in
the same conversation, or descends from an already excluded branch. Missing
thread parents and an excluded submitted post still request paste. Known video
and GIF types are retained as media-omission labels under the active text-only
policy, without requiring image URLs or downloads.

Existing lookup/search requests expand referenced posts. Reply-parent selection
is separate from quote/repost dependencies, so a quoting reply remains connected
to its author's thread. A submitted repost resolves to its expanded original's
author/conversation; its RT preview is excluded. Complete recursive dependencies
are deduplicated and attributed by URL/author ID. Missing references, cycles or
conflicting versions request paste, with no implicit retry. The active Article
path completes missing embedded text with bounded once-only lookups; it does not
look up posts solely to complete media expansions.
Expanded resource charges remain in the operator's X account. The 100-post bound
includes collected expanded context; unrelated expanded content is not source.

- [Current source contract](../../.agent/context/changes/x-rich-sources/text-only-workflow.html)
  · [Editable JSON](../../.agent/context/changes/x-rich-sources/text-only-workflow.json)
- [Historical acquisition contract](../../.agent/context/changes/x-ingestion/x-workflow.html)
  · [Editable JSON](../../.agent/context/changes/x-ingestion/x-workflow.json)

### Full Articles and static images — migration 000016

Historical media-reading architecture, superseded by
[text-only analysis](#text-only-analysis--migration-000019). It remains documented
for old charge settlement and migration history.

The acquisition result can carry bounded ephemeral image bytes alongside full
Article/thread text. The X edge parses complete Article bodies and validates
embedded post/media dependencies; previews and unknown content blocks fail
closed. A separate credential-free media client accepts only static PNG/JPEG/WebP
from HTTPS `pbs.twimg.com`, without redirects or proxies. Twelve images, 5 MB each,
10 MB total and 20 million pixels per image bound acquisition and decoding.

Before caching or assessing, ProcessingService reserves a separate image-reading
slot from the shared monthly ledger. One OpenRouter batch returns all image IDs,
explicit completeness, transcription and visible diagram descriptions. Known
actual cost settles before the final complete source is cached. Extracted text
is labeled model-extracted with image and post provenance. Image bytes are not
stored. Incomplete reading requests paste; unknown cost retains its reservation
and blocks Retry. Existing generation reconciliation also handles attached image
reservations, and late generation IDs survive lease loss or content deletion.

Article code entities are validated and preserved; where offsets are absent,
additional code is explicitly labeled as having an unspecified position. Missing
quoted Article media URLs permit one direct post lookup with existing expansions;
known-invalid sources and already-read posts are never retried. The lookup and
thread search share a hard twelve-request cap inside the 60-second deadline.
Missing expansions or conflicting versions still stop before inference.

Image reading defaults independently to `openai/gpt-4.1-mini` through
`OPENROUTER_IMAGE_MODEL`. One call handles up to twelve images under the existing
0.16896 USD conservative reservation and provider price/output ceilings.
Explicit legacy `openai/gpt-4o-mini` image configuration retains a four-image cap.
The text assessment model and durable generation/settlement contract are unchanged.

Migration 000016 adds a reservation purpose and durable per-job extraction pointer.
Admission checks owner, account status, current lease, expiry, X admission and
the total shared budget. The active-reservation uniqueness key includes purpose,
so manual pasted content can proceed separately while uncertain image charges
remain reserved. An explicit known-terminal fetch Retry alone resets the image
slot. Database migration must precede deployment. Mocked/local verification does
not establish live Article payload compatibility or transcription accuracy.

- [Rich-source contract HTML](../../.agent/context/changes/x-rich-sources/rich-source-workflow.html)
  · [Editable JSON](../../.agent/context/changes/x-rich-sources/rich-source-workflow.json)
- [Progress and activation boundaries](../../.agent/context/changes/x-ingestion/progress.md)

The diagram describes the contract; it does not claim repository snapshot
provenance or hosted X validation. Local tests mock all provider requests.

## Analysis and topic chat — local implementation, 2026-10-18

`ChatService` orchestrates owner-scoped context/history, durable question claims,
model calls and conditional research. `api/chat.py` only handles authentication,
input validation, response privacy and error translation. `main.py` wires the
existing OpenRouter, Brave and safe fetcher with `ChatRepository`; no new provider
framework, dependency or worker is added.

The first structured generation answers from supplied passages or requests one
targeted search for missing evidence. A unique search reservation admits at most
one Brave request for the turn. Up to 20 result URLs are safely fetched, with four
concurrent reads and bounded content/time. One final generation cannot request
another search. Every answer paragraph selects known passages; the application
restores exact excerpts and source URLs. Search snippets are never evidence.
Saved analysis describes its historical assessment, rather than independently
verifying article claims. Model grounding/necessity still needs live evaluation.

Migration 000013 adds RLS-protected `chat_turns` with a composite item/owner
foreign key. Browser writes are revoked. A client request UUID admits one
executor, one active turn per item, and unique decision/search/answer billing
slots. All reservations share the existing user settings lock and USD ledger.
Unknown costs remain reserved; generation IDs can settle after deletion. Item
deletion/expiry cascades all chat content; late answer writes require an existing,
unexpired, owner-matching turn and completed item. Chat GET/POST uses no-store.

Chat restores the latest 100 questions. Generation uses the recent eight completed
turns, analysis/original text and up to 30 relevant saved research sources, with
byte-bounded passage selection. Word overlap is a simple retrieval heuristic,
not exhaustive evidence coverage. Interrupted turns become explicit failures
after five minutes on a later read; paid calls are never automatically retried.

- [Behavioral contract HTML](../../.agent/context/changes/analysis-chat/chat-workflow.html)
  · [Editable JSON](../../.agent/context/changes/analysis-chat/chat-workflow.json)
- [Progress and verification](../../.agent/context/changes/analysis-chat/progress.md)

Archify source/artifact checks pass. Browser QA is skipped because Chrome/Chromium
is unavailable; no perceptual review or hosted acceptance is claimed.

### Chat query gate — migration 000015

Before answer generation or research, ChatService reserves the unique
`classification` slot and asks OpenRouter Decisions model `typesafe/jev-1.13`
about the latest message. It receives bounded original/analysis excerpts and
recent conversation; saved research does not expand the original topic's scope.
The provider returns scope and refusal language, never generated refusal text.
Only a valid, sufficiently confident relevant classification reaches the existing
answer/search flow. Off-topic/unsafe messages use fixed Polish or English replies
with no citations or further provider/search calls. English is the fallback for
other languages; malformed, low-confidence and failed classifications stop.

The existing OpenRouter adapter owns HTTP and validation; application orchestration
and owner-scoped persistence remain in their established layers. Classification
shares the monthly USD ledger, unique-call fences, cost settlement, generation-ID
recovery and deletion behavior. No new dependency, key or worker is introduced.
See the [editable sequence](../../.agent/context/changes/chat-query-classification/chat-sequence.json),
[sequence HTML](../../.agent/context/changes/chat-query-classification/chat-sequence.html)
and [verification record](../../.agent/context/changes/chat-query-classification/evidence.md).


## Source relevance contract — migration 000017

`domain/search_query.py` derives the bounded public query. The Brave adapter
retains metadata transiently; `infrastructure/source_selector.py` reuses the
existing Jev typed-choice validator and price caps. `ProcessingService` validates
complete decision coverage, maps IDs only to supplied candidates and gates safe
fetches. Snippets are not evidence or persisted passages. The selector adds no
SDK/dependency, search-query model or domain blacklist. Existing content/host
hash deduplication and exact passage provenance remain necessary after selection.

One bounded request reserves at most USD 0.02688 (twenty conservative per-question
input bounds), then settles actual returned cost. Unknown cost remains held;
failed selection does not buy a retry. SQL admission is owner/lease/expiry/account
fenced and requires cached primary content plus a settled Brave reservation.
Deletion retains accounting and the first late generation ID. The new purpose
and pointer require migration 000017 before deployment. Existing cached research
is reused, without retroactive quality claims. New source checking requires the
updated unchecked opt-in and data/cost disclosure.

[Source selection workflow](../../.agent/context/changes/source-relevance/source-selection-workflow.html)
· [editable contract JSON](../../.agent/context/changes/source-relevance/source-selection-workflow.json).
This is a behavior contract for the approved change, not a frozen repository map.
Automated artifact checks and browser limitations are recorded in the change's
evidence. Chat answering/research policy remains unchanged.


## Reader replies — migration 000018

`DiscussionService` resolves only owned, completed, unexpired items and persisted
source IDs. DiscussionRepository invokes server-only list/admit/finish RPCs; the
API handles authentication, strict consent and no-store responses. The entrypoint
wires the existing X adapter only when X reads and its server token are enabled.

A collapsed Reader comments panel reads cached results on opening. An explicit
Load X replies click discloses X charges and admits one attempt per item/post,
including URL aliases. X performs one post lookup and one conversation-search
page, bounded to thirty seconds and twenty text replies. Media is labeled but
not downloaded. Uncertain attempts stay admitted; refresh reads saved data only.
Owner/item/attempt completion fences and cascading deletion prevent late writes.

Selected safe social candidates are retained as discussion links in research JSON
before ordinary host deduplication, separately from fetched evidence. Replies
and discussion candidates never enter assessment scoring or model passages.
Legacy assessments can use their primary and already saved social sources;
there is no retroactive search. Reddit has no adapter and is shown unsupported.

[Reply workflow HTML](../../.agent/context/changes/x-rich-sources/reader-replies-workflow.html)
· [editable contract](../../.agent/context/changes/x-rich-sources/reader-replies-workflow.json)
· [verification](../../.agent/context/changes/x-rich-sources/evidence.md#reader-replies-verification--2026-10-19).
This is a behavioral contract. Archify static checks pass; diagram browser QA is
skipped because Chrome is unavailable. Synthetic product browser QA is separate.


Image-reading maintenance: validated X /media/ photo URLs request original size
using name=orig under the existing download/decoding bounds. MediaResult carries
a code-generated failure check through the existing service to Render logs and
image.reading telemetry. Raw response/image/source text is excluded. Provider
admission, prompt/model, accounting, unknown-cost fencing and complete-source
requirements remain unchanged. This is an existing adapter/service correction,
with no new integration or data-flow stage.


## Text-only analysis — migration 000019

The X adapter validates full text, thread identity/connections, Article bodies/code
and quoted/embedded text. Media presence maps to bounded image/video/GIF/audio/
other labels. Missing byte URLs/expansions do not block otherwise complete text;
media metadata cannot satisfy minimum text length. No media-only hydration or
CDN request occurs. The public HTML adapter records visible media tags without
fetching them or treating alt text as a transcription.

Article `entities.tweets` and `entities.posts` normalize to deduplicated validated
embedded IDs. The dependency walk reuses the acquisition-local post map and looks
up missing embedded posts once through the existing official lookup adapter.
Nested Articles use the same cycle/version checks. Thread search and embedded
lookups share twelve requests, one hundred posts and the sixty-second deadline;
a known full post map stops another lookup before spending. Any lookup failure
ends acquisition, and ordinary quote/repost references still require expansions.
No media-only lookup or partial-source assessment is introduced.

Migration 000021 adds an explicitly disclosed automatic **Partial preview** on
failed/incomplete acquisition. `FetchResult.partial_text` is separate from complete
`text`; safe readable fragments are bounded to 6,000 characters and remain in
memory. X previews traverse only returned reachable references and exclude
withheld/unrelated text; HTML previews strip scripts/navigation and retain the
existing target/MIME/byte guards. They never enter source caching or research.

Processing reserves one preview call under the existing shared budget before
using the current OpenRouter model with a sentence-only schema. Only its bounded
sentence becomes owner-scoped item metadata; there is no assessment, score or
status promotion. A durable per-job slot, current lease, consent/account/expiry
guards and late generation recording preserve existing recovery protections.
Unknown preview costs remain held and suppress Retry until reconciliation. Old
jobs default to no preview consent; updated submission/Retry disclosure authorizes
it without an extra button. [Preview contract](../../.agent/context/changes/partial-previews/workflow.html)
· [editable JSON](../../.agent/context/changes/partial-previews/workflow.json).

ProcessingService caches validated text with omission metadata, then follows
existing research/assessment admission. Its active image-reader branch and startup
wiring are removed. Existing legacy image adapters/accounting stay inactive for
new acquisition; generation reconciliation and uncertain billing safeguards remain.
The assessment prompt explicitly restricts claims to supplied text. Metadata is
not source evidence and does not enter citation offsets or domain scoring.

Migration 000019 saves primary media types atomically alongside text/hash through
an owner/account/lease/state/expiry-fenced server-only RPC. Assessment GET reads
owned metadata; NULL distinguishes unrecorded legacy/manual scope from [] on new
text-only fetches. Research source types are stored in existing JSON, outside the
text passage. The UI shows a visible scope notice before summary plus per-research
source notes; historical analyses are not relabeled. No new service/dependency.

[Workflow HTML](../../.agent/context/changes/x-rich-sources/text-only-workflow.html)
· [editable contract](../../.agent/context/changes/x-rich-sources/text-only-workflow.json).
This is the owner's behavior contract, not a frozen repository snapshot. Static
Archify checks pass; its browser check is skipped (Chrome unavailable). Native
product QA with synthetic desktop/mobile fixtures is recorded separately.
## AI topic titles — migration 000020

The assessment provider returns a separately validated topic title in its normal
response. `record_model_result` writes it to the existing owner-scoped item under
the active lease, preserving meaningful titles and retaining it through later
assessment failures. Ready state still requires a valid settled assessment.

The queue also exposes confirmed title-only generation for existing untitled
ready/failed items. `ProcessingService` orchestrates `reserve_item_title`, a
bounded call to the existing OpenRouter adapter, `record_item_title` and existing
settlement. The database checks owner/account/expiry, complete cached source,
inactive processing and shared monthly capacity. A per-item unresolved ledger
reservation prevents duplicate paid execution; content deletion detaches that
reservation while preserving late-generation reconciliation. No source fetching,
new worker, new service or assessment rerun is introduced.

Editable [title workflow JSON](../../.agent/context/changes/ai-link-titles/titles-workflow.json)
and [workflow HTML](../../.agent/context/changes/ai-link-titles/titles-workflow.html)
cover normal analysis and confirmed backfill. Schema, delivery and strict artifact
checks pass; browser QA is unavailable because Chrome/Chromium is absent.
