# Rich X source ingestion implementation plan

Active scope is T8–T9: complete text, media-omission labels and bounded embedded
Article text completion. Earlier media-reading tasks describe historical delivery
and legacy charge recovery; they do not enable new image reads.

Goal: complete Article and image source text, budgeted and cached before scoring.
Architecture: existing acquisition -> image extraction -> complete-source cache
-> existing research/assessment. Python 3.11, strict typing, HTTPX/Pydantic v2,
Pillow, PostgreSQL owner/lease RPCs and existing React queue. Scope was approved
by the owner with “YUP LETS IMPLEMENT IT”; execute natively in this chat.
Spec: frame.md and decisions.md. Canonical execution state: progress.md.

Global constraints: no partial assessments, server-only credentials, owner
scoping even for admins, mocked paid integrations, uv-managed dependencies,
English diagrams. No browser cookies, scraping, video/audio or new service.

## Review focus

Unreadable/cropped images; preview-only Articles; hostile media URLs/redirects;
late/deleted/expired-job results; interrupted/unknown-cost extraction. Each has
behavioral tests in its owning task below. No live paid verification is assumed.

## Tasks

- [x] T1 Rich acquisition (`domain/acquisition.py`, `infrastructure/x_adapter.py`,
  new `infrastructure/x_content.py`/`x_images.py` as needed; adapter tests).
  Red tests require full body instead of preview, article media/reference
  dependencies, quoted Article support, unknown block/entity failure, image URL
  isolation, response length/format/size/pixel/frame bounds and missing media.
  Implement in-memory SourceImage and typed content parsing; preserve all existing
  limits. Run focused acquisition tests and strict typing.
- [x] T2 Budgeted extraction (`application/media_contracts.py`, OpenRouterClient,
  ProcessingService/Repository and migration 000016; provider/service/SQL tests).
  Red tests cover all-image coverage, no assessment on incomplete extraction,
  actual/unknown-cost settlement, stale lease/cross-owner/repeated admission,
  monthly/concurrent budget guards, deletion/late generation recording and no
  repeated inference after interruption. Implement bounded base64 vision batch,
  reserve/record RPCs, known-result-only cache and reconciliation using the existing
  ledger. Test migration with existing SQL gate and concurrency scripts locally.
- [x] T3 Product behavior and delivery (Queue, submission cost copy, UI tests,
  setup/architecture/roadmap and Archify workflow). Add precise manual-fallback
  labels, image-reading progress/cost disclosure and uncertain-attempt retry
  exclusion. Update canonical records, then boards. Run backend tests, strict
  mypy, full Ruff lint/format, agent-toolkit check; frontend tests/lint/build.
  Record mutation evidence, diagram validation/artifact/browser status and local
  implementation review before committing/pushing main. Report hosted migration,
  live schema and image-quality acceptance separately.


## Approved bounded compatibility follow-up

- [x] T4 Captured Article compatibility: synthetic code-entity preservation and
  rejection cases; quoted missing-media lookup, no repeated lookup, conflict and
  aggregate-request-limit cases; eleven-image acquisition; shared twelve-image
  bound and dedicated image-model/schema/coverage/cost tests. Implement in
  x_content.py, x_adapter.py, x_images.py, domain/acquisition.py,
  openrouter_images.py, config.py and main.py. Update fallback copy, .env.example,
  setup/architecture/roadmap and the editable English X workflow. Verify full
  backend tests, strict mypy, Ruff lint/format, frontend tests/lint/build and
  agent-toolkit check. Record mutation and offline captured-payload reproduction.
  No hosted fetch, environment change, database migration or new dependency.

## Approved thread and media correction — 2026-10-19

- [x] T5 Exclude only confirmed replies to other commenters (and their author
  descendants) from the author's self-reply thread. Preserve missing-parent,
  cycle, identity and submitted-post coverage checks. Classify known video/GIF
  types before image URL availability. Add regression, mutation and captured-log
  replay evidence, with every remote integration mocked. The owner approved the
  bounded in-chat design with “Approved and lets code”. No video processing,
  paid retry, deployment, dependency or schema change.

