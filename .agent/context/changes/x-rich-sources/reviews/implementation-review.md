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


## Captured Article compatibility implementation review

Outcome: approve T4 for the authorized ongoing main publication. No actionable
findings by severity; no Skip dispositions or new review-decision entries.

Plan/design coverage: validated entities.code, once-only quoted media resolution,
twelve-image single generation, separate default image model and truthful UI copy
are implemented. Invalid known media are checked before direct lookup; one local
request counter bounds lookup/search together. Source identity, version, graph,
completeness, URL, size, decoding and provider-output guards remain. Existing
reservation/settlement/unknown-charge fencing are unchanged, with tests for
all-image coverage and runtime settlement before source caching. Configuration is
server-only, wired at main, with no new dependency, schema or scoring change.

Evidence: 444 Python tests, 66 frontend tests, strict mypy, Ruff, oxlint and build
pass. Mutation catches omitted code. Actual captured payload is replayed offline,
with synthetic expansion/images explicitly separated from observed evidence.
No live credential read, paid request, deployment environment edit or migration.

Documentation/boards: canonical plan and progress mark T1–T4 complete locally;
change and roadmap boards mirror these states while hosted acceptance stays
pending. English editable workflow and rendered HTML reflect the lookup/model/
image limits. Static specification and artifact validation pass. Browser checks
are unavailable (Chrome absent), as is agent-toolkit; these are disclosed rather
than counted as success. No archive or claim of hosted inference quality.

## Thread/media correction review — 2026-10-19

Outcome: approve T5 locally. T6 (actual X-user replies panel) is pending scope
clarification and is not included in this approval. Graft is unavailable;
focused repository reads were used. No actionable findings by severity and no
Skip decisions.

The primary source remains the author's connected thread. Only branches with a
known foreign-author parent in the same conversation, and their author
descendants, are excluded. Unknown parents, cycles, foreign-conversation parents
and a submitted post outside the retained thread still fail closed. Unsupported
video/GIF types are identified before URL absence; source media are neither
silently discarded nor converted to partial assessment text.

Evidence: four initial failures become green; all 163 acquisition/debug cases
and all 470 backend tests pass. Thread/media mutations each fail two targeted
cases and were restored. Both supplied logs replay successfully using synthetic
image bytes with unchanged mocked API responses. Strict typing (47 files), Ruff
and whitespace checks pass. agent-toolkit is unavailable, not passed.

No new provider request, source persistence, API, schema, scoring or dependency
change in T5. Existing owner/lease/budget fences remain. No live paid request or
deployment occurred. The temporary analysis-note panel was removed after the
owner clarified actual reader comments by X users; it is not part of delivery.


## Reader-replies review — 2026-10-19

Outcome: approve T6 locally. Findings by severity: one medium (P2), RC1 keyboard
focus loss, returned to implementation and now verified fixed. Its canonical
[Fix now disposition](review-decisions.md#rc1--keyboard-focus-after-loading)
contains evidence and follow-up. No unresolved findings, Skip decisions or
accepted exceptions. Hosted provider quality acceptance remains pending.

Plan fidelity: actual X-user replies for primary and selected search links,
independent collapsed UI, explicit per-source X-charge consent, saved-only GET,
two-read/twenty-reply bounds, text/media disclosure, and unsupported Reddit match
the clarified scope. Discussion links/replies are separate from fetched evidence
and never reach scoring/model context. No analysis-note substitution remains.

Security/privacy: verified owner travels through each server-only RPC; eligible
completed/unexpired items and saved source membership are checked before atomic
once-only admission. Alias post IDs share the attempt. Uncertain/failed persistence
cannot buy another request. Completion is owner/item/attempt fenced and cannot
resurrect deleted content. Client grants are revoked; foreign content stays
inaccessible even to admins. No client URL, arbitrary HTTP destination, scraping,
new credentials or reply-media request. Output is bounded and rendered as text.

Architecture/conventions: routes handle transport, application service admission,
repository persistence, X adapter remote I/O, entrypoint concrete wiring. Native
details/summary, existing tokens and isolated styles preserve product conventions.
No dependency or lockfile changes; unrelated dirty admin/App/README edits retained.

Evidence: 487 backend tests, 77 frontend tests, strict mypy, Ruff, frontend lint/
build, 23 new pgTAP assertions and full disposable database/race gate pass. Guard
and consent mutations fail as intended; focus regression is red/green and native
keyboard verified on desktop/mobile synthetic previews. Workflow static checks
pass; Archify browser-check and agent-toolkit unavailable, explicitly disclosed.

Canonical plan/progress precede derived delivery/review boards. Setup documents
migration 000018 ordering, X configuration/cost and unsupported Reddit. English
editable workflow describes the new data flow. No roadmap milestone state is
changed by this bounded addition. No archive, hosted acceptance or external
publication is claimed. Graft is unavailable; focused impact/source reads used.


## Image quality/diagnostic maintenance review — 2026-10-19

Outcome: approve the local bounded correction and diagnostic change. No actionable
findings or new dispositions. The reported hosted failure remains unresolved
until its provider rejection check is observed; T7 stays in progress.

Original-size requests preserve fixed-host validation, query format, credential
isolation, single-call acquisition and all static-image/size bounds. Failures
do not fall back to lower-quality content. Diagnostics contain fixed check
labels, image count and a cost-known boolean, not raw source/model/provider text.
No scoring/model/prompt/budget/retry rule is changed. Known costs and generation
IDs survive rejection; unknown outcomes remain fenced and cannot yield assessment.

Evidence: 11 red/green cases, diagnostic and normalization mutations, 498 backend
tests, strict typing and Ruff pass. Privacy assertions cover rejected model text
and provider error messages. Read-only CDN observation proves only the resolution
difference, not the hosted failure cause. No frontend/database gate is necessary
for this backend-only maintenance. Toolkit is unavailable. Canonical execution
status and derived board retain pending hosted diagnosis; no archive or production
success claim. Existing unrelated admin changes remain untouched.
