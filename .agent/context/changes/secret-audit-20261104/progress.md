# SEC-001 follow-up — 2026-11-05

Owner requested fixing the broad lock-file exception. Scope: scanner configuration,
a synthetic regression check and the existing Secrets workflow; no application or
hosting change, paid requests, credential inspection, commit or push.

## Decision and risk

Require path AND an anchored four-space YAML hash line, restricted to the default
`generic-api-key` rule. Other provider rules remain active even on hash lines.
This follows the Gitleaks v8.28.0 allowlist contract. Installed agent-toolkit still
regenerates the vulnerable blanket exclusion; do not run install/update until its
upstream generator is corrected. The regression CI step protects against reintroduction.

Risk: credentials accidentally placed in the lock could escape detection (high
impact, medium likelihood, conservative assumption; source SEC-001 and AGENTS.md).
False positives could block contributions (medium impact, low likelihood).
No rating was lowered. No real credentials are used in checks.

## Execution and evidence

- Config narrowed; added `tools/check_gitleaks_allowlist.py` to Secrets CI using
  the same pinned Gitleaks v8.28.0 Docker image as the existing full-history scan.
- Strict mypy: 51 source files pass. Ruff check passes; format: 290 files pass.
  `git diff --check` passes.
- Actual scanner regression is NOT executed locally: neither Docker nor Gitleaks
  is installed. No installation performed. CI execution remains required.
- `agent-toolkit check` fails: `Gitleaks allowlist differs: .gitleaks.toml` because
  its installed template contains the original SEC-001 defect. No check weakened.
- Graft unavailable: registry DNS resolution failed. Focused file inspection used.
- No application code changed; application test suites were not rerun.

| Regression check | Expected behavior | Break caught |
| --- | --- | --- |
| Hash in lock | Scanner succeeds | Removing intended hash exception |
| Hash outside lock | Scanner reports finding | Dropping path constraint |
| Credential in lock | Scanner reports finding | Original blanket exclusion |
| Credential beside hash | Scanner reports finding | Broadening hash-line pattern or provider exclusions |

Status: implemented, awaiting actual scanner evidence and toolkit generator fix.

## Main publication follow-up

Commit 7556ed3 published; application CI passed. Full-history Secrets scan exposed
seven legitimate historical lock hashes not accepted by the line-based matcher.
Changed the matcher to the extracted secret, exactly 64 lowercase hex characters,
with the same path AND generic-api-key restriction. Provider rules remain active.
The canary-beside-hash regression continues to require detection by provider rules.

Gitleaks v8.28.0 config source reveals targetRules attachment is skipped after
default extension (extendDepth guard). Use explicit generic-api-key rule allowlist
instead; preserve inherited detector and all other rules.

Full-history scan now passes. Regression caught an ineffective alphabet-sequence
canary (default scanner stopword); replaced with a synthetic non-sequential value.

## Generator correction — 2026-11-06

Owner requested update/check and publication to main. Initial update reproduced the
unsafe whole-file exception. Fixed the local agent-toolkit source generator to
emit the exact verified Linksifty configuration and added a generated-TOML
regression. All 26 toolkit tests pass (cache-write warnings only). Reinstalled
from the local source, then ran update and check: `agent-toolkit: clean`.
The generated Linksifty files are unchanged from main. Graft index build still
fails with exit 126; this does not certify the index. Earlier scanner/runtime
limitations above are historical: Linksifty CI and all four scanner regressions
passed for f391f6d (Secrets run 42075492079).

Independent generator review identified conflicting project overrides of the same
rule ID. Generator now rejects that input before writes with an actionable error;
a dedicated regression passes. Existing check-read-only tests remain passing.
