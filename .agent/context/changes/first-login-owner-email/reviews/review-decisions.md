# Review decisions

## REV-001 — Interrupted delivery reconciliation

- Finding: implementation-review.md, interrupted sending.
- Severity: medium.
- Impact: operations and duplicate-mail prevention.
- Decision: Fix now.
- Owner: implementing agent.
- Rationale: avoid automatic resend of uncertain outcome; document operator lookup and record reconciliation rather than promise unconditional admin retries.
- Status: verified.
- Follow-up: docs/certification/resend.md, recovery section.
- Evidence: test_interrupted_sending_event_is_not_resent_on_login_or_admin_retry; independent re-review approved.

## REV-002 — Notification documentation drift

- Finding: implementation-review.md, outdated approval instructions.
- Severity: medium.
- Impact: incorrect configuration and rollout.
- Decision: Fix now.
- Owner: implementing agent.
- Rationale: describe first-login recipient, exact sender, migration order and fresh-account acceptance.
- Status: verified.
- Follow-up: updated Resend, deployment, flow, architecture and test-plan docs.
- Evidence: independent resolution re-review approved.
