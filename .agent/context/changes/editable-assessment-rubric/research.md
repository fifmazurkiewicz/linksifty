# Verified implementation context

- Stack: React/TypeScript static frontend; FastAPI/Pydantic v2 API on Render;
  owner-scoped Supabase RPCs/PostgreSQL; opportunistic API worker and OpenRouter.
- `domain/models.py` owns CriterionName IDs/default weights; `domain/scoring.py`
  computes a normalized weighted percentage and a threshold-derived verdict.
- `SettingsPanel.tsx` edits only threshold. GET/PUT `/v1/settings` use
  ProcessingService and ProcessingRepository; current PUT ignores extra fields.
- `reserve_analysis` in migration 000005 locks settings, then the leased job,
  and records threshold in both the reservation and job before inference.
- Latest `claim_processing_job` and `complete_processing_job` are in 000007.
  Claim exposes cached result/research. Completion writes assessment and checks
  actual source citation offsets. Latest explicit resume is in 000008 and clears
  reservation/result/threshold only after rejecting uncertain-cost reservations
  and duplicate links.
- ProcessingService passes threshold into pure complete_assessment and builds
  AssessmentView. Repository detail reads assessment rows and research context;
  it does not recalculate results. OpenRouter currently receives fixed grounding
  instructions plus source text, with a full-context bounded cost reservation.
- Existing SQL integration gate requires explicit local disposable `_test` DB,
  psql and pgTAP and returns 77 when unavailable. Do not discover credentials or
  install a new runtime. It tests concurrent reservations and duplicate links.
- Existing tests cover default domain scoring, owner identity, threshold API,
  cached paid-result recovery, provider grounding, settings save and detail UI.
- Graft is unavailable; facts above were established with focused local reads.
