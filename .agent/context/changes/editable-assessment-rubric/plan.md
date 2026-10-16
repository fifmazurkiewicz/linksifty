# Editable Assessment Rubric Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. In this harness use the available implementation skill for native execution; do not invent unavailable tools or delegate without the selected execution method. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Let each account edit descriptions and weights for the eight existing criteria, with consistent model/scoring snapshots and inspectable historical rules.

**Architecture:** Extend the existing settings/processing boundary. An atomic owner-scoped PostgreSQL reservation selects a rubric snapshot; the provider and pure scorer consume that same snapshot. React edits returned settings and displays saved assessment snapshots.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, PostgreSQL/Supabase RPC/RLS, React/TypeScript, existing Langfuse/OpenRouter adapters; no new runtime dependency.

**Spec:** [Approved design](design.md). User approved the written specification on 2026-10-16. User approved this plan and native execution on 2026-10-16.

## Global Constraints

- Eight fixed criterion IDs and names; adding, removing or renaming is excluded.
- Each description is 1–1000 nonblank characters with no NUL; weights are strict integers 1–10.
- Preserve all grounding, completeness, source ownership, citation, budget and corroboration safeguards.
- Settings belong only to the authenticated account, including admins.
- Snapshot at first model reservation; historical and already-reserved analyses keep original rules.
- Preserve future-only threshold behavior, guarded explicit reset and no implicit paid retry.
- Use English UI labels/default descriptions; permit user descriptions in other languages.
- Python commands use `uv run --package linksifty`; npm only in frontend; no new dependencies or environments.
- Full type annotations and strict mypy; no FastAPI/database/provider imports in domain scoring.
- All diagrams must be authored in English.
- No hosted mutation, paid provider call, push or deployment is part of local implementation.

## Review Focus

1. A settings save races a model reservation: threshold and rubric must come from one consistent locked settings row (Task 2 SQL test).
2. Cached or interrupted jobs are resumed after settings edits: scoring must use the original rubric, and no second model request may be sent (Tasks 2/3).
3. Old API omits rubric or GET fails: the UI must disable saving rather than overwrite settings using guessed defaults (Task 4).
4. Rubric input has duplicates, missing IDs, zero/fractional/bool weights, whitespace-only/NUL descriptions: reject atomically at API and SQL boundaries (Tasks 1/2/4).
5. Edited description asks the model to ignore evidence checks: fixed grounding and post-response citation/corroboration validation remain effective (Task 3).

## Files and responsibilities

- Create `backend/src/linksifty/domain/rubric.py`: pure immutable rubric entries/catalog/validation, using CriterionName from existing models.
- Modify `domain/scoring.py`: optional explicit rubric argument with legacy default; no mutable global rules.
- Modify `application/processing_contracts.py`: validated rubric transport/snapshot types; settings/provider/store boundaries.
- Modify `application/processing_service.py`, `infrastructure/processing_repository.py`, `api/processing.py`, `infrastructure/openrouter_client.py`: atomic settings update and propagation of reserved rubric into input/scoring/output.
- Create `supabase/migrations/20261016_000009_assessment_rubric.sql`: validation/defaults, storage, backfill, updated reservation/claim/completion/reset RPCs and grants.
- Create `supabase/tests/assessment_rubric.test.sql`; extend `backend/tests/integration/check_processing_database.py` with this suite and reservation/settings concurrency case.
- Extend unit tests in `test_scoring.py`, `test_processing_api.py`, `test_processing_repository.py`, `test_processing_service.py`, `test_openrouter.py`; create `test_rubric.py` for rule validation/default/migration equivalence.
- Modify frontend `lib/api.ts` and shared `lib/rubric.ts`, `features/settings/SettingsPanel.tsx`, `features/queue/AssessmentDetail.tsx`, `App.css` and their behavior tests.
- Update `docs/product/vision.md`, `docs/deployment/setup.md`, `README.md`, architecture editable source/HTML and derived progress boards.

## Task 1 — Validated rubric and pure scoring

**Interfaces:** Domain `RubricCriterion(name: CriterionName, description: str, weight: int)` and `AssessmentRubric(criteria: tuple[RubricCriterion, ...])`, both frozen dataclasses. `default_rubric() -> AssessmentRubric`. Transport `RubricEntry`/`RubricConfig` mirror those fields with `.to_domain() -> AssessmentRubric`; default transport rubric is generated from the domain catalog. Snapshot shape is `{"criteria": [...]}`.

