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
