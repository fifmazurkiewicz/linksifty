# Linksifty Personal MVP Implementation Plan

> Scope update, 2026-10-18: the owner approved Jev only for the analysis-chat
> relevance/safety gate. That supersedes this historical plan's Jev exclusion;
> assessment scoring remains deterministic. See [current roadmap](../../roadmap.md).

**Current execution supplement (2026-10-13):** [completion plan](2026-10-13-linksifty-completion.md). It owns the remaining C1–C8 cards, concrete acceptance and evidence; this original plan remains the approved design breakdown. Demo code and mock tests do not constitute completion of Tasks 3–10.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `implementation` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the personal Linksifty MVP: authenticated submission of up to five sources, durable source-grounded assessments, inbox/detail/chat UI, and safe free-tier operation.

**Architecture:** This is a monorepo: `frontend/` contains the React/Vite browser app and `backend/` contains the FastAPI service. The browser app uses Supabase Auth and calls the API. FastAPI owns orchestration and server-only adapters, while pure Python domain code derives scores and verdicts. Supabase is the durable source of truth for user data and jobs; an awake API process opportunistically drains leased jobs, so no paid worker is required.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, `uv`, Supabase Auth/PostgreSQL/RLS, React, TypeScript, Vite, Vitest, Vercel, Render Free, OpenRouter, official X API.

**Spec:** [`docs/superpowers/specs/2026-10-11-linksifty-personal-mvp-design.md`](../specs/2026-10-11-linksifty-personal-mvp-design.md)

## Global Constraints

- `backend/` is the installable Python package, `frontend/` is the installable React/Vite package, and the root `pyproject.toml` is the uv workspace only.
- Python dependencies and all Python commands use `uv`; run backend commands from the root as `uv run --package linksifty …`. Never use `pip` or edit `uv.lock` by hand.
- The approved React/Vite frontend uses npm only inside `frontend/`, with a committed `package-lock.json`. This is the explicit frontend exception to the Python-only `uv` rule.
- Use FastAPI and Pydantic v2 APIs only; all Python functions have full annotations and strict mypy passes.
- Keep routes transport-only; domain scoring, verdicts, and completeness rules are deterministic and framework-free.
- Never create an assessment, summary, or chat-ready result from failed or partial acquisition.
- Scope every item, job, assessment, citation, note, and chat action to the authenticated user ID, even for the sole MVP account.
- Keep Supabase service-role, OpenRouter, and X credentials server-only; commit only example variable names.
- Store a threshold snapshot at assessment completion. Settings changes affect only future completed items.
- Delete source data and all dependent records after 30 days; an explicit user deletion is permanent.
- Remote and paid integrations are mocked in tests. Every implementation task runs its focused tests; the final gate also runs `uv run mypy src`, `uv run ruff check .`, `uv run ruff format --check .`, and `agent-toolkit check`.

## Review Focus

1. A login/paywall/JavaScript-only response must lead to `awaiting_manual_content`, never an assessment — Task 5.
2. Two API processes trying to resume one expired task must produce one active lease and no duplicate paid call — Task 4.
3. A user must receive `404` for another user's known item ID, even with a service-role-backed repository — Tasks 3 and 7.
4. A threshold change after completion must not change an existing verdict — Task 2 and Task 6.
5. A job that wakes after Render sleep must preserve the visible queue state and resume only after an authenticated request — Tasks 4 and 7.

---

## File map

| Area | Files | Responsibility |
| --- | --- | --- |
| API entry/config | `backend/src/linksifty/main.py`, `backend/src/linksifty/config.py` | App factory, dependency wiring, environment validation. |
| Domain | `backend/src/linksifty/domain/*.py` | Typed entities, source policy, deterministic score/verdict, task state transitions. |
| Application | `backend/src/linksifty/application/*.py` | Submission, manual-content replacement, job execution, chat orchestration. |
| Infrastructure | `backend/src/linksifty/infrastructure/*.py` | Supabase, HTTP extraction, X, OpenRouter, structured logging. |
| HTTP | `backend/src/linksifty/api/*.py` | Auth dependency and user-scoped request/response routes. |
| Schema | `supabase/migrations/20261011_000001_personal_mvp.sql` | Tables, indexes, RLS, atomic job-claim RPC, 30-day cleanup RPC. |
| Frontend | `frontend/src/*`, `frontend/tests/*` | Authenticated inbox, submission, detail/chat/settings and API client. |
| Tests | `backend/tests/unit/*`, `backend/tests/integration/*` | Pure behavior, application orchestration, HTTP contracts with fakes. |
| Delivery | `.github/workflows/ci.yml`, `.env.example`, `README.md` | Reproducible checks and deploy/configuration documentation. |

