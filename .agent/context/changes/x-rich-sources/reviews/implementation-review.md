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
