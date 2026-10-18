# Rich X source ingestion implementation plan

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