## Approved monorepo and UX-preview amendment — 2026-10-12

- Move the existing Python package and tests to `backend/`; make the root `pyproject.toml` a uv workspace and keep the shared `uv.lock` at the root.
- Create `frontend/` with npm-managed React, TypeScript, and Vite dependencies.
- Before Task 3, deliver a **Task 2.5 — UX preview**: a responsive, keyboard-accessible Inbox-first frontend with clearly labelled in-memory demo data. It must show a completed result and an `awaiting_manual_content` state, plus navigable Add and Settings screens. It makes no authenticated, provider, or API request.
- After Task 2.5, continue Tasks 3–10 unchanged in behavior but interpret every former `src/`, `tests/`, and `web/` path as `backend/src/`, `backend/tests/`, and `frontend/` respectively. Every former `uv run` command uses `uv run --package linksifty`; every frontend command uses `npm --prefix frontend`.

### Task 1: Establish the executable skeleton and configuration boundary

**Files:**
- Modify: `pyproject.toml`, `.env.example`, `src/linksifty/__init__.py`, `README.md`
- Create: `src/linksifty/main.py`, `src/linksifty/config.py`, `tests/unit/test_config.py`, `web/package.json`, `web/tsconfig.json`, `web/vite.config.ts`, `web/src/main.tsx`, `web/src/App.tsx`, `web/src/styles.css`, `web/index.html`

**Interfaces:**
- Produces `Settings` and `create_app(settings: Settings | None = None) -> FastAPI` for every later API task.
- Produces a minimal web application mount point for Tasks 8–10.

- [ ] **Step 1: Write failing configuration and health tests.**

```python
from fastapi.testclient import TestClient
from linksifty.config import Settings
from linksifty.main import create_app


def test_settings_rejects_missing_server_secret() -> None:
    assert Settings.model_validate({"supabase_url": "https://db.example"}).is_configured is False


def test_health_endpoint_needs_no_provider_call() -> None:
    client = TestClient(create_app(Settings.for_test()))
    assert client.get("/health").json() == {"status": "ok"}
```

- [ ] **Step 2: Run `uv run pytest tests/unit/test_config.py -v` and confirm it fails because `Settings` and `create_app` do not exist.**
- [ ] **Step 3: Implement a frozen configuration dataclass with server-only fields, a `from_environment()` constructor using the standard library, a `for_test()` constructor, and an app factory that exposes only `GET /health`.**

```python
@dataclass(frozen=True, slots=True)
class Settings:
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    openrouter_api_key: str | None = None
    x_api_bearer_token: str | None = None

    @property
    def is_configured(self) -> bool: ...

    @classmethod
    def for_test(cls) -> Self: ...
```

- [ ] **Step 4: Generate `.env.example` with empty names only: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENROUTER_API_KEY`, `X_API_BEARER_TOKEN`. Do not add a configuration dependency. Create the Vite/React/TypeScript skeleton and commit its lockfile.**
- [ ] **Step 5: Run `uv run pytest tests/unit/test_config.py -v`, `uv run mypy src`, `uv run ruff check .`, and `uv run ruff format --check .`; then commit `chore: add api and web application skeleton`.**

### Task 2: Implement pure source policy, scoring, and verdict contracts

**Files:**
- Create: `src/linksifty/domain/models.py`, `src/linksifty/domain/content_policy.py`, `src/linksifty/domain/scoring.py`, `tests/unit/test_content_policy.py`, `tests/unit/test_scoring.py`

**Interfaces:**
- Produces `ContentReadiness`, `AssessmentDraft`, `CompletedAssessment`, `Score`, `Verdict`, `evaluate_content(...)`, and `complete_assessment(...)`.
- Consumed by Task 5 acquisition and Task 6 assessment orchestration.

- [ ] **Step 1: Write failing pure-domain tests.**

```python
def test_incomplete_content_is_not_assessable() -> None:
    result = evaluate_content(text="Please log in to continue", fetched=True)
    assert result.status is ContentReadiness.AWAITING_MANUAL_CONTENT


