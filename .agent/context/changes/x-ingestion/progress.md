# X ingestion

Current source policy and Article compatibility live in
[rich-source progress](../x-rich-sources/progress.md) and its
[text-only workflow](../x-rich-sources/text-only-workflow.html). The acquisition
diagram here is now explicitly historical; its earlier media rejection behavior
is superseded. T9 adds bounded missing-embed text lookups, no new migration.

## Quote/repost fix — 2026-10-18

Owner-supplied hosted log identifies `unsupported_references`. The adapter's
parent guard treated all references as reply parents. Implemented expansion of
referenced posts in existing requests, separate reply-parent selection, original
thread acquisition for reposts, complete context validation and attributed source
text. Updated plan/research document decisions and boundaries before the derived
board. Full backend suite: 357 pass; strict mypy and repository Ruff lint/format
pass. Contract diagram source/HTML updated; validation, delivery and strict
artifact checks pass, browser check is skipped because Chrome is unavailable.
Toolkit remains unavailable. Local implementation review approves publication;
hosted acceptance of the quote/repost fix requires deployment and an explicit
owner retry. No live paid request was made. Graft remains unavailable; focused
reads used.

## Render diagnostics follow-up — 2026-10-18

Owner reports deployed X ingestion still fails with no visible Render error and
requests logs. Bounded maintenance: use existing warning-level Python logging,
without dependencies, configuration flags, database/UI changes or new provider
requests. Log fixed endpoint labels and HTTP status at the adapter, exception
types without messages, and job ID/provider/failure reason at the acquisition
outcome. Keep credentials, URLs, source text and raw provider data out of logs.
Document Render filters and explicit retry/billing implications. Local regression
verification is recorded in evidence.md; deployment and live diagnosis remain
outstanding.

Follow-up: owner supplied hosted logs showing only `source_fetch_failed` with
`partial_content`. This confirms the first diagnostics build runs but leaves the
intentional completeness guard unidentified. Every internal adapter rejection
now carries a static `check` label logged at the existing warning boundary;
payload validation distinguishes post lookup from thread search. No source
acceptance rules or retry/billing behavior change. Regression cases verify
specific checks and payload exclusion; details are in evidence.md. The failing
post's precise hosted guard remains unknown until the next explicit attempt.

2026-10-18 — Local implementation complete. Owner requested implementation and explicitly selected
individual posts plus full threads. Graft is unavailable; focused repository
reads and official X documentation establish the integration contract.

- Context and design: complete; existing owner-scoped acquisition pipeline.
- Adapter and behavioral tests: complete. Official fixed endpoints, paginated
  full-archive reads, long text, connected author thread, URL/size/time guards.
- Durable attempt guard, runtime composition and queue explanations: complete.
  Migration 000012 admits one owner/lease-fenced attempt; cached source is reused.
- Documentation and English editable workflow diagram: complete. Archify source,
  delivery and strict artifact checks pass; browser check is unavailable.
- Verification/review: complete for the X slice. 53 focused X cases, 285 full
  backend tests, 57 frontend tests, strict mypy, full Ruff lint/format and frontend
  lint/build pass. Eleven local SQL suites and six concurrency checks pass.
  Required toolkit and diagram browser checks are unavailable. Concurrent chat
  lint/format edits settled; the final full-repository checks pass. See [evidence](evidence.md) and
  [implementation review](reviews/implementation-review.md).

## Activation (external, not performed)

Apply migration 000012 before deploying this backend; configure the server-only
X_API_BEARER_TOKEN with lookup/full-archive access and explicitly set
X_API_READS_ENABLED=true after reviewing X billing. X account charges are outside
the existing model/Brave ledger. Hosted endpoint/billing acceptance is unverified.
Old manual-content items stay manual; paste or explicitly delete and re-add.

No new dependency, hosted migration or paid provider call was made.
Concurrent chat implementation in this shared workspace was preserved.

No live credentials, paid requests, deployment or production data changes are
authorized by this local implementation task.

## Publication authorization — 2026-10-18

The owner requested pushing all workspace changes to main, including X ingestion
and analysis chat. Final combined checks: 285 backend and 57 frontend tests,
strict mypy, Ruff lint/format and frontend lint/build pass. Pending files were
checked for credential files and common secret formats with no matches.
agent-toolkit remains unavailable. Hosted migrations and activation are separate.
