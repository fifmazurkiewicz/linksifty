# Rich X source implementation review — 2026-10-18

Outcome: approve local implementation; hosted activation remains pending.

## Findings

No actionable correctness, security or billing findings from the fresh read-only
review. No Skip dispositions or owner-accepted defects are used. The parent
review reconciles final documentation and boards after implementation.

## Coverage and evidence

T1–T3 cover the approved full Article/static image scope. Provider/HTTP parsing
stays at infrastructure edges; orchestration and its new small protocol stay in
application; scoring is unchanged. No new API surface or service is introduced.
Full-body/dependency, credential-free media, all-image completeness, reservation,
settlement, cache ordering and no-assessment-on-failure have behavioral evidence.
SQL tests cover owner/lease/expiry/account/budget/deletion; concurrent admission
and shared-ledger races pass. Full Python/frontend checks are recorded in
../evidence.md. Canonical progress/plan are updated before derived boards.

## Security, privacy and cost

No server key reaches image CDN/frontend; media uses exact HTTPS host allowlist,
no redirects/proxies/cookies and byte/pixel/frame bounds. Model image content is
untrusted data. Bytes are ephemeral; only labeled complete readings are cached.
Existing owner scope and lease fences apply to new admission. Known costs settle
before assessment; unknown costs retain holds and block Retry. Late generation
IDs and deleted-job reservations remain reconcilable. Tests mock paid calls.

## Remaining external checks

Migration 000016 must precede backend/frontend. No hosted migration or paid
acceptance is authorized by this local review. The exact real Article payload,
full-body access and image-reading quality need hosted acceptance. Graft,
agent-toolkit and diagram browser QA unavailable are disclosed rather than waived.
Editable workflow has passing specification/artifact checks; no visual QA claim.
No archive until the separate activation work is resolved.

Diagnostic follow-up review: fixed branch labels replace the combined Article
check without changing accepted sources or performing additional requests. Nine
new cases check expected branch and privacy; deliberate diagnostic mutation is
caught. Full follow-up gate passes 407 tests, mypy and Ruff; toolkit unavailable.
No actionable security or acceptance-regression finding in the local diff.
Hosted failure root cause still requires a new explicitly authorized attempt.

Media-key compatibility review: normalize scalar Article media keys into the
existing bounded reference model; existing expansion and URL/type/byte validation
still applies. No new request, provider, persisted data or schema is introduced.
Four new cases cover both Article locations and both expansion outcomes. The
observed hosted media error does not alone prove this is its exact payload shape;
post-deploy live verification remains pending. One authorized Retry was consumed.


## Opt-in wire logger maintenance review

Outcome: approve local change for the owner-authorized push to main; hosted
acceptance remains pending. This review applies the implementation-review skill
using the approved in-chat design, existing plan/progress, final diff and evidence.

No actionable findings by severity. The server flag defaults off and does not
activate billed reads. Entry-point composition passes all configured secrets;
HTTP details stay in infrastructure, routes and scoring remain unchanged.
Configured/common secrets are redacted before truncation/chunking; headers are
excluded. Public source text, post IDs and queries become visible only in the
explicitly enabled operator log mode, as approved and documented. No additional
request/retry/persistence/schema/frontend behavior is introduced.

Accepted criteria have behavioral evidence: request/response correlation, 200
and 403 bodies before validation, request parameters for successful thread fetch,
invalid/oversized body rejection, transport interruption and status preservation,
privacy, output limits, default-off behavior, and startup wiring without Langfuse.
Secret-redaction mutation is detected. Final 423 tests, strict mypy and Ruff pass;
agent-toolkit is unavailable, not passed. Graft is unavailable; focused source
reads replace its orientation. Existing board states match canonical T1–T3 local
completion and pending hosted acceptance, so no board regeneration is needed.
No Skip decisions, archive or production success claim. No live paid request or
hosted environment mutation was performed. Operator activation remains separate.