def test_threshold_snapshot_is_used_for_historic_verdict() -> None:
    assessment = complete_assessment(draft_with_weighted_total(7.0), threshold=6.5)
    assert assessment.verdict is Verdict.VALUABLE
    assert assessment.threshold_snapshot == 6.5


def test_equal_score_is_to_review_not_hype() -> None:
    assert derive_verdict(score=6.5, threshold=6.5) is Verdict.VALUABLE
```

- [ ] **Step 2: Run `uv run pytest tests/unit/test_content_policy.py tests/unit/test_scoring.py -v` and confirm missing imports fail.**
- [ ] **Step 3: Define exactly eight `CriterionName` values and immutable Pydantic/domain dataclasses. Give evidence, replicability, source credibility, and conflict-of-interest weight `2`; give novelty, practicality, independent corroboration, and concreteness weight `1`. Require a non-empty citation reference for every criterion rationale.**

```python
def complete_assessment(draft: AssessmentDraft, threshold: float) -> CompletedAssessment:
    score = weighted_average(draft.criteria)
    return CompletedAssessment(
        note=draft.note,
        criteria=draft.criteria,
        score=score,
        verdict=derive_verdict(score, threshold),
        threshold_snapshot=threshold,
    )
```

- [ ] **Step 4: Implement explicit incomplete-content reasons (`blocked`, `paywalled`, `login_required`, `script_only`, `unsupported`, `too_short`) and ensure no `AssessmentDraft` can be constructed from a non-ready result.**
- [ ] **Step 5: Run focused tests, then `uv run mypy src` and Ruff checks; commit `feat: add deterministic assessment domain`.**

### Task 3: Add the Supabase schema, RLS, and user-scoped repository

**Files:**
- Create: `supabase/migrations/20261011_000001_personal_mvp.sql`, `src/linksifty/infrastructure/supabase_repository.py`, `src/linksifty/application/ports.py`, `tests/unit/test_repository_contract.py`, `docs/deployment/supabase.md`

**Interfaces:**
- Produces protocol `LinksiftyRepository` with `create_items`, `get_item(user_id, item_id)`, `list_items(user_id, verdict)`, `replace_manual_content`, `save_completed_assessment`, and `delete_item`.
- Produces concrete `SupabaseRepository`; Tasks 4–7 depend only on the protocol.

- [ ] **Step 1: Write repository-contract tests against an in-memory fake, including ownership denial.**

```python
def test_get_item_does_not_cross_user_boundary(repository: LinksiftyRepository) -> None:
    item = repository.create_items(USER_A, [new_submission()])[0]
    assert repository.get_item(USER_B, item.id) is None
```

- [ ] **Step 2: Run `uv run pytest tests/unit/test_repository_contract.py -v` and confirm the port/fake are absent.**
- [ ] **Step 3: Create the migration with `settings`, `items`, `source_contents`, `jobs`, `assessments`, `citations`, and `chat_messages`; add `user_id uuid not null references auth.users(id)`, foreign keys, status/check constraints, `expires_at`, and indexes on `(user_id, created_at desc)` and claimable jobs. Enable RLS on each user-data table and create `select`, `insert`, `update`, and `delete` policies using `auth.uid() = user_id`.**
- [ ] **Step 4: Implement the protocol and `SupabaseRepository` so every public repository method takes `user_id` and includes it in the query predicate. Use a service-role client only in server infrastructure; browser access uses the anon key plus the user session and therefore remains RLS-bound.**
- [ ] **Step 5: Document migration application and an SQL verification query that attempts a cross-user select under two JWT identities. Run focused tests and commit `feat: add user-scoped Supabase persistence`.**

### Task 4: Implement durable job leasing, retry, and expiry cleanup

**Files:**
- Create: `src/linksifty/domain/jobs.py`, `src/linksifty/application/job_runner.py`, `tests/unit/test_jobs.py`, `tests/unit/test_job_runner.py`
- Modify: `supabase/migrations/20261011_000001_personal_mvp.sql`, `src/linksifty/application/ports.py`, `src/linksifty/infrastructure/supabase_repository.py`

**Interfaces:**
- Produces `JobStatus`, `claim_next_job(user_id, now)`, `release_or_fail(job, error)`, and `JobRunner.drain_for_user(user_id, limit=2)`.
- Consumed by Task 7 after a successful authenticated submission or foreground request.

- [ ] **Step 1: Write failing lease-state tests.**

```python
def test_only_one_claimant_receives_a_queued_job() -> None:
    first, second = repository.claim_twice_same_timestamp(USER_A)
    assert first is not None
    assert second is None


