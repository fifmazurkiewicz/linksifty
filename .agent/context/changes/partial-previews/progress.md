# Automatic partial-content previews — 2026-10-19

Approved bounded design: the owner rejected an extra Generate button and requested
an automatic one-sentence overview whenever any readable content was fetched.
This explicitly permits a labeled preview from incomplete text; assessment and
scoring still require complete content. No media inference is introduced.

Graft unavailable; focused reads cover X/web adapters, processing, title/model
generation, owner-scoped item DTOs, ledger/migrations, queue and submission flow.
Unrelated admin edits remain untouched. No paid request or hosted migration.

- [x] Retain bounded, separately typed partial text from safe web reads and only
  reachable X posts, including readable Article fragments; never use unrelated
  expansions, withheld text, unsafe targets or binary data.
- [x] Automatically generate one validated sentence with existing OpenRouter
  controls. Persist preview metadata separately; never save partial source as
  complete text, research it, assess it or change Needs action status.
- [x] Migration 000021: owner/lease/account/expiry and shared-budget admission,
  durable once-only preview slot, late-generation recording and reconciliation.
  Persist explicit consent from updated submission/Retry disclosure; old jobs
  default off. No additional button, provider retry or media read.
- [x] Queue preview/loading/empty states and cost disclosure; backend/frontend/
  SQL regressions, red/green/mutation, all required checks, docs/English editable
  Archify contract and review. Deployment remains a separate operator step.

Partial text stays in memory and is bounded to 6,000 characters. Only the generated
sentence is stored on the owned item, under the existing retention/deletion rules.
An exhausted budget, invalid output or unknown charge cannot create an assessment.
One preview attempt per job survives recovery and explicit source retries; there
is no automatic paid resend. Existing failed items need an explicit fetch Retry.


## Local completion

Complete locally. All requested behavior is implemented with no extra preview
button: bounded X/web fragments, automatic budgeted generation, labeled metadata
in Needs action and no assessment/score. Consent comes from updated Submit/Retry
disclosure; older jobs/clients remain off. Unknown preview charges suppress Retry
until reconciled; Paste remains available under existing budget rules.

Verification and limitations are canonical in evidence.md. Reviews PP1 and PP2 are Fix now /
verified in reviews/review-decisions.md. The English new preview workflow and the
updated text-only contract pass static Archify gates; browser checks are skipped
without Chrome. Toolkit is unavailable. Unrelated admin work and concurrently
completed chat diagnostics remain separate. Migration 000021 and matching backend/
frontend deployment plus an explicitly authorized real Retry are still required
for this existing failed item. No hosted migration, paid request, push or deployment.

Review PP2 correction: Submit/search/Retry persist consent atomically through
three-argument RPC overloads reusing the existing guarded operations. No separate
consent request can race the worker claim. Old clients keep the two-argument RPC
behavior and no consent. API regression and three SQL cases verify this boundary.

Final local verification: 560 backend tests, 89 frontend tests, strict mypy, Ruff
lint/format, frontend lint/build and the disposable 31-assertion SQL plus complete
admission/budget/deletion gate pass. Current diagram artifact hashes agree with
static receipts. PP1 and PP2 are verified; no open findings or accepted Skip.