- [x] Write failing tests in `test_rubric.py` requiring exactly eight unique IDs and validated descriptions/weights. Exercise all invalid inputs in Review Focus 4, unknown IDs, bounds 1/10, description bounds, immutable independent defaults and canonical ordering.

```python
with pytest.raises(ValueError):
    RubricCriterion(CriterionName.NOVELTY, "   ", 1)
with pytest.raises(ValueError):
    RubricCriterion(CriterionName.NOVELTY, "New information", True)
```

- [x] Write a failing mixed-score test in `test_scoring.py`: novelty=5 and other seven scores=1; default weights yield 26.67%, novelty weight=10 yields 58.10%. A saved first result must remain 26.67% after constructing changed rules.

```python
assert complete_assessment(draft, 60).score == 26.67
assert complete_assessment(draft, 60, rubric=custom).score == 58.10
```

- [x] Run `uv run --package linksifty pytest backend/tests/unit/test_rubric.py backend/tests/unit/test_scoring.py -q` and record red.
- [x] Implement the two frozen domain types. Validate each integer with `type(weight) is int`, 1–10, nonblank/NUL-free description, exact eight ID set/length. Strip description edges, preserve internal text. Defaults describe each existing criterion without changing meaning; weight defaults use `CriterionName.weight`.
- [x] Implement keyword-only `rubric: AssessmentRubric | None = None` on `weighted_score` and `complete_assessment`. Resolve defaults once, index weights by criterion ID, use `round(sum(score * weight) / (5 * sum(weights)) * 100, 2)`. Preserve current result structure/verdict boundaries.
- [x] Add shared Pydantic DTO validation and `rubric: RubricConfig` to UserSettings. Add `rubric_snapshot` to ProcessingJob, Reservation and AssessmentView with legacy-default handling; invalid present data must fail instead of silently defaulting.
- [x] Run the focused tests green; deliberately restore fixed scoring once, verify mixed-score regression fails, then restore implementation. Record evidence.

## Task 2 — Atomic settings and durable snapshots

**Interfaces:** `ProcessingStore.update_settings(user_id: UUID, threshold: Decimal, rubric: RubricConfig | None) -> UserSettings`; service mirrors it. New RPC `update_user_assessment_settings(p_user_id uuid, p_threshold numeric, p_rubric jsonb default null)` returns owner settings; null rubric preserves existing rules. Existing GET/PUT paths remain.

- [x] Add API/repository failing tests for full rubric save, authenticated owner passed instead of supplied ID, atomic failure, malformed rubric rejection, threshold-only compatibility, and no worker/provider wake on save. New settings update model uses `extra="forbid"`; unknown owner fields receive 422 rather than the previous ignored-extra behavior.
- [x] Run `uv run --package linksifty pytest backend/tests/unit/test_processing_api.py backend/tests/unit/test_processing_repository.py -q` and record red.
- [x] Create forward migration 000009 with a deterministic default JSON function, a total JSON validation function and constrained `rubric`/`rubric_snapshot` columns on settings/jobs/usage_reservations/assessments. SQL validates types before array/object operations; requires eight exact IDs, weight numeric integral 1–10 (not bool), trimmed nonempty description ≤1000 characters/no NUL. Defaults must match the domain catalog; test equivalence with parsed migration fixture. Backfill completed assessments and reserved jobs/reservations with original defaults, leaving unreserved job snapshot null.
- [x] Implement owner-scoped settings RPC: initialize existing settings, lock/update one row; validate threshold/rubric before one update; preserve rubric if omitted. Keep existing monthly-budget and threshold RPC compatibility. Revoke public/anon/authenticated execution and grant service_role only for new/replaced RPCs; retain existing RLS.
- [x] Replace `reserve_analysis` preserving existing settings→job lock order, costs, lease fencing and duplicate reservation handling. In one transaction select `coalesce(job.rubric_snapshot, settings.rubric)` and threshold, storing both on reservation/job before returning. Brave reservations must not select or overwrite analysis rules.
- [x] Replace latest claim return shape to include job rubric snapshot; restore grants after drop/recreate. Completion must persist the authoritative job snapshot rather than trust a submitted replacement, while preserving all existing citation/source/settlement validation.
- [x] Replace the 000008 guarded explicit resume so it clears rubric snapshot only together with reservation/result/threshold reset; preserve duplicate guards and refusal to reset uncertain charges. Automatic recovery never clears the snapshot.
- [x] Audit the existing `paste_item_content` reset: an awaiting-manual-content job has no paid model attempt. Keep threshold/rubric reset consistent for that path and test that newly pasted complete content takes current rules at first reservation. Never discard an uncertain reservation as part of rubric support.
- [x] Add pgTAP tests with two synthetic accounts and transaction rollback for owner isolation, invalid no-partial-save, default backfill, reserved snapshot persistence, explicit reset, grants, lease rejection and source/citation behavior. Extend local DB gate to run it. Add concurrent settings-update/reservation test asserting each reservation gets either the whole old pair or whole new threshold/rubric pair, never a mixture.
- [x] Wire API/service/repository interfaces and strict response parsing. Use existing storage failure handling; do not turn missing migration/data into silently accepted defaults for new saves.
- [x] Run focused tests and the explicit local SQL gate. If local runtime is unavailable, record exit 77 as unavailable, preserve migration/tests and disclose database verification as an open gate. Never inspect production credentials or install tools to manufacture a passing check.