def test_expired_processing_lease_can_be_reclaimed() -> None:
    job = processing_job(lease_expires_at=NOW - timedelta(seconds=1))
    assert transition_claim(job, NOW).status is JobStatus.PROCESSING


def test_second_transient_failure_is_terminal() -> None:
    assert release_or_fail(job_with_attempts(1), transient_error()).status is JobStatus.FAILED
```

- [ ] **Step 2: Run `uv run pytest tests/unit/test_jobs.py tests/unit/test_job_runner.py -v` and confirm it fails.**
- [ ] **Step 3: Add an atomic `claim_next_job(p_user_id uuid, p_now timestamptz)` SQL function that updates one `queued` or expired `processing` job with a random lease token and finite lease expiry, returning that exact row. Keep job attempts and error codes in the same transaction.**
- [ ] **Step 4: Implement `JobRunner` with an injected clock and executor. It claims at most two jobs per authenticated request, never processes a job owned by another user, returns incomplete content to `awaiting_manual_content`, and makes only one retryable external attempt. Add a `delete_expired_records(p_now)` RPC that deletes items with `expires_at <= p_now`, relying on cascading foreign keys.**
- [ ] **Step 5: Run focused tests and static checks; commit `feat: add durable job leasing and retry policy`.**

### Task 5: Implement source acquisition adapters and safe fallbacks

**Files:**
- Create: `src/linksifty/infrastructure/http_fetcher.py`, `src/linksifty/infrastructure/text_extractor.py`, `src/linksifty/infrastructure/x_adapter.py`, `tests/unit/test_http_fetcher.py`, `tests/unit/test_text_extractor.py`, `tests/unit/test_x_adapter.py`
- Modify: `src/linksifty/application/ports.py`, `src/linksifty/application/job_runner.py`

**Interfaces:**
- Produces `SourceAcquirer.acquire(submission) -> AcquiredSource | AcquisitionFailure`.
- Generic HTTP and X adapters are selected by normalized source kind; later Tasks never call an adapter directly.

- [ ] **Step 1: Write failing adapter tests using `httpx.MockTransport`.**

```python
def test_login_html_requires_manual_content() -> None:
    result = acquirer.acquire(fetch_submission("https://example.test/article"))
    assert result.readiness is ContentReadiness.AWAITING_MANUAL_CONTENT
    assert result.reason is IncompleteReason.LOGIN_REQUIRED


def test_x_urls_use_official_adapter() -> None:
    acquirer.acquire(fetch_submission("https://x.com/user/status/1"))
    assert fake_x_adapter.calls == ["1"]
