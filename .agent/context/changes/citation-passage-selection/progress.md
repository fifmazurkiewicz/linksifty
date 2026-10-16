# Citation passage selection

Approved by the owner in chat on 2026-10-16. Bounded adapter change: the model
selects a supplied passage ID; code supplies the exact excerpt and actual source.

## Decision and scope

Keep persisted SourceAssessment, application orchestration, API, SQL offset checks,
budget accounting and recovery unchanged. Replace only the provider input/output
contract. Do not add retries, dependencies, fuzzy matching or provider calls.
Use bounded contiguous source slices, preserving original characters and all text.
Passage selection proves provenance, not semantic support or publisher independence.
Existing failed results require an explicitly requested new analysis after deployment.

## Tasks

- [x] P1: Reproduce failure with mocked provider tests (RED).
- [x] P2: Implement ID selection, exact hydration and regression coverage.
- [x] P3: Run available checks, review diff and document deployment/limitations.
- [ ] P4: Required agent-toolkit gate — blocked: command unavailable in this environment.

Graft is unavailable in this session; orientation used focused code searches and
existing architecture/setup documentation. No topology or public API change.

Evidence: [evidence.md](evidence.md).

Implementation and local verification complete. Deployment and paid live-provider
acceptance were not performed. Required toolkit verification is not waived; rerun
`agent-toolkit check` in the configured operator environment before release.
The board is a derived snapshot; this record remains canonical.