## Task 3 — Consistent model input, scoring and history

**Interfaces:** `AssessmentProvider.assess(text: str, *, sources: list[EvidenceSource] | None = None, rubric: RubricConfig | None = None) -> ModelResult`. Optional rubric defaults support existing direct adapter callers; production ProcessingService always supplies reserved snapshot explicitly. `AssessmentView.rubric_snapshot` is independent of current account settings.

- [x] Add failing service test: store returns reservation A, settings later become B; assert provider receives A and `store.complete` score/snapshot reflect A. Add cached-result recovery test that uses A and never calls `provider.assess` or reads current rules.

```python
provider.assess.assert_awaited_once_with(text, rubric=reserved_rules)
assert store.complete.call_args.args[1].rubric_snapshot == reserved_rules
```

- [x] Add mocked OpenRouter request test inspecting posted messages: edited descriptions/weights for all fixed IDs are present in a dedicated rubric message, not source passages; source IDs/text unchanged. Mock a response following a malicious description with an invented quote; it must still fail `invalid_citation` and account for one paid response without retry.
- [x] Run focused service/provider tests red, then propagate reservation snapshot onto job before inference; cached jobs use persisted/default legacy snapshot. Convert it to a pure domain rubric for `complete_assessment`; attach its transport snapshot to AssessmentView and preserve original rules in repository detail reads.
- [x] Add bounded rubric data separately from source content in model input, explicitly identifying it as criterion guidance subordinate to grounding/schema requirements. Preserve original 8-criterion schema, provider caps/known-model guard, source completeness, exact citation anchoring, cost settlement and independent-corroboration score clamp.
- [x] Update mocks/protocol implementations and tests affected by the extra keyword argument. Langfuse's existing redacted input/output path records the actual rubric; no user/account IDs or new blanket logging.
- [x] Run domain, processing, repository, research, OpenRouter, excerpt and telemetry suites. Deliberately substitute current/default rubric once and verify custom-score/recovery regression turns red, then restore.

## Task 4 — Settings editor and historical rule display

**Interfaces:** frontend `RubricEntry = {name: string; description: string; weight: number}`; `RubricConfig = {criteria: RubricEntry[]}`; settings response `{valuable_threshold: string | number; rubric: RubricConfig}`; assessment includes `rubric_snapshot: RubricConfig`. Frontend validates fixed ID membership/uniqueness and bounds before enabling save, without duplicating authoritative default descriptions/weights.

