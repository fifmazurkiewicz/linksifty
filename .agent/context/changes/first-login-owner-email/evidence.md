# Verification evidence — 2026-11-04

## Results

- Full backend: **611 passed**, one existing Starlette/httpx deprecation warning.
- Frontend: **112 passed**, 12 test files.
- Focused account/Resend/API tests: **18 passed**. Independent reviewer also ran focused service/Resend: **12 passed**.
- Mypy strict: 51 files PASS. Ruff lint PASS; format check 289 files PASS. Frontend lint/build PASS. agent-toolkit clean; git diff --check PASS.
- Disposable local PostgreSQL 17, UTF-8: every migration applied, fresh-profile first-login test **8 assertions PASS**, existing approval test **13 assertions PASS**, pre-migration account not backfilled PASS. Full database gate: **19 SQL suites PASS**, budget/duplicate/rubric/delete/X/image/selection/discussion/preview concurrency checks PASS. Database stopped afterward.
- Initial regression tests against unchanged application: **8 failed, 1 passed**, proving missing first-login dispatch and new mail contract. The first-login behavior assertion failed because the old flow left the event pending.

## Regression map

| Test | Expected behavior | Regression detected / change that would fail it |
| --- | --- | --- |
| test_first_login_notifies_owner_once_and_approval_only_grants_access | One owner message, no repeat on refresh or approval | Move dispatch back to approval or dispatch sent event again |
| test_failed_login_notification_never_blocks_or_retries_on_later_login | Login succeeds; failure remains visible; only explicit admin retry sends | Retry failed event on each /v1/me |
| test_admin_rejected_and_unverified_accounts_do_not_send_notification | No mail for owner, rejected or unverified identity | Remove dispatch eligibility conditions |
| test_missing_resend_configuration_keeps_login_available | Login succeeds, failure not_configured is persisted | Let missing mailer deny access |
| test_notification_storage_outage_does_not_block_login | Notification-only storage failure cannot deny login | Remove fail-open notification boundary |
| test_interrupted_sending_event_is_not_resent_on_login_or_admin_retry | Uncertain delivery waits for reconciliation | Automatically resend sending state |
| test_first_login_mail_targets_owner_with_stable_idempotency_key | Actual HTTP payload targets owner and carries stable event key | Use new user's address as recipient or generate random request key |
| test_first_login_email_escapes_user_content_in_html | User address is escaped in HTML | Interpolate unescaped address |
| Provider error/timeout/malformed-success tests | Safe failure categories, no private response leakage | Expose raw provider response or accept invalid receipt |
| first_login_notification.test.sql | One durable event; atomic claim; approval sends no new event and removes trial cap | Remove unique/trigger/claim guards or restore approval enqueue |
| Updated frontend auth-flow regression | Pending account exposes failed-notification retry | Require approved account to show retry |

## Review and limitations

Independent review and dispositions: reviews/implementation-review.md and reviews/review-decisions.md. No production database, credentials, DNS or Resend delivery were inspected. No real emails or paid-provider calls were made. Existing pre-migration profiles are intentionally not notified. Interrupted/uncertain sending requires operator reconciliation as documented; no blind resend.

Graft runtime was unavailable in this session's earlier check (npm registry DNS failure); focused source/docs reads were used. No Graft installation or paid indexing. No deployment, commit, push or archive.
