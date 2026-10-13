---
project: "Linksifty"
version: 2
status: approved-for-design
created: 2026-10-03
updated: 2026-10-11
context_type: greenfield
product_type: personal-web-app
target_scale:
  users: one
timeline_budget:
  mvp_weeks: 5
  hard_deadline: 2026-11-04
  after_hours_only: true
---

# Linksifty — Product Requirements

## Vision and problem

Implementation status is tracked in `docs/roadmap.md` and `docs/superpowers/plans/2026-10-13-linksifty-completion.md`. Requirements here describe the agreed target, not an assertion that every capability already runs. The current baseline has 37 mock-backed backend tests; live RLS, cleanup, job execution, model/cost controls and complete UI remain unfinished.

Filip has a backlog of unread saved links but not enough time to decide which deserve attention. Linksifty turns ordinary web links into source-grounded notes, an eight-criterion assessment, and a deterministic value verdict: **valuable**, **to review**, or **hype**.

The product is domain-agnostic. IT, AI, and finance are Filip's interests, not restrictions on accepted content. It is not a generic summarizer: its value is a transparent reading-priority decision, with visible support from the submitted source material.

## User and scope

The personal MVP has one user: Filip, authenticated with one normal account. Public signup, pending users, trials, role management, and administration are out of scope.

## Success criteria

### Primary

- Filip processes 20 real backlog links. Each reaches either a completed inbox result or an explicit request for manually pasted content.
- At least 60% of the twenty verdicts match Filip's own judgment.

### Secondary

- Submit, review, filter, mark-read, and deletion flows are comfortable on a phone.

### Guardrails

- A failed or incomplete fetch never produces a note, assessment, score, verdict, or chat-ready item.
- Every stored record remains scoped to the authenticated user ID.
- Paid processing stops at 10 USD per calendar month.
- Stored item data automatically expires 30 days after creation.

## User stories

### US-01: Triage a small batch

**Given** Filip is signed in,
**when** he submits up to five web links,
**then** each link is queued and eventually appears with a source-grounded note, assessment, score, and verdict, or waits for pasted content when the source cannot be used.

### US-02: Supply source material directly

**Given** Filip has content he wants assessed or a link whose content cannot be used,
**when** he chooses paste-content mode and supplies the text,
**then** Linksifty performs the same assessment flow without fetching a page.

### US-03: Understand and explore a result

**Given** an item has completed assessment,
**when** Filip opens it,
**then** he sees a note, supporting excerpts, eight score rationales, deterministic verdict, and can chat only about that source material.

## Functional requirements

### Submission and acquisition

- **FR-001:** The submission page accepts up to five URLs in one input and provides a direct choice between fetch-link and paste-content modes.
- **FR-002:** A generic web adapter fetches ordinary web pages and extracts usable text. A dedicated server-side X adapter retrieves X posts using the official X API.
- **FR-003:** Paywalls, login walls, JavaScript-only pages, PDFs, videos, newsletters, unsupported sources, and incomplete retrievals become `awaiting_manual_content`. They create no assessment.
- **FR-004:** A duplicate URL prompts Filip to choose whether to use the existing item or create a fresh assessment attempt.
- **FR-005:** The inbox always exposes truthful task state: `queued`, `processing`, `awaiting_manual_content`, `completed`, or `failed`.

### Assessment and verdict

- **FR-006:** A completed source produces a concise note whose important claims identify a quoted supporting excerpt and its location in the saved source content.
- **FR-007:** The assessment scores novelty, evidence, practicality, source credibility, replicability, independent corroboration, absence of conflict of interest, and concreteness versus superlatives from 1–5, each with a short rationale.
- **FR-008:** Assessment may inspect up to five cited sources. Independent corroboration counts distinct sources, not reposts.
- **FR-009:** The weighted score is deterministic: evidence, replicability, source credibility, and absence of conflict of interest have weight `×2`; the remaining four criteria have weight `×1`.
- **FR-010:** The default verdict thresholds are `≥60%` valuable, `40–59%` to review, and `<40%` hype. Every completed item stores its score, threshold snapshot, and verdict.
- **FR-011:** Filip can change the valuable threshold in Settings. The new threshold applies only to assessments created after the change; existing verdicts remain unchanged.

### Inbox, detail, and chat

- **FR-012:** The inbox is the default screen. It orders unread items before read items, then by descending score, and filters by verdict.
- **FR-013:** Filip can mark an item read or unread and can permanently delete it after confirmation.
- **FR-014:** The item detail displays the verdict using text plus supplemental color, the note, citations, criterion rationales, and task status where relevant.
- **FR-015:** Filip can open chat from a completed item's detail. Answers are grounded only in that item's saved content and citations; unsupported questions are declined.

### Cost, retention, and recovery

- **FR-016:** The application records paid processing cost and blocks new paid processing after 10 USD in the current calendar month.
- **FR-017:** A transient provider failure gets one safe retry. A permanent failure remains visible with a clear explanation.
- **FR-018:** Items, source content, citations, assessments, task records, and chat messages permanently expire after 30 days. Explicit deletion removes them sooner.
- **FR-019:** Tasks are durable. If the API process stops while work is queued or processing, the next authenticated application visit safely resumes claimable work rather than pretending it completed.

## Non-functional requirements

- The responsive web app supports current mainstream phone and desktop browsers.
- Semantic controls, keyboard access, visible focus, accessible names, and clear loading/error/disabled states are required.
- Scoring and verdict code is pure, deterministic, and has one source of truth.
- FastAPI routes own only transport concerns. Provider and database integrations remain at the edge; domain logic does not depend on them.
- External credentials are server-only and never committed. Remote/paid integrations are mocked in tests.

## Non-goals

- Public signup, trials, account approval, admin content access, sharing, or multi-user collaboration.
- Bookmark import, Telegram, topic categories, manual verdict override, automatic reassessment, or bring-your-own-key.
- Automatic fetching for Reddit, PDFs, video, podcasts, newsletters, or blocked/unsupported pages.
- Full-text inbox search, paid background workers, a dedicated analytics platform, System One/Jev classification, or research beyond the submitted source plus five cited sources.

## Open questions

- Select an X API plan and verify its post/thread access and cost before enabling real X retrieval.
- Select an OpenRouter model and verify structured-output behavior and actual unit cost before enabling paid calls.
