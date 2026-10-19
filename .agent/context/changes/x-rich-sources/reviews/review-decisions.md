# Review decisions — reader replies

## RC1 — Keyboard focus after loading

- Finding: [Reader-replies review](implementation-review.md#reader-replies-review--2026-10-19).
- Severity: medium (P2).
- Impact: keyboard and assistive-technology users lose their position when the
  completed request removes the focused Load button.
- Decision: Fix now.
- Owner: Codex.
- Rationale: a persistent result announcement preserves navigation after the
  asynchronous result and follows the established accessible UI contract.
- Status: verified.
- Follow-up: [T6](../plan.md), [canonical progress](../progress.md). Retain a
  focusable status announcement and move focus there after loading; cached
  refresh preserves its button focus.
- Evidence: [T6 verification](../evidence.md#reader-replies-verification--2026-10-19).
  Focus assertion failed before implementation and passes afterward. Native
  Return/Space activation at desktop and 390px mobile focuses the saved-result
  status. Screenshots retain the visible focus indicator.
