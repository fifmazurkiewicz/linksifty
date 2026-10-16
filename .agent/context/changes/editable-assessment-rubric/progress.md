# Editable assessment rubric — progress

User approved design, plan and native execution on 2026-10-16. Implementation
uses the implementation, Ponytail, TDD and FastAPI skills. Graft is unavailable;
focused source reads and existing project documentation supplied context.

| Task | State | Evidence |
| --- | --- | --- |
| 1 Validated rubric/pure scoring | Done | Domain bounds, custom totals, default compatibility |
| 2 Atomic settings/snapshots | Done (local) | 31 pgTAP rubric assertions, concurrent save/reserve, legacy upgrade |
| 3 Model/scorer/history | Done (local) | Mocked provider input, exact citation rejection, cached recovery |
| 4 Settings/detail GUI | Done (local) | Form tests, keyboard, mobile 390px/light and desktop/dark preview |
| 5 Documentation/final review | Done (local) | 163 backend/32 frontend tests, 120 SQL assertions, 3 races, Archify gates, review |

Rules: eight fixed IDs; owner-specific descriptions and weights 1–10; one atomic
save. First model reservation captures rules; recovery reuses them. Legacy
records keep defaults, no score recomputation, no implicit paid retry. Migration
preserves source hashing from 000006 and duplicate/reset guards from 000008.

[Plan](plan.md) · [Evidence](evidence.md) · [Derived board](plan-kanban.html).
No production migration, deployment or paid call has been performed.


Implementation review: approved for local scope; see
[review](reviews/implementation-review.md) and the verified
[decision](reviews/review-decisions.md). Product source is saved in local commit
053f110; the architecture source pins that immutable revision. No push was made.
Hosted migration 000009, coordinated deployment and paid acceptance remain
separate owner-authorized actions, not incomplete local implementation tasks.