```

- [ ] **Step 2: Run `uv run pytest tests/unit/test_http_fetcher.py tests/unit/test_text_extractor.py tests/unit/test_x_adapter.py -v` and confirm missing adapter imports fail.**
- [ ] **Step 3: Implement URL normalization that permits only `http` and `https`, rejects localhost, private/link-local/reserved IP addresses and redirects to them, caps redirect count, response bytes, and fetch timeout. Use an `httpx.AsyncClient` with injected transport in tests.**
- [ ] **Step 4: Extract readable text with the standard-library `HTMLParser`; detect common paywall/login markers and return `too_short` below the agreed minimum. Do not add a browser scraper. The X adapter receives a post ID through the official client abstraction only and returns the same `AcquiredSource` contract.**
- [ ] **Step 5: Run focused tests and quality checks; commit `feat: add safe source acquisition adapters`.**

### Task 6: Implement assessment, citations, budget, and grounded chat services

**Files:**
- Create: `src/linksifty/application/assessment_service.py`, `src/linksifty/application/chat_service.py`, `src/linksifty/infrastructure/openrouter_client.py`, `tests/unit/test_assessment_service.py`, `tests/unit/test_chat_service.py`
- Modify: `src/linksifty/application/ports.py`, `src/linksifty/application/job_runner.py`

**Interfaces:**
- Produces `AssessmentService.assess(item, source, threshold) -> CompletedAssessment` and `ChatService.reply(user_id, item_id, message) -> ChatReply`.
- Requires an `OpenRouterClient` port that returns Pydantic-validated structured DTOs; the deterministic scorer stays in Task 2.

- [ ] **Step 1: Write failing service tests with a fake provider.**

```python
def test_assessment_snapshots_current_threshold() -> None:
    result = service.assess(item, ready_source(), threshold=6.5)
    assert result.threshold_snapshot == 6.5
    assert result.verdict is Verdict.VALUABLE


def test_chat_rejects_uncited_provider_answer() -> None:
    provider.reply_value = ProviderChatReply(text="claim", citation_ids=[])
    with pytest.raises(UngroundedAnswerError):
        chat.reply(USER_A, ITEM_ID, "Why?")
```

- [ ] **Step 2: Run `uv run pytest tests/unit/test_assessment_service.py tests/unit/test_chat_service.py -v` and confirm absence of services.**
- [ ] **Step 3: Define strict Pydantic response schemas: a note, exactly eight criteria, one-or-more citation excerpts with start/end positions for material claims, and provider metadata. Validate citation bounds against stored content. Let `complete_assessment` alone calculate score and verdict.**
- [ ] **Step 4: Before a paid call, atomically verify the user's current-month cost plus conservative request allowance stays within 10 USD. Persist actual provider cost and reject excess work with a visible budget error. Chat receives only stored content plus stored citation excerpts and rejects responses without valid citation IDs.**
- [ ] **Step 5: Run focused tests, type/lint checks, and commit `feat: add evidence-bound assessment and chat services`.**

### Task 7: Expose authenticated FastAPI routes and trigger bounded processing

**Files:**
- Create: `src/linksifty/api/auth.py`, `src/linksifty/api/schemas.py`, `src/linksifty/api/routes/items.py`, `src/linksifty/api/routes/settings.py`, `src/linksifty/api/routes/chat.py`, `tests/integration/test_items_api.py`, `tests/integration/test_settings_api.py`, `tests/integration/test_chat_api.py`
- Modify: `src/linksifty/main.py`

**Interfaces:**
- Produces `/v1/items`, `/v1/items/{item_id}`, `/v1/items/{item_id}/content`, `/v1/items/{item_id}/chat`, and `/v1/settings` JSON APIs.
- Browser receives status payloads only; no route returns a secret or raw provider response.

- [ ] **Step 1: Write FastAPI contract tests with an injected fake auth service and repository.**

```python
def test_submit_accepts_at_most_five_sources(client: TestClient) -> None:
    response = client.post("/v1/items", json={"sources": [source_payload()] * 6})
    assert response.status_code == 422


def test_detail_of_another_users_item_is_not_found(client: TestClient) -> None:
    response = client.get(f"/v1/items/{OTHER_USERS_ITEM}")
    assert response.status_code == 404
