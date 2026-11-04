# Frontend caught-error reporting

Scope approved by owner: frontend only. Keep API/backend and Render configuration outside this fix.

Observation: invalid link input shows a generic UI error while Sentry has no events. Reproduction returns422; this expected validation outcome is intentionally excluded. Public production JS already contains the expected DSN and enabled=true, calls the initializer, and has no CSP response header blocking ingestion. Those checks do not prove browser delivery.

Separate supported defect: the shared frontend API and activity-stream boundaries throw failures that UI callers catch, without reporting unexpected5xx, network or malformed-response failures. Existing SDK global handlers cannot observe those caught errors. Existing contract: errors-only, expected4xx/cancellation excluded, technical allowlist, monitoring outage preserves business behavior.

- [x] Reproduce missing telemetry with actual SDK envelopes and mocked network only.
- [x] Report unexpected failures at both shared HTTP boundaries; preserve exact returned data and thrown errors,4xx/auth/cancellation behavior and stream cleanup.
- [x] Verify privacy/outage cases, full frontend tests, lint, existing Sentry regressions and production build.
- [x] Independent review, publish to main, inspect CI and live frontend artifact.
- [x] Separately verify a synthetic event through the frontend adapter into Sentry. Disclose that this verifies ingestion/adapter, not the user's Safari transport or backend initialization.

High-impact privacy/outage risks retain existing testing-strategy depth. Monitoring gap: medium impact/medium likelihood. External browser/runtime acceptance remains explicitly separate from local proof. No logs, sessions, tracing, replay or metrics are enabled.