- [x] T6 Expandable reader replies for the submitted X link and selected X
  search results, as clarified by the owner. Reddit is conditional on existing
  support; no Reddit adapter exists, so disclose unsupported status. Reuse
  native details/summary and existing tokens. No analysis-note substitution.
  - Record selected X/Reddit candidates as discussion links in existing research
    JSON, separate from fetched evidence. Legacy fetched social sources remain
    eligible. Do not send discussion candidates/replies to the assessment model.
  - Add an owner/item/source-scoped cached discussion table and three server-only
    RPCs (list, atomic once-only admission, fenced completion), migration 000018.
    Check profile access, completed/unexpired item and persisted source membership.
    Retain uncertain admissions; repeat clicks/read refresh never repeat X calls.
    Cascade comments on item/account deletion; late writes cannot resurrect them.
  - Add a small application discussion service, repository edge, authenticated
    no-store GET/POST routes and entrypoint wiring. POST requires explicit cost
    consent. No client-supplied fetch URL; source IDs resolve from owned records.
  - Extend XAdapter with a bounded optional replies operation: fixed official
    lookup plus one archive-search page, at most twenty replies, thirty seconds,
    existing response byte bounds, text-only display and safe username validation.
    No media downloads, extra pagination, automatic retries or paid model calls.
  - Add independently collapsed Reader comments UI. Opening reads cached status;
    only a Load replies button with X-charge disclosure sends POST. Show loading,
    empty, failure/uncertain, unsupported Reddit and missing configuration states;
    link each reply to its original X post and label the result a limited snapshot.
  - TDD covers consent, owner/expiry/source checks, cached/repeated/uncertain
    admission, no provider repeat after persistence failure, X error/size/identity
    guards, research candidate separation, unsafe UI links and disclosure behavior.
    Run mocked backend/frontend suites, strict typing, Ruff, frontend lint/build,
    toolkit and the explicit disposable database gate when available. Record
    mutation evidence, native browser QA and an editable/validated Archify flow.

Scope review before T6 implementation: this matches the clarified approved
feature. All provider reads remain explicit and once-only per owned source;
Reddit integration and broad crawling are outside this change. Database rollout
must precede deployment; local verification makes no hosted-success claim.


- [x] T7 Hosted image-reading diagnosis: retain safe parser rejection checks in
  MediaResult, Render logs and image.reading telemetry; test privacy, accounting,
  coverage, schema, truncation and single-call behavior. Request original-size
  /media/ photos on the existing fixed CDN with no retry or limit increase.
  Local correction/tests complete; actual hosted rejection remains unconfirmed
  until matching diagnostics from an independently authorized attempt are available.
  No model, budget, schema migration or partial-source acceptance change.


## Owner-directed text-only operation

- [x] T8 Disable primary media downloads/reading, preserve complete text checks
  and metadata-only media types across X posts/Articles/quotes and web HTML.
  Replace obsolete active media expectations with regressions for text with
  photos/videos/GIFs, missing expansions, zero CDN/vision/budget calls and short
  or truncated source rejection. Persist primary omission metadata via migration
  000019 and owner-fenced repository; retain research metadata and expose
  nullable historical scope in assessment API/UI. Update submission/retry copy,
  model text-only constraints, setup/architecture/roadmap and English editable
  workflow. Run all project gates, synthetic database checks and native UI QA.
  No hosted/paid operation or automatic reprocessing is authorized by this task.

Plan review: scope is the owner's explicit narrowing of the existing ingestion
flow, not permission to accept incomplete text. Existing image cost settlement
and uncertain-attempt protections remain. Migration precedes matching deployment.

## Approved embedded Article text compatibility — 2026-10-19

- [x] T9 Accept and validate both Article `entities.tweets` and `entities.posts`,
  deduplicating embedded IDs. Reuse expanded text; look up missing embedded posts
  once through the existing official endpoint, including recursively embedded
  Articles. Preserve fail-closed handling for missing ordinary quote/repost
  expansions, invalid content, cycles and conflicting versions. Share the
  twelve-request, hundred-post and sixty-second bounds with thread acquisition.
  Add realistic mocked regressions, mutation and captured-payload replay evidence;
  update the existing text-only contract diagram and deployment documentation.
  Run backend tests, strict mypy, Ruff lint/format and agent-toolkit check.
  No dependency, migration, frontend, deployment or live paid read is needed.

Bounded design approval: the owner accepted the preceding in-chat recommendation
with “Yup, lets do this”. This extends the existing dependency walk; it introduces
no new integration, credential, approval surface or media processing.
