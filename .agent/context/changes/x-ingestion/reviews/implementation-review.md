# Implementation review — 2026-10-18

Outcome: approve local X implementation; hosted activation remains external.
No unresolved non-informational findings in the X change.

## Plan and behavior

The adapter implements individual/long posts and the author's parent-connected
thread from root or middle URLs. Archive pagination, identities, parents and
complete source material are checked before assessment. Missing material returns
manual paste. An explicit archive start avoids default recent time windows.
The established tweet.fields wire names match the official quickstart; response
aliases cover renamed reference fields without repeating rejected reads.

## Security, privacy and costs

URLs cannot choose an API host/path or leak the token to redirects. API body,
source size, time, page and post bounds fail without returning a prefix. Domain
scoring remains provider-independent. Credentials remain server-only. Only
primary acquisition may use X; ordinary fetch and source research cannot trigger
X billing. Operator enablement explicitly approves external X-account costs.
Owner/lease/expiry/account SQL predicates and an atomic persistent marker prevent
automatic repeat attempts after crashes; source caching permits model recovery.

## Verification and limitations

Acceptance is supported by [evidence](../evidence.md): mock runtime/adapter tests,
real local SQL ownership/concurrency tests, strict typing, X-file lint, frontend
tests/build and mutation evidence. Transient shared-workspace lint failures in concurrent
chat code settled; the final full-repository Ruff lint/format checks pass. Toolkit and diagram browser checks cannot
run in this environment. API visibility cannot prove hidden/deleted descendants;
media, Article previews and external quote/repost context require paste. These
boundaries are explicit in the plan/setup and do not claim full hosted readiness.

Canonical progress and derived boards describe local completion, with external
activation separate. Keep the change record here until those external gates are
resolved; do not archive it as hosted verification.
