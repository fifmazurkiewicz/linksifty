# Documentation refresh — 2026-10-22

## Scope and decision

User requested updated documentation, flows, diagrams, CI/CD, deployment and README.
This is a documentation-only change, authorized by that request; no product behavior,
provider calls, hosted migrations or deployments are part of execution.
Keep existing detailed rollout history, replace template frontend README, and make
current behavior and operator release steps easy to find. Prose is Polish; all
Archify diagrams are English per AGENTS.md. No new dependencies.

Graft is unavailable in this session. Evidence comes from focused inspection of
entrypoints, application services, SQL migrations, CI, Dockerfile and existing docs.
Preserve pre-existing frontend edits and the admin-count addition to README.

## Plan / acceptance

- [x] Inspect existing instructions, docs, runtime, CI and deployment configuration.
- [x] Refresh root/frontend README and documentation navigation.
- [x] Document current architecture, user/runtime flows and operational release process.
- [x] Produce editable, source-backed Archify diagrams and validate artifacts.
- [x] Check relative links, source claims and required repository gates; record limitations.

## Verification

Completed documentation and review. No hosted readiness is inferred.

- Root/frontend README, documentation index, architecture, flows, deployment and CI/CD updated.
- Historical architecture and feature/rollout details retained, including the existing admin-count note.
- Three English Archify diagrams delivered as editable JSON plus standalone HTML.
- Independent review completed; all three recorded findings fixed and verified.
- Final link check: 208 relative targets/anchors across 16 Markdown files, zero failures.
- Final artifact check: all three JSON/HTML SHA256 pairs match their current receipts.
- Review-decision board self-check and handwritten-document whitespace check passed.
  Generated Archify HTML has trailing whitespace; exact validated bytes are preserved.
- 595 backend and 93 frontend tests passed; mypy, Ruff, frontend lint/build passed.
- Unavailable: agent-toolkit command, configured local SQL gate, Chrome/Chromium browser QA.
- No deployment, hosted migration, paid provider request, commit or push performed.

See [evidence](evidence.md), [independent review](reviews/implementation-review.md),
[canonical dispositions](reviews/review-decisions.md) and
[derived review board](reviews/review-decisions-kanban.html).

Documentation scope is complete; environment-dependent checks remain disclosed limitations.
