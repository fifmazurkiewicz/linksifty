# Repository secret audit — 2026-11-04

Scope: repository at `739808b7ffeb55ef7de81b8c2981d682d24e14e7`, reachable Git
history, tracked worktree, existing local frontend build and GitHub alert metadata.
No provider credentials were exercised or rotated, no private environment files
were read, and no external messages, deployments or pushes were performed.

## Result

No actual API key, access token, private key or credential leak was identified.
This is a bounded secret audit, not a guarantee of absence or a complete application
security assessment. Runtime hosting configuration and private environment values
were not examined.

## Evidence

- GitHub Actions Gitleaks v8.28.0 for the same commit: **77 commits**, approximately
  **52.25 MB** scanned, **no leaks found**. Logs confirm a real scan and success,
  not merely a green workflow label. The workflow fetches full history.
  [Secrets run](https://github.com/fifmazurkiewicz/linksifty/actions/runs/41904018162).
- GitHub Secret Scanning checked separately for both `state=open` and
  `state=resolved`: **zero alerts in both responses**. The API output was restricted
  to metadata; no secret values were printed or retained in this audit report.
- Independent local supplemental scan with Node standard library: **1,900 tracked
  files**, **2,087 unique historical blobs**, all reachable local refs (**77 commits**),
  and **3 existing local frontend build files**. No blanket scanner allowlist applied
  to `.agent/lock.yaml`.
- The supplemental scan checks recognizable provider token formats, private-key
  blocks, JWTs, credential URLs and plausible literal credential assignments.
  It is narrower than a general-purpose scanner and supplements the CI evidence.
- Supplemental URL candidates occur only in vendored Archify tests and Langfuse
  redaction tests. Their test contexts exercise credential rejection/redaction;
  all 23 file/value groups (12 distinct synthetic URL values) were reviewed as test
  fixtures, not actual provider credentials. Values omitted.
- **18 binary file/blob instances** were not parsed by the text scanner. No
  oversized text was skipped. Images, encoded archives and secrets lacking a
  recognizable format are outside that supplemental text coverage.
- Git history filenames contain `.env.example` templates, not real `.env` files.
  Current `.env` / production / local environment filenames are ignored and untracked.
- Inspected browser imports and Vite configuration: server provider keys are not
  referenced by browser source; `SENTRY_AUTH_TOKEN` is read in build configuration,
  passed to the upload plugin and not injected through Vite `define`/`envPrefix`.
- Docker context is allowlisted and explicitly excludes `.env` files.
- No local Gitleaks or Docker runtime is available; the actual Gitleaks result comes
  from the existing CI run. No audit tool was installed.

## SEC-001 — Broad lock-file exception (P2)

Location: `.gitleaks.toml:5–7`.

The global allowlist matches the entire `.agent/lock.yaml` path. Its description
says it excludes vendored-file SHA256 hashes, but there is no regex constraining
which matches are allowed. An actual secret accidentally added to that file would
also be excluded from Gitleaks. This is a detection gap; no such secret was found
in this audit's supplemental scan of the file or history.

Recommendation: constrain the managed exception to the known hash pattern as well
as its path, preferably through agent-toolkit so regeneration preserves it. Verify
with a synthetic non-secret canary that ordinary credential patterns in that file
remain detectable. Do not weaken existing provider rules.

Disposition: [canonical record](review-decisions.md#sec-001--lock-file-scan-exception).
No product/configuration fix was applied during this audit-only request.

## Review status

Single-session audit; not an independent second reviewer assessment. Confirmed
leaks: zero. One actionable prevention finding remains open. Environment variables
in Render/Vercel/Supabase, ignored local secret files, inaccessible third-party
systems and unreachable/deleted remote history are not certified by this result.
