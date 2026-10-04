---
project: LinkSift
version: 1
status: draft
created: 2026-10-04
updated: 2026-10-04
prd_version: 1
main_goal: speed
top_blocker: time
milestone_id: mvp-backlog-triage
milestone_seq: 1
milestone_status: open
---

# Roadmap: LinkSift

> Derived from `context/foundation/prd.md` (v1) + `context/foundation/tech-stack.md` + auto-researched codebase baseline.
> Edit-in-place; archive when superseded.
> Slices below are listed in dependency order. The "At a glance" table is the index.

## Milestone

**M-1: MVP backlog triage** — Status: open

- **Intent:** Deliver the full MVP flow from the PRD. A user logs in and submits links, each link's content is fetched or pasted, and it ends up in the inbox with a note, an eight-criteria assessment, a score and a verdict, ready to be reviewed from a phone.
- **Source materials:** `context/foundation/prd.md` (v1)
- **Done when:** every F-NN and S-NN below is `done`, and the author has run 20 real backlog links through the product to measure verdict agreement (PRD § Success Criteria → Primary).
- **Scope anchors:** FR-001 – FR-018 (FR-006 removed in the PRD), US-01, US-02, all Non-Functional Requirements, Access Control.

## Vision recap

The author has about 100 unread bookmarks on IT/AI and finance and no time to vet them. LinkSift does not just shorten text. It returns a *verdict* (valuable, to review or hype) judged on eight fixed criteria, with the score computed by a deterministic, repeatable rule rather than chosen by the model. When content cannot be fetched, LinkSift asks the user to paste it instead of inventing a summary.

## North star

**S-01: User submits an article link and sees it in the inbox with a note, eight-criteria assessment, score and verdict.** This slice proves the core product hypothesis, that a rule-derived verdict on fetched content is useful. With a speed goal and a hard deadline, every later slice only matters if this works.

> "North star" here means the smallest end-to-end slice whose successful delivery proves the core product hypothesis. It is placed as early as its prerequisites allow.

## At a glance

| ID   | Change ID                     | Outcome (user can …)                                                        | Prerequisites               | PRD refs                                    | Status   |
| ---- | ----------------------------- | --------------------------------------------------------------------------- | --------------------------- | ------------------------------------------- | -------- |
| F-01 | deployed-app-shell            | (foundation) API and web app shell are deployed and reachable from a phone  | —                           | NFR (mobile + desktop), tech-stack.md        | ready    |
| F-02 | minimal-login-and-isolation   | (foundation) the author can log in; every stored record is scoped per user  | F-01                        | Access Control, NFR (data isolation)        | proposed |
| S-01 | first-article-verdict         | submit an article link and see its note, assessment, score and verdict      | F-01, F-02                  | US-01, FR-005, FR-009, FR-010, FR-011       | proposed |
| S-02 | manual-content-paste          | paste content for a failed or incomplete fetch and get a verdict            | S-01                        | US-02, FR-008, FR-005                        | proposed |
| S-03 | x-post-fetching               | submit an X post link and get a verdict, with the thread when reachable     | S-01                        | US-01, FR-007                                | proposed |
| S-04 | inbox-order-filter-read       | review the inbox ordered by score, unread first, filter by verdict, mark read | S-01                      | FR-012, FR-013                               | proposed |
| S-05 | batch-submit-dedupe           | submit up to 5 links at once and be told about links already in the inbox   | S-01                        | US-01, FR-004, FR-015                        | proposed |
| S-06 | referenced-sources-check      | see assessments that also weigh up to 20 sources the link references        | S-01                        | FR-016, FR-010                               | proposed |
| S-07 | monthly-spend-cap             | see a clear message when the monthly processing cap is hit                  | S-01                        | US-01, NFR (10 USD cap), Guardrails          | proposed |
| S-08 | pending-signup-trial          | sign up, see "awaiting approval" and process up to 3 trial links            | F-02, S-01                  | FR-001, FR-003, Access Control               | proposed |
| S-09 | admin-account-approval        | (admin) approve or reject pending accounts                                  | S-08                        | FR-002, Access Control                       | proposed |
| S-10 | delete-item                   | delete an item so that nothing of it stays retrievable                      | S-01                        | FR-014, NFR (permanent deletion)            | proposed |
| S-11 | item-chat                     | chat about an item's topic from that item                                   | S-01                        | FR-017                                       | proposed |
| S-12 | custom-verdict-threshold      | set their own "valuable" threshold in settings                              | S-01                        | FR-018, FR-011                               | blocked  |

## Streams

A navigation aid that groups items into parallel tracks and gives a proposed reading order. The dependency graph below is canonical.

