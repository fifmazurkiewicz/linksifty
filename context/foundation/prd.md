---
project: "LinkSift"
version: 1
status: draft
created: 2026-10-03
context_type: greenfield
product_type: web-app
target_scale:
  users: small
timeline_budget:
  mvp_weeks: 5
  hard_deadline: 2026-11-04
  after_hours_only: true
---

# LinkSift — Product Requirements

## Vision & Problem Statement

The author keeps ~100 unread bookmarks in the mobile browser — links from X, Reddit and articles on IT/AI and finance. They sit scattered, without notes; there is no realistic time to open and vet each one, so it is unclear which are worth attention and valuable items get missed among the hype.

Readers and plain "summarize this" prompts only shorten text. LinkSift's insight: the useful output is a *verdict* — value vs hype, judged on fixed criteria (novelty, evidence, practicality, source credibility, replicability, independent corroboration, absence of conflict of interest, concreteness vs superlatives) — with a value score derived by a deterministic, repeatable rule rather than model whim. And when content cannot be fetched, the product asks the user for it instead of inventing a summary.

Pain categories: data trapped in scattered bookmarks; workflow friction (vetting each link costs too much time); decision paralysis (which of 100 is worth reading).

Scale note: at much larger scale, a single global weighting would likely give way to per-user weights — what counts as "valuable" differs per person. Not MVP.

## User & Persona

**Primary persona — the author (Filip).** Follows IT/AI and finance on X, Reddit and blogs; saves links on the phone faster than they can be read. Reaches for LinkSift when the bookmark backlog becomes unmanageable and they want to know, without reading everything, what is actually worth their time.

### Secondary persona

Other people with an account (approved by the admin) who want the same triage for their own links. MVP serves the primary.

## Success Criteria

MVP flow: log in → submit up to 5 links → content fetched (articles, X) → on failure user is asked to paste content manually → summary + assessment on eight criteria → rule derives a weighted score and a verdict (valuable / to review / hype) → item lands in the inbox (filter by verdict, mark as read, delete, chat about the item).

### Primary
- Backlog processed: the author submits 20 real backlog links and every one ends in the inbox with a note, score and verdict — or with an explicit request for manual content.
- Verdict matches the author's own judgement in ≥ 60% of cases, on a sample of 20 links.

### Secondary
- Inbox review and mark-as-read work comfortably from the phone.

### Guardrails
- No hallucination: a failed fetch never produces an invented summary.
- Data isolation: no user — including the admin — sees another user's links.
- Cost control: unapproved accounts generate only bounded trial costs (FR-003); processing spend stays within 10 USD per user per month.

## User Stories

### US-01: User triages a batch of backlog links

- **Given** a logged-in, approved user
- **When** they submit several links (up to 5 — e.g. an article and an X post)
- **Then** each appears in the inbox with a note, an eight-criteria assessment, a score and a verdict — and any link that could not be fetched waits for manually pasted content

### US-02: User supplies content for a link that could not be fetched

- **Given** a link whose content fetch failed
- **When** the user pastes the content manually
- **Then** a note, assessment, score and verdict are produced exactly as for a fetched link

#### Acceptance Criteria
- Until content is pasted, the item shows no summary, assessment or verdict.

## Functional Requirements

### Access
- FR-001: Visitor can sign up; the new account stays pending until approved. Priority: must-have
  > Socrates: Counter-argument considered: open sign-up adds moderation cost. Resolution: kept — sign-up comes ready-made, its cost is negligible.
- FR-002: Admin can approve or reject pending accounts. Priority: must-have
  > Socrates: Counter-argument considered: an in-app admin panel is a hidden cost (a day or two); approval could be done manually outside the product. Resolution: kept as written — full approve/reject in the app.
- FR-003: Pending user can process up to 3 trial links and sees an "awaiting approval" notice; beyond the trial limit they cannot add links until approved. Priority: must-have
  > Socrates: Counter-argument considered: a pending user who sees nothing has zero value and may give up. Resolution: modified — bounded trial instead of a pure waiting screen.

