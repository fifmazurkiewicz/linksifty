# Chat Langfuse diagnostics — 2026-10-19

Owner request: trace chat classification and answers; investigate current failures.
Bounded maintenance of existing chat and opt-in telemetry. Reuse redaction and
failure isolation; preserve owner scope, budget settlement and no automatic retries.
No new dependency, migration, provider call, deployment or architecture change.

- [x] Inspect chat/provider/telemetry and deployment documentation; Graft unavailable.
- [x] Add failing behavioral tracing tests, implement and verify regression coverage.
- [x] Inspect existing hosted failure metadata without resubmitting paid requests.
- [x] Update deployment guidance; local Python gates pass. Toolkit gate unavailable.

Decision: named classification/answer generations under an opaque per-turn chat
trace, with bounded redacted inputs/raw responses, validated outputs, known usage
and cost, provider status and stable failure reasons. Reuse the existing telemetry
boundary rather than add a separate logger or tracing framework. Telemetry must
not retry providers or change the result/charge behavior.

Implemented: per-turn scope, named classification and answer generations, raw
redacted response/status events, generation usage/cost/output/failure and persisted
outcome. Backend failure warnings expose opaque turn ID and stable reason only.
No public HTTP contract or frontend change; existing unrelated user edits preserved.

Production diagnosis: both exact screenshot-question turns on 2026-10-19 at
16:39:18 and 16:39:28 UTC failed with `classification_uncertain`. The only
reservations were classification, both settled at USD 0.000091938 each; no
answer/search call was made. Existing code requires validated scope confidence
>=0.8. Historical confidence/choice responses were not stored; exact values and
the classifier's semantic reasoning cannot be recovered from the current records.
Read-only Supabase queries were owner-scoped. No credentials were accessed,
paid calls repeated, hosted data changed, or backend deployed. Threshold unchanged.

Verification: initial full snapshot: 532 backend unit tests, strict mypy (50
source files), Ruff lint/format (131 files) and diff whitespace check pass. Real SDK export uses an
in-memory collector and mocked HTTP only. Deliberate removed trace makes its
behavioral regression test fail; restored code passes. `agent-toolkit check`
cannot run because the command is not installed; no installation attempted.
See evidence.md and reviews/implementation-review.md for details and limits.

Final rerun after concurrent partial-preview edits appeared: 72 focused
chat/provider/telemetry/config tests pass; strict mypy passes. Full unit suite:
539 passed, 3 failed in the newly added test_partial_previews.py acquisition
cases. Global lint/format now fail in concurrent partial-preview code/tests,
including their new sections in openrouter_client.py. These edits and AGENTS.md's
concurrent preview-policy update were inspected and preserved. This task does
not claim a green final global gate or repair/archive that separate active work.

Release follow-up: owner authorized push to main. An exact chat-only snapshot
from current main, excluding all concurrent admin/partial-preview changes, passes
532 backend tests, strict typing and Ruff lint/format. Provider imports were
verified to resolve to the snapshot. Toolkit remains unavailable; see evidence.