| Stream | Theme              | Chain                                                   | Note                                                                                  |
| ------ | ------------------ | ------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| A      | Processing core    | `F-01` → `F-02` → `S-01` → `S-02` → `S-03` → `S-05` → `S-06` | The strict must-have path: get to verdicts first, then broaden the inputs.       |
| B      | Inbox review       | `S-04` → `S-10` → `S-11` → `S-12`                       | Joins Stream A at `S-01`. These slices can run in parallel with A once S-01 lands.   |
| C      | Accounts and cost  | `S-07` → `S-08` → `S-09`                                | Joins Stream A at `S-01`. The spend cap goes before opening sign-up to other users.  |

## Baseline

What's already in place in the codebase as of `2026-10-04` (auto-researched + user-confirmed).
Foundations below assume these are present and do NOT re-scaffold them.

- **Frontend:** absent. The SPA planned in `tech-stack.md` has no code in the repo yet.
- **Backend / API:** partial. The framework and server are declared in `pyproject.toml`, but no app instance exists (`src/linksift/__init__.py` holds only a placeholder `main()`).
- **Data:** absent. The database is chosen in `tech-stack.md`, but there is no driver, schema or migrations.
- **Auth:** absent. The provider is chosen in `tech-stack.md`, but there is no integration or route protection.
- **Deploy / infra:** absent. Hosts and CI are chosen in `tech-stack.md`, but there is no deploy config and no `.github/workflows/`.
- **Observability:** absent. There is no logging setup, error tracking or metrics.
- **Verification tooling (extra):** present. Pytest, strict mypy and ruff are configured, and a smoke test passes (`tests/test_smoke.py`).

## Foundations

### F-01: Deployed app shell

- **Outcome:** (foundation) an empty API and an empty web app shell are deployed to the hosts chosen in `tech-stack.md`, with automatic deploy on merge, and the web shell can call the API from a phone browser.
- **Change ID:** deployed-app-shell
- **PRD refs:** NFR (usable on phone and desktop), `tech-stack.md` (deployment target and CI flow)
- **Unlocks:** S-01 (its end-to-end verification path runs on the deployed app). It also removes the risk of discovering deploy problems near the 2026-11-04 deadline.
- **Prerequisites:** —
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Sequenced first because the deadline is close and deploy issues found late are the most expensive. The scope is limited to an empty shell, with no features and no layer built out in advance.
- **Status:** ready

### F-02: Minimal login and per-user isolation