### Adding & fetching
- FR-004: User can submit up to 5 links at once; each link is processed as its own item. Priority: must-have
  > Socrates: No counter-argument accepted initially; on follow-up user chose to cap links per paste to bound processing cost. Later revised: up to 5 links per submission, each its own item.
- FR-005: System fetches the content of articles; paywalled, cookie-walled or script-only pages count as a failed fetch. Priority: must-have
  > Socrates: Counter-argument considered: many finance articles sit behind paywalls, so "fetching" returns only a lead/cookie wall. Resolution: kept; such cases are treated as failures and routed to manual paste (FR-008).
- FR-007: System always fetches a single X post, and the full thread when it is reachable; when a thread is incomplete the item says so and the user can paste the rest. Priority: must-have
  > Socrates: Counter-argument considered: backlog bookmarks are often older than the 7-day search window, so full threads may be unreachable. Resolution: modified — post always, thread when reachable, explicit incompleteness marker. X remains core value and must-have.
- FR-008: When a fetch fails, user is asked to paste the content manually; no note is produced without content. User can also flag any item's content as incomplete and paste the content manually. Priority: must-have
  > Socrates: Counter-argument considered: partial fetches (cookie wall, title only) look like successes and yield junk notes. Resolution: modified — the user decides: they can flag incomplete content on any item and paste it manually.
