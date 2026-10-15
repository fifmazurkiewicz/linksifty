# Repository evidence

- `frontend/src/App.tsx`: static 60% threshold; queued items incorrectly use completed copy; POST replaces the previous list; no detail interaction or progress subscription.
- `frontend/src/features/admin/AdminPanel.tsx`: approval/rejection/email retry only.
- `backend/src/linksifty/main.py`: accepted submission persists records, response omits assessment data, no executor wiring.
- `application/item_service.py` and `application/item_contracts.py`: list/get/create orchestration only.
- `application/assessment_service.py`: injected draft conversion, no provider or completeness/budget enforcement.
- `domain/scoring.py`: pure score/verdict and snapshot, threshold range 40–100.
- `supabase/migrations/20261012_000001_personal_mvp.sql`: jobs and leases exist; budget is whole cents; owner ALL policy on settings currently permits changing budget through direct client writes.
- `docs/architecture/overview.md`, `docs/roadmap.md`, earlier account specification: opportunistic executor intended; stage-two cost controls depend on processing.

Graft is unavailable in this session; focused repository reads used. No official provider pricing/contract verification is claimed at specification stage; it is an implementation-planning prerequisite. No credentials read or external provider calls made.

## Resumed technical verification — 2026-10-15

- Official [OpenRouter GPT-4o-mini model](https://openrouter.ai/openai/gpt-4o-mini) documents 128,000 context tokens and structured outputs. [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection) documents max-price prompt/completion per million tokens and per-request ceiling. Reservation now bounds the full context and explicit output maximum instead of estimating framing/tokenization. Only this verified model ID is allowed; no live inference/pricing request was made.
- [Usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting) identifies usage.cost as total account charge and generation lookup as reconciliation. Persisted actual cost is sufficient for recovery without another lookup.
- `command -v` checks found no psql, Docker, Supabase CLI or agent-toolkit. Focused Homebrew binary inventory also found no psql/postgres/initdb/pgTAP runtime. No automatic install attempted; owner was asked about providing/preparing a disposable runtime.
- Local browser tab acquisition was denied by the browser URL policy. Do not retry through alternate surfaces. Current UI behavior is exercised by jsdom/component tests; prior screenshots remain prior-run evidence only.
- Archify contract updated for heartbeat/freshness and exact reservation; deterministic validate/deliver/check pass. Automated browser gate skipped because Chrome/Chromium is unavailable; no full-finalize success claim.

## Brave / Langfuse verified contracts — 2026-10-15/16

Graft unavailable; existing service/provider/SQL/API/UI traced with focused reads. No search service existed before this extension. Brave API endpoint and X-Subscription-Token header verified in https://api-dashboard.search.brave.com/api-reference/web/search/get. https://brave.com/search/api/ notes plan-dependent storage rights: do not persist search response/snippets; fetch source content independently and retain only application evidence. No account-specific billing plan inspected or assumed.

https://langfuse.com/docs/observability/sdk/overview documents Python SDK v5, Cloud EU base URL https://cloud.langfuse.com and current observation APIs; self-hosted v3 requires an older compatible SDK. uv resolved langfuse 5.0.1. Constructor/start_observation/update/end signatures inspected locally. Do not use legacy ingestion endpoint or OpenAI auto instrumentation that would capture messages. SDK initialization does not enable this integration without explicit application settings.