- **Outcome:** (foundation) an existing account (the author's) can log in, unauthenticated access to app routes redirects to login, and the per-user isolation policy is applied to the first user-owned record type.
- **Change ID:** minimal-login-and-isolation
- **PRD refs:** Access Control (login required, every user sees only their own links), NFR (data isolation)
- **Unlocks:** S-01 (items must be user-scoped from the first record), S-08 (sign-up builds on the login flow)
- **Prerequisites:** F-01
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Isolation is hard to retrofit once items exist, so it comes before S-01. Sign-up, pending accounts and roles stay out of this foundation and are delivered in S-08 and S-09.
- **Status:** proposed

## Slices

### S-01: First article verdict

- **Outcome:** User can submit one article link and later see it in the inbox with a concise, source-backed note, eight criteria scored 1–5 with justifications, a weighted score and a verdict (valuable, to review or hype), with processing running without the user staying on the page.
- **Change ID:** first-article-verdict
- **PRD refs:** US-01, FR-005, FR-009, FR-010, FR-011, NFR (no fixed time bound, status visible), Business Logic
- **Prerequisites:** F-01, F-02, an LLM gateway account with a server-side key
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:**
  - Which background processing mechanism to use; `tech-stack.md` defers it to planning. Owner: user. Block: no.
  - Initial criterion weights are fixed by the PRD and may be re-tuned later (see Open Roadmap Questions). Owner: user. Block: no.
- **Risk:** This is the north star. It carries the riskiest assumption, that LLM scores fed into the deterministic rule give useful verdicts, so it goes first. Paywalled and cookie-walled pages count as failed fetches, but the paste flow is deferred to S-02.
- **Status:** proposed

### S-02: Manual content paste

- **Outcome:** User can paste content for a link whose fetch failed, or flag any item's content as incomplete and paste it, and gets a note, assessment, score and verdict exactly as for a fetched link. Until then the item shows no summary.
- **Change ID:** manual-content-paste
- **PRD refs:** US-02, FR-008, FR-005
- **Prerequisites:** S-01
- **Parallel with:** S-03, S-04, S-05, S-06, S-07, S-08, S-09, S-10, S-11, S-12
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Enforces the no-hallucination guardrail. It comes right after S-01 because finance articles often sit behind paywalls, so many of the 20 sample links will need this path.
- **Status:** proposed

### S-03: X post fetching

- **Outcome:** User can submit an X post link and get a verdict. The single post is always fetched, the full thread is fetched when reachable, and an incomplete thread is marked so the user can paste the rest.
- **Change ID:** x-post-fetching
- **PRD refs:** US-01, FR-007
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-04, S-05, S-06, S-07, S-08, S-09, S-10, S-11, S-12
- **Blockers:** Paid access to the official X API is not yet set up (per `tech-stack.md`).
- **Unknowns:**
  - Which X API tier covers single posts and thread lookup for older bookmarks, and at what cost against the 10 USD per-user cap. Owner: user. Block: no.
- **Risk:** X is the main bookmark source and the only external vendor dependency. Sequencing it early in the core stream leaves time to fall back to manual paste if access stalls.
- **Status:** proposed

### S-04: Inbox ordering, filtering and mark-as-read

- **Outcome:** User can view all their items in one inbox, ordered by score with unread items first, filter by verdict and mark an item as read, comfortably on a phone.
- **Change ID:** inbox-order-filter-read
- **PRD refs:** FR-012, FR-013, NFR (usable on phone), Success Criteria → Secondary
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-03, S-05, S-06, S-07, S-08, S-09, S-10, S-11, S-12
- **Blockers:** —
- **Unknowns:** —
- **Risk:** S-01 shows only a plain list. This slice turns it into the daily review loop, which is the secondary success criterion.
- **Status:** proposed

### S-05: Batch submit with duplicate detection

- **Outcome:** User can submit up to 5 links at once, each processed as its own item, and is told when a link is already in their inbox instead of having it processed again.
- **Change ID:** batch-submit-dedupe
- **PRD refs:** US-01, FR-004, FR-015
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-03, S-04, S-06, S-07, S-08, S-09, S-10, S-11, S-12
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Low-risk widening of the S-01 input. The duplicate check covers only links currently in the inbox, so it interacts with S-10, where deleted links are forgotten.
- **Status:** proposed

### S-06: Referenced sources check

- **Outcome:** User can see assessments that also take into account up to 20 links referenced in the item's content, with independent corroboration counting distinct sources rather than reposts.
- **Change ID:** referenced-sources-check
- **PRD refs:** FR-016, FR-010, Business Logic
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-03, S-04, S-05, S-07, S-08, S-09, S-10, S-11, S-12
- **Blockers:** —
- **Unknowns:**
  - Cost per item with up to 20 extra fetches and LLM inputs against the 10 USD monthly cap. Owner: user. Block: no.
- **Risk:** This is the largest per-item cost multiplier. It is kept separate from S-01 so the north star does not depend on it, and S-07 should land before heavy use.
- **Status:** proposed

### S-07: Monthly spend cap

- **Outcome:** User's processing stops with a clear message once their spend reaches 10 USD in the current month, instead of incurring further cost.
- **Change ID:** monthly-spend-cap
- **PRD refs:** US-01, NFR (10 USD per user per month), Success Criteria → Guardrails
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-03, S-04, S-05, S-06, S-08, S-09, S-10, S-11, S-12
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Must land before sign-up opens to other users (S-08), because the operator pays for every account.
- **Status:** proposed

### S-08: Pending sign-up with trial

- **Outcome:** A visitor can sign up and log in as pending, see an "awaiting approval" notice, and process up to 3 trial links, after which adding links is blocked until approval.
- **Change ID:** pending-signup-trial
- **PRD refs:** FR-001, FR-003, Access Control
- **Prerequisites:** F-02, S-01
- **Parallel with:** S-02, S-03, S-04, S-05, S-06, S-07, S-10, S-11, S-12
- **Blockers:** —
- **Unknowns:** —
- **Risk:** It serves the secondary persona, so it sits after the author's own triage loop. The trial bound limits the cost of unapproved accounts.
- **Status:** proposed

### S-09: Admin account approval

- **Outcome:** The admin can approve or reject pending accounts in the app, without gaining any access to other users' items.
- **Change ID:** admin-account-approval
- **PRD refs:** FR-002, Access Control
- **Prerequisites:** S-08
- **Parallel with:** S-02, S-03, S-04, S-05, S-06, S-07, S-10, S-11, S-12
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Introduces the admin role. Tests must prove that the admin still sees only their own links (data isolation guardrail).
- **Status:** proposed

### S-10: Delete item

- **Outcome:** User can delete an item, and its content, note and assessment are removed permanently with nothing retrievable afterwards. Submitting the same link again is treated as new.
- **Change ID:** delete-item
- **PRD refs:** FR-014, NFR (permanent deletion)
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-03, S-04, S-05, S-06, S-07, S-08, S-09, S-11, S-12
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Small slice. Deletion must also cover data added by later slices (chat history from S-11, referenced sources from S-06), so re-check it when those land.
- **Status:** proposed

### S-11: Item chat

- **Outcome:** User can open a chat from an item and ask about its topic, with answers grounded in that item's content.
- **Change ID:** item-chat
- **PRD refs:** FR-017
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-03, S-04, S-05, S-06, S-07, S-08, S-09, S-10, S-12
- **Blockers:** —
- **Unknowns:**
  - How chat answers stay within the item's content so the no-hallucination guardrail holds. Owner: user. Block: no.
- **Risk:** This is a separate LLM flow competing for the same deadline (as the PRD noted). It is placed late in Stream B so it does not delay the triage loop.
- **Status:** proposed

### S-12: Custom verdict threshold

- **Outcome:** User can set their own "valuable" threshold in settings (default 60% of the maximum score).
- **Change ID:** custom-verdict-threshold
- **PRD refs:** FR-018, FR-011, Business Logic
- **Prerequisites:** S-01
- **Parallel with:** S-02, S-03, S-04, S-05, S-06, S-07, S-08, S-09, S-10, S-11
- **Blockers:** —
- **Unknowns:**
  - When the threshold changes, do existing items' verdicts change? FR-011 says results are "stored once", while Business Logic says the same scores and threshold always yield the same verdict. Owner: user. Block: yes.
- **Risk:** The answer decides whether the verdict is stored or derived at read time, which affects how S-01 stores results. Resolving it early is cheap.
- **Status:** blocked

## Backlog Handoff

| Roadmap ID | Change ID                   | Suggested issue title                                          | Ready for `/10x-plan` | Notes |
| ---------- | --------------------------- | -------------------------------------------------------------- | --------------------- | ----- |
| F-01       | deployed-app-shell          | Deploy empty API and web shell with auto-deploy on merge       | yes                   | Run `/10x-plan deployed-app-shell` |
| F-02       | minimal-login-and-isolation | Author login, route protection and per-user record isolation   | no                    | Waits for F-01 |
| S-01       | first-article-verdict       | Article link → note, 8-criteria assessment, score and verdict  | no                    | North star; waits for F-01, F-02 |
| S-02       | manual-content-paste        | Paste content for failed or incomplete fetches                 | no                    | Waits for S-01 |
| S-03       | x-post-fetching             | Fetch X posts and reachable threads                            | no                    | Waits for S-01; X API access pending |
| S-04       | inbox-order-filter-read     | Inbox ordering, verdict filter and mark-as-read                | no                    | Waits for S-01 |
| S-05       | batch-submit-dedupe         | Submit up to 5 links with duplicate detection                  | no                    | Waits for S-01 |
| S-06       | referenced-sources-check    | Weigh up to 20 referenced sources in the assessment            | no                    | Waits for S-01 |
| S-07       | monthly-spend-cap           | Enforce the 10 USD per-user monthly spend cap                  | no                    | Waits for S-01 |
| S-08       | pending-signup-trial        | Open sign-up with pending state and 3-link trial               | no                    | Waits for F-02, S-01 |
| S-09       | admin-account-approval      | Admin approves or rejects pending accounts                     | no                    | Waits for S-08 |
| S-10       | delete-item                 | Permanent item deletion                                        | no                    | Waits for S-01 |
| S-11       | item-chat                   | Chat about an item's topic                                     | no                    | Waits for S-01 |
| S-12       | custom-verdict-threshold    | Per-user "valuable" threshold setting                          | no                    | Blocked on threshold/stored-verdict question |

## Open Roadmap Questions

1. **Criterion weights may be re-tuned after measuring verdict agreement on the 20-link sample** (copied from PRD § Open Questions). Owner: user. By: before 2026-11-04. Block: none. It affects scoring constants introduced in S-01.
2. **How is per-user processing spend measured before S-07 lands?** Every LLM-calling slice (S-01, S-03, S-06, S-11) adds cost that S-07 must be able to attribute. Owner: user. Block: none, but each of those slices should record spend from the start.

## Parked

- **Telegram bot** — Why parked: PRD § Non-Goals.
- **Bulk import of bookmarks** — Why parked: PRD § Non-Goals.
- **Research beyond the link and up to 20 referenced sources** — Why parked: PRD § Non-Goals.
- **Automated trying-out of technologies mentioned in links** — Why parked: PRD § Non-Goals.
- **Bring-your-own-key** — Why parked: PRD § Non-Goals (next version).
- **Topic categorization** — Why parked: PRD § Non-Goals.
- **Editing items, re-assessment or manual verdict override** — Why parked: PRD § Non-Goals.
- **Automatic fetching of Reddit, video, podcasts, PDF and newsletters** — Why parked: PRD § Non-Goals (manual paste only).
- **Sharing notes** — Why parked: PRD § Non-Goals.
- **Per-user criterion weights** — Why parked: PRD § Vision scale note, "not MVP".
- **Error tracking and metrics** — Why parked: no PRD requirement demands them, and with a speed goal against a hard deadline they are deferred until after the MVP.

## Milestone History

## Done