- FR-015: User is told when a submitted link is already in their inbox; it is not processed again. Priority: must-have
  > Socrates: (arose from FR-014's challenge) Duplicate check covers links currently in the inbox only; a deleted link is forgotten.

FR-006 (Reddit fetching) was removed — Reddit is dropped from fetched sources for MVP; see Non-Goals.

### Assessment
- FR-009: User gets a concise note summarizing each link's content, with its claims backed by references to the source content. Priority: must-have
  > Socrates: Counter-argument considered: a summary may distort the thesis and can't be checked without reading the original. Resolution: modified — note is backed by the source.
- FR-010: User sees an assessment on eight criteria, each scored 1–5 with a short justification — novelty, evidence, practicality, source credibility, replicability, independent corroboration, absence of conflict of interest, concreteness (vs superlatives); source credibility is judged from available signals (author, domain, cited sources) and "unknown" is an allowed value. Priority: must-have
  > Socrates: Counter-argument considered: source credibility isn't a property of the content; judging it from text alone is guessing. Resolution: modified — judged from visible signals (e.g. open-source weights), always justified, "unknown" allowed (scored 1). Criteria later extended from four to eight at user's request.
- FR-011: User sees a weighted score and a verdict (valuable / to review / hype) derived by a deterministic rule from the assessment; each link is assessed once and the stored result does not change on its own. Priority: must-have
  > Socrates: Counter-argument considered: the rule is repeatable but its inputs (the scores) are not, so the same link processed twice may get a different verdict. Resolution: kept — determinism of the rule is sufficient; results are stored once. (Separate priority dropped — the weighted score orders the inbox.)
- FR-016: When assessing a link, the system also checks up to 20 links referenced in its content (e.g. cited sources). Priority: must-have
  > Socrates: Counter-arguments offered: 20× cost per item against a 10 USD/user cap; overlaps with the "no in-depth research" non-goal. Resolution: no counter-argument accepted; stands as written. Non-goal narrowed accordingly.
- FR-017: User can chat about a given item's topic from that item. Priority: must-have
  > Socrates: Counter-arguments offered: chat may invent answers (no-hallucination guardrail); a separate flow competes with X fetching for the 5-week budget. Resolution: no counter-argument accepted; stands as written.

### Settings
- FR-018: User can set their own verdict threshold in settings (default: score ≥ 60% of maximum = "valuable"). Priority: must-have
  > Socrates: Counter-argument offered: changing the threshold makes existing verdicts inconsistent with the new one. Resolution: no counter-argument accepted; stands as written.

### Inbox
- FR-012: User can view all their items in a single inbox ordered by score, unread first, and filter it by verdict. Priority: must-have
  > Socrates: Counter-argument considered: hype items sitting next to valuable ones still clutter the inbox. Resolution: modified — filter by verdict (hype / valuable / to review) added.
- FR-013: User can mark an item as read. Priority: must-have
  > Socrates: Counter-argument considered: "read" conflates "rejected" with "worth acting on". Resolution: no counter-argument accepted; stands as written.
- FR-014: User can delete an item. Priority: must-have
  > Socrates: Counter-argument considered: a deleted link submitted again costs again and re-clutters the inbox. Resolution: duplicate check against links currently in the inbox (FR-015); deleted links are not remembered.

## Non-Functional Requirements

- A submitted link reaches its verdict with no fixed upper time bound, without the user having to stay on the page; each link's current status is visible in the inbox.
- The full flow (submitting links, reviewing the inbox, marking read, filtering) is usable on a phone screen and on desktop, in current versions of mainstream browsers.
- A user's links, notes and assessments are visible only to that user — no other user, including the admin, can access them.
- Deleting an item removes its content, note and assessment permanently; nothing of it remains retrievable in the product.
- Processing spend has a hard cap of 10 USD per user per month; once reached, processing stops with a clear message instead of incurring further cost.

## Business Logic

Each link is scored 1–5 on eight criteria and a fixed weighted sum of those scores, as a percentage of the maximum, determines its verdict — ≥ 60% valuable, 40–60% to review, < 40% hype — and its place in the inbox.

The eight criteria: novelty, evidence, practicality, source credibility, replicability, independent corroboration, absence of conflict of interest, concreteness (vs superlatives). Inputs are the link's content (fetched or pasted by the user) and up to 20 sources it references, judged on these criteria, each with a short justification. Source credibility rests on visible signals (e.g. open-source model weights); when it cannot be established it is scored 1 — content of unknown provenance cannot score high. Independent corroboration counts distinct sources covering the topic, not reposts of the same one.

Weights are global and evidence-first: ×2 for evidence, replicability, source credibility and absence of conflict of interest; ×1 for novelty, practicality, independent corroboration and concreteness — hype typically scores high on novelty without evidence, so these weights push it down. Weights may be re-tuned against the 20-link agreement sample.

Output: one score and one verdict per link, stored once. The user meets them in the inbox, ordered by score (unread first) and filterable by verdict. The "valuable" threshold (default 60%) is set by each user in settings. Same scores and the same threshold always yield the same verdict.

## Access Control

- Login required; every user sees only their own links.
- Roles: **admin** (the author) and **user**.
  - Admin approves or rejects new accounts and also uses the app as a regular user. Admin does NOT see other users' links.
  - User: full control over own links only.
- Sign-up is open, but new accounts start as *pending*: a pending user can log in, sees an "awaiting approval" notice, and can process up to 3 trial links; beyond that they cannot add links until approved (FR-003).
- Unauthenticated access to any app route redirects to login.

## Non-Goals

- No Telegram bot — links are added in the web app only.
- No bulk import of bookmarks — links are submitted one or a few at a time.
- No in-depth research beyond the linked content and up to 20 sources it references.
- No automated trying-out of new technologies mentioned in links.
- No bring-your-own-key — processing runs on the operator's account in MVP; BYOK is the next version.
- No topic categorization — hype vs not-hype is enough.
- No editing of items — notes and assessments are read-only.
- No automatic fetching beyond articles and X — Reddit (dropped for MVP), video, podcasts, PDF and newsletters only via manual paste.
- No re-assessment or manual override of a verdict — the result is stored once.
- No sharing of notes — no public links, nothing visible to other users.

## Open Questions

None blocking. Note: criterion weights may be re-tuned after measuring verdict agreement on the 20-link sample (Success Criteria → Primary). Owner: user. By: before 2026-11-04.
