# Secret audit review decisions — 2026-11-04

Canonical finding disposition. The board is derived from this record.

## SEC-001 — Lock-file scan exception

- Finding: [audit report](implementation-review.md#sec-001--broad-lock-file-exception-p2)
- Severity: medium
- Impact: security/privacy; future accidentally committed credentials could escape Gitleaks in one allowlisted file
- Decision: Fix now
- Owner: project maintainer / agent-toolkit integration
- Rationale: Only known vendored-file hashes should be ignored, not arbitrary credentials in the whole lock file.
- Status: in progress
- Follow-up: Configuration narrowed; execute the new scanner regression in CI and correct the upstream toolkit generator before regeneration. See [progress](../progress.md).
- Evidence: `.gitleaks.toml:5–7`; [audit scope and results](implementation-review.md).

The open status is not a human acceptance or a Skip. This audit reports a detection
gap, not an actual leaked credential. No credentials were revoked or changed.

## REV-001 — Regression scanner path

- Finding: [fix review](fix-review.md)
- Severity: medium
- Impact: correctness; clean-hash regression would fail on absolute paths
- Decision: Fix now
- Owner: project maintainer
- Rationale: Directory scans must use relative paths like the production Git scan.
- Status: verified
- Follow-up: Docker runs with working directory /src and scans `.`.
- Evidence: Source args inspected after correction; actual scanner execution remains pending under SEC-001.

## REV-002 — Generator rule override conflict

- Finding: Independent generator review, 2026-11-06
- Severity: medium
- Impact: existing custom generic-api-key rules could conflict with generated rule
- Decision: Fix now
- Owner: project maintainer
- Rationale: Stop with an actionable diagnostic before modifying project files.
- Status: verified
- Follow-up: Generator parses unmanaged config and rejects duplicate rule ownership.
- Evidence: 26 toolkit tests pass, including conflict and read-only check regressions.
