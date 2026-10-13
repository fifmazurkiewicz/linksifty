# Implementation review: C8.1

Reviewed 2026-10-13 against the completion plan, progress, evidence, workflow,
README and derived boards. Scope: CI configuration for the existing packages.

## Findings and plan coverage

No non-informational findings. Two independent jobs install from lockfiles and
run backend tests, strict mypy, Ruff lint/format and frontend lint/build. Commands
use the established package roots and package managers. The frontend test step
will propagate failures once C6.1 supplies the runner; it is explicitly labelled
as absent today. No dependencies, lockfiles or product behavior changed.

## Verification

37 backend tests, strict mypy, Ruff, locked installs and frontend lint/build pass.
YAML contract checks cover triggers, permissions, required command lists,
working directories and lack of failure suppression. A deliberate failing npm
test returned exit 17; package.json was restored. Both boards pass diagram-design
self-check and agree with canonical task statuses: C8.1 Done locally, C1.1
Blocked on PostgreSQL, C2.1/C3.1/C6.1 Ready. Other MVP work remains incomplete.

## Security, conventions and limits

CI has read-only repository permissions, does not retain checkout credentials,
does not need provider keys, and performs no deployment or paid integration.
Timeouts and concurrency bound execution. GitHub execution, actionlint validation,
frontend behavior tests and the missing agent-toolkit gate are not represented
as passing. Real database RLS/ownership verification remains outside this slice.

## Outcome

Approve the locally verified C8.1 code slice. Hosted Actions execution and the
agent-toolkit quality gate remain unverified; this does not approve release,
archive the active MVP change, or waive either gate. Next independent task: C2.1.

## C2.1 review — 2026-10-13

**Scope:** Approved URL/DNS safety card, D-009 and acquisition adapter only.
No non-informational findings. C2.1 acceptance is covered by URL rejection,
all-answer DNS validation, public IPv4/IPv6 success, mixed DNS denial and a
real HTTPX transport test with mocked socket/TLS. The deliberate-break test
fails when numeric-IP pinning is removed. All 73 backend tests and strict
mypy/Ruff gates pass; no live network/provider requests or new dependencies.

The adapter now owns a fresh client, avoiding shared auth/cookies and IP-keyed
cross-host TLS pools. Environment proxies are disabled. Original Host and SNI
are supplied while the connection destination is numeric. This remains inside
the established acquisition boundary; domain/application/provider layering
and deployment topology are unchanged. Only tests called the former signature.

**Outcome:** Approve C2.1 for its local, mocked evidence scope. C2.2–C2.5 still
own redirects, streaming limits, extraction and full completeness; the fetcher
is not yet a complete production acquisition pipeline. Missing agent-toolkit
runtime remains an outstanding quality gate. No release/archive approval.
C2.1 Done and C2.2 Ready are reflected in canonical records and derived boards.