```

- [ ] **Step 2: Run `uv run pytest tests/integration/test_items_api.py tests/integration/test_settings_api.py tests/integration/test_chat_api.py -v` and confirm missing routes fail.**
- [ ] **Step 3: Add a bearer-token dependency that resolves a user ID through Supabase Auth. Map domain errors to stable `400`, `401`, `404`, `409`, `422`, and `429` responses. The submit route persists accepted sources/jobs first, returns them as `queued`, and schedules only `JobRunner.drain_for_user(user_id, limit=2)` after the response.**
- [ ] **Step 4: Implement paginated inbox response ordered `unread_at is not null` then score descending, verdict filtering, explicit read marking, manual-content replacement, confirmed deletion endpoint, future-only threshold update, and item-bound chat. Keep all route functions thin and call application services.**
- [ ] **Step 5: Run all API tests, `uv run mypy src`, Ruff checks, then commit `feat: expose authenticated Linksifty API`.**

### Task 8: Build the authenticated web shell, inbox, and submission screen

**Files:**
- Create: `web/src/lib/api.ts`, `web/src/lib/supabase.ts`, `web/src/components/AppShell.tsx`, `web/src/components/StatusBadge.tsx`, `web/src/features/auth/*`, `web/src/features/inbox/*`, `web/src/features/submit/*`, `web/tests/inbox.test.tsx`, `web/tests/submit.test.tsx`
- Modify: `web/src/App.tsx`, `web/src/styles.css`, `web/package.json`

**Interfaces:**
- Consumes the API schemas from Task 7 and Supabase browser session.
- Produces the Inbox-first UX and an accessible Add flow.

- [ ] **Step 1: Write Vitest/Testing Library tests.**

```tsx
it("renders an explicit queued state and verdict text", () => {
  render(<Inbox items={[queuedItem(), completedValuableItem()]} />);
  expect(screen.getByText("Queued")).toBeVisible();
  expect(screen.getByText("Valuable")).toBeVisible();
});

it("disables submit for a sixth URL", async () => {
  render(<SubmitSources />);
  await userEvent.type(screen.getByLabelText("Links"), sixUrls());
  expect(screen.getByRole("button", { name: "Submit links" })).toBeDisabled();
});
```

- [ ] **Step 2: Run `npm --prefix web test -- --run tests/inbox.test.tsx tests/submit.test.tsx` and confirm it fails before components exist.**
- [ ] **Step 3: Implement session restoration/login, a three-item keyboard-accessible navigation (`Inbox`, `Add`, `Settings`), and an Inbox route as the default. Render text labels for every status and verdict, with color as supplementary only. Sort and filter server results; include loading, empty, and API-error states.**
- [ ] **Step 4: Implement one large source textarea, parse one URL per line, support up to five sources, expose per-source fetch/paste mode, and post valid batch entries. For duplicate conflicts, present a user choice and resend the selected action explicitly.**
- [ ] **Step 5: Run frontend tests and production build, then commit `feat: add inbox and source submission UI`.**

### Task 9: Build item detail, manual-content recovery, chat, and settings

**Files:**
- Create: `web/src/features/item-detail/*`, `web/src/features/chat/*`, `web/src/features/settings/*`, `web/tests/item-detail.test.tsx`, `web/tests/settings.test.tsx`
- Modify: `web/src/App.tsx`, `web/src/lib/api.ts`, `web/src/styles.css`

**Interfaces:**
- Consumes item detail, manual-content, chat, and settings endpoints from Task 7.
- Produces complete recovery and explanation UI specified in the PRD.

- [ ] **Step 1: Write UI tests for recovery and historic verdict copy.**

```tsx
it("asks for pasted content when fetch is incomplete", () => {
  render(<ItemDetail item={awaitingManualContentItem()} />);
  expect(screen.getByRole("heading", { name: "Paste content to continue" })).toBeVisible();
  expect(screen.queryByText("Assessment")).not.toBeInTheDocument();
});

it("labels a setting change as future-only", () => {
  render(<Settings />);
  expect(screen.getByText(/future assessments only/i)).toBeVisible();
});
```

- [ ] **Step 2: Run `npm --prefix web test -- --run tests/item-detail.test.tsx tests/settings.test.tsx` and confirm it fails before features exist.**
- [ ] **Step 3: Implement detail states for queued/processing/failed/manual content/completed; show short note, score, eight criteria, citations with excerpts and positions, and a delete confirmation. Do not render an assessment section in non-completed states.**
- [ ] **Step 4: Implement item-scoped chat with submitted-message pending state, cited-answer rendering, and clear refusal/error state. Add settings for threshold, monthly budget display, 30-day expiry policy, and logout; label threshold impact as applying only to future assessments.**
- [ ] **Step 5: Run frontend tests and build, then commit `feat: add detail recovery chat and settings UI`.**

### Task 10: Add delivery safeguards, observability, and release evidence

**Files:**
- Create: `.github/workflows/ci.yml`, `tests/integration/test_end_to_end_workflow.py`, `docs/deployment/render.md`, `docs/deployment/vercel.md`, `docs/release/20-link-evaluation.md`, `.agent/context/changes/linksifty-personal-mvp/evidence.md`
- Modify: `README.md`, `.agent/context/changes/linksifty-personal-mvp/progress.md`, `docs/roadmap.md`, `docs/roadmap-kanban.html`

**Interfaces:**
- Produces repeatable quality gates and the evidence template required for the 20-link acceptance evaluation.

- [ ] **Step 1: Write an end-to-end application test entirely with fakes.**

```python
def test_submitted_complete_source_reaches_completed_with_citations() -> None:
    item = workflow.submit(USER_A, [pasted_source("evidence-rich text")])[0]
    workflow.drain(USER_A)
    completed = workflow.get_item(USER_A, item.id)
    assert completed.status is ItemStatus.COMPLETED
    assert len(completed.assessment.criteria) == 8
    assert completed.assessment.citations
```

- [ ] **Step 2: Run `uv run pytest tests/integration/test_end_to_end_workflow.py -v` and confirm it fails before all prior behavior is wired.**
- [ ] **Step 3: Add structured JSON logs for request ID, user/item/job IDs, status transitions, adapter category, retry, provider cost, and budget rejection. Explicitly exclude source bodies, bearer tokens, and secrets. Add GitHub Actions jobs for Python tests/mypy/Ruff/format/agent-toolkit and the frontend test/build.**
- [ ] **Step 4: Document Vercel and Render environment-variable setup without values, Supabase migration/RLS validation, Render cold-start behavior, and a 20-row evaluation sheet whose accepted outcome is a result or manual-content request for every item and at least 12/20 verdicts judged acceptable. Update the roadmap/progress/derived Kanban with implementation status.**
- [ ] **Step 5: Run `uv run pytest`, `uv run mypy src`, `uv run ruff check .`, `uv run ruff format --check .`, `agent-toolkit check`, `npm --prefix web test -- --run`, and `npm --prefix web run build`; record exact outcomes and any unavailable manual checks in `evidence.md`. Commit `chore: add delivery validation and release evidence`.**

## Plan self-review

### Spec coverage

- Personal, domain-agnostic source submissions, batch size, and paste/fetch choice: Tasks 5, 7, and 8.
- No assessment after partial fetch: Tasks 2, 4, 5, 7, and 9.
- Eight criteria, citations, deterministic score/verdict, and historic threshold snapshot: Tasks 2 and 6.
- User scope, RLS, deletion, and 30-day retention: Tasks 3, 4, 7, and 10.
- Free-tier durable work without a dedicated worker: Tasks 3, 4, and 7.
- Inbox, detail, manual recovery, chat, settings, accessibility: Tasks 8 and 9.
- Generic web adapter, official X seam, OpenRouter budget/schema boundary: Tasks 5 and 6.
- CI, quality checks, structured logs, and 20-link evaluation: Task 10.
- System One/Jev remains excluded: Global Constraints and Task 6 use only the OpenRouter port plus deterministic scorer.

### Placeholder scan

The plan contains no deferred implementation markers or undefined interfaces. The two external activation choices are intentionally configuration gates: X API plan and OpenRouter model/cost, already identified in the approved specification.

### Type consistency

`CompletedAssessment` is produced in Task 2 and consumed in Tasks 3, 6, 7, 9, and 10. `LinksiftyRepository` is introduced in Task 3 and used only through its user-ID-scoped methods thereafter. `JobRunner.drain_for_user` is introduced in Task 4 and scheduled by Task 7.

### Review-focus coverage

Each review-focus condition is assigned to focused unit or integration tests in its owning task, including inaccessible content, lease contention, user isolation, threshold immutability, and restart-resumable job state.

## Execution notes

This plan intentionally starts with the domain rules and fake-backed contracts before adding Supabase or paid-provider calls. Real Supabase setup, Vercel/Render deployment, X credential provisioning, OpenRouter model choice, and the 20 real-link evaluation require Filip's external access and must not be simulated as complete.