- [x] Extend `settings-usage.test.tsx` with a complete API fixture, requiring eight named fieldsets with labelled description/weight inputs. Edit description+weight+threshold and inspect the one authenticated PUT body; verify confirmation, load failure/old response disablement, invalid 0/11/fractional/blank values, duplicate IDs and preserved edits after rejected PUT. Existing expiry handling remains.
- [x] Extend assessment behavior test: save custom snapshot A, render detail while settings differ, and assert historical description/weight from A are visible beside that criterion's score. Existing legacy fixtures can omit snapshot only when compatibility behavior explicitly supplies default rules from backend.
- [x] Run `npm test -- --run tests/settings-usage.test.tsx tests/assessment.test.tsx` in frontend and record red.
- [x] Implement loaded state separate from editable draft/saved snapshot in SettingsPanel; AbortController/session changes invalidate old responses. Render fixed labels, description textareas (maxLength 1000), numeric integer weights min 1/max 10/step 1 and clear validation hints. Disable duplicate save while busy and when unchanged/invalid/unloaded; preserve form on error; normalize saved response only after successful complete response validation.
- [x] Explain point scale 1–5, relative weights and normalized formula. Use one Save settings button with threshold and rubric payload. Do not call model/provider or launch jobs. Render rules read-only in historical assessment detail using the returned snapshot and safe text rendering.
- [x] Use existing theme tokens and semantic fieldset/legend/labels; add only scoped CSS for vertical spacing, compact weights, readable textarea height and mobile stacking. Avoid existing global article/right-align rules for the form. Do not add libraries.
- [x] Run frontend tests/lint/build green. Deliberately omit rubric from PUT once, verify submitted-value test fails, then restore. Browser-check loaded mocked settings at desktop/mobile in light/dark mode and keyboard traversal; never use real credentials to build the test fixture.

## Task 5 — Diagrams, documentation and final verification

- [x] Use Archify skill to update `docs/architecture/current.architecture.json` and validated HTML, showing owner settings → atomic reservation snapshot → model rubric + deterministic scorer → stored historical snapshot. Preserve established source acquisition, citation, budget and recovery boundaries; all diagram text English. Record rendering limitation if unavailable.
- [x] Update product vision (fixed eight IDs, editable owner descriptions/weights), README settings behavior, and deployment guide (000009, matching backend/frontend, defaults/backfill, future-only semantics and no automatic reassessment). Document coordinated rollout: avoid mixed old/new workers when enabling custom rubrics, apply migration, deploy backend then frontend and verify capabilities before editing. Do not execute hosted steps.
- [x] Run backend relevant/full unit tests and strict mypy/Ruff, frontend tests/lint/build and toolkit check. Run explicit local SQL gate if configured. Capture exact results in evidence.md and refresh progress before derived board. Existing known warnings are not failures; unavailable gates are not passes.

```sh
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty pytest backend/tests/unit -q
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty mypy --strict backend/src
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty ruff check .
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty ruff format --check .
UV_CACHE_DIR=/private/tmp/linksifty-uv-cache uv run --package linksifty python backend/tests/integration/check_processing_database.py
```

Frontend working directory: `npm test -- --run`, `npm run lint`, `npm run build`.
Toolkit: use existing `agent-toolkit check`; if absent from PATH use the already
verified toolkit checkout runtime without installation, as recorded in earlier
change evidence. Run `git diff --check`.

Known existing toolkit runtime (read-only invocation, no installation):

```sh
/Users/Filip/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/agent-toolkit/.venv/bin/python -m agent_toolkit --project /Users/Filip/dev/linksifty check
```

- [x] Apply implementation-review skill and record findings with canonical dispositions in reviews/review-decisions.md before any derived review board. No Skip without human acceptance. Update roadmap/progress evidence without claiming hosted readiness. Commit only task files if authorized; push/deployment requires explicit user request.

## Automated versus manual gates

Automated local work: source/tests/migration/documentation edits, mocked provider
tests, pure score checks, owner RPC tests in explicitly configured disposable DB,
type/lint/build/toolkit checks, architecture generation and local browser QA.

Human/external work: review this plan and choose execution method; authorize
hosted migration/deploy/push separately; optionally authorize a paid acceptance
analysis after deploy. Do not ask for secrets or inspect environment files.

## Self-review

Spec mapping: fixed criteria/editor (Tasks 1/4), atomic account settings (2), model
guidance and unchanged safeguards (3), historic/resume snapshots (2/3/4), delivery
and verification (5). Review Focus cases each have an owning test above. All new
types and interfaces are defined before consumers. No new provider, worker,
framework or dependency is introduced. Database verification may remain external
if the explicit disposable runtime is absent; this is a stated delivery limit.


## Completion evidence

All local tasks complete; see [evidence.md](evidence.md) and
[implementation review](reviews/implementation-review.md). The native workflow
kept implementation local. Hosted migration/deployment and push are not claimed.
The diagram cites the immutable local product-source commit; its visual browser
gates pass without claiming a separate perceptual diagram review.
