# Verification evidence — 2026-10-17

## Behavioral checks

- Before implementation, 11 new scoring/status cases failed against the old domain.
- Before provider/search changes, 6 provider/20-source cases failed, including 10-vs-20 results and the five-fetch cap.
- New detail tests initially failed on missing unscored labels and hype evidence, then passed after implementation.
- Final full backend run: 184 passing tests.
- Frontend: 35 tests pass, including legacy detail, null totals, N/A/unverified labels, hype citations and v2 settings save round-trip.
- Strict mypy: 33 source files pass. Ruff lint and formatting pass. Frontend oxlint and production build pass.
- `git diff --check` passes.

## Deliberate-break check

The first mutation (restoring automatic below-40 hype) did not fail the all-ones case because the independent critical-criterion guard already returned review. Added a case with all four key criteria at 3, remaining criteria at 1 and learning weight 2: total 38.46%, expected to_review. Restoring the old below-40 rule made that case fail. The original scorer was restored byte-for-byte and all 12 calibrated scoring tests pass. This isolates the low-total rule from the key-criterion guard (REV-001).

## Database

Existing installed PostgreSQL 17 / pgTAP used on a fresh disposable cluster under
`/private/tmp/linksifty-calibration-pg`, loopback port 55440, database
`linksifty_calibration_test`, synthetic local role and synthetic content only.
No production credentials or provider calls were used.

Applied migrations 000001–000009, seeded a custom description/weight 9 and a
reserved v1 job, then applied migration 000010. Assertions confirmed settings
upgrade to v2, custom wording/weight preservation, replacement of old default
wording, and unchanged unversioned reserved snapshot. The SQL test identified
a PL/pgSQL citation alias ambiguity; corrected the alias and reran the gate.

Final gate: eight SQL suites / 139 pgTAP assertions pass, plus three concurrency
checks (budget admission, duplicate submissions, atomic settings/reservation
snapshot). New cases cover 20 sources accepted / 21 rejected, owner fences,
null points/totals, N/A restriction, hype rejected without primary evidence,
comparison-source hype rejection and successful grounded-hype persistence.

Command:
`PATH=/opt/homebrew/opt/postgresql@17/bin:$PATH UV_CACHE_DIR=/private/tmp/linksifty-uv-cache LINKSIFTY_TEST_DATABASE_URL=postgresql://linksifty_test_runner@127.0.0.1:55440/linksifty_calibration_test uv run --package linksifty python backend/tests/integration/check_processing_database.py`

## Review and documentation

Fresh read-only reviewer found no actionable code defects after excluding the
known in-progress SQL alias fix. Suggested cached-v1 recovery and v2 settings
round-trip tests were added and pass. Final self-review identified REV-001's
mutation-test isolation gap; disposition and verification are recorded in
[review-decisions](reviews/review-decisions.md).

Product vision, architecture, deployment instructions, README, roadmap and
derived boards updated. No deployment or paid/live article calibration is claimed.

## Diagram

Archify workflow `assessment-workflow.json` / `assessment-workflow.html` passes
schema/source validation, delivery and strict artifact checks. Browser check is
skipped: Chrome/Chromium unavailable. No perceptual review is claimed. The
source evidence is pinned to an isolated local snapshot of the inspected
working-tree files, preserved in `diagram-source.bundle`; the main repository's
HEAD was not changed. Snapshot restore for evidence: `git clone diagram-source.bundle <new-directory>`.
The final summary receipt records the exact candidate/artifact hashes.

## Limitations

- Graft runtime unavailable; focused repository inspection used.
- `agent-toolkit check` attempted, exit 127: command not found. This quality gate remains unverified; the change is not archived as fully gated release work.
- Diagram browser QA unavailable. Semantic UI tests and frontend build pass; no fresh manual browser QA is claimed.
- Live model agreement, production migration, hosted recovery and paid article calibration remain operator activation steps.
