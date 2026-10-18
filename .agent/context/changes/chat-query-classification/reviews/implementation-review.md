# Implementation review — 2026-10-18

Native self-review against the approved bounded in-chat design and final diff;
not an independent review. Graft is unavailable; focused source/test reads used.

## Outcome

Approve local implementation. No actionable review findings remain. No Skip or
human risk acceptance is inferred. Environment and live-provider limitations
below are informational, recorded in ../evidence.md.

## Coverage and boundaries

- The separately pinned typesafe/jev-1.13 gate precedes generation/research.
- Relevant scope uses bounded analysis/original excerpts and recent conversation;
  saved research cannot expand the original topic scope. Current message wins.
- Off-topic/unsafe decisions produce fixed Polish/English uncited paragraphs with
  no answer/search calls. Provider failure/malformed output/low confidence stops.
- Strict enum/distribution/finite numeric validation rejects invalid decisions;
  source/question/history data cannot change classifier policy by design.
- Application orchestration remains outside routes; HTTP stays in the existing
  OpenRouter adapter. No new dependency, credential, framework or worker.
- Migration 000015 preserves ownership, shared settings-lock admission, unique
  call slots, no automatic retry, generation persistence, exact existing cost
  settlement and content-deletion fences. Database grant scope is preserved by
  CREATE OR REPLACE on already restricted RPCs. Historical turns remain readable.
- Existing frontend safely renders uncited refusals; regression verifies history
  restoration and a subsequent draft. The source-grounded answer contract stays
  unchanged, including the requirement for real passage IDs.

## Evidence

309 backend tests; strict mypy; Ruff lint/format; 65 frontend tests/lint/build;
39 chat SQL assertions; five chat concurrency checks; 12 SQL suites and six
existing concurrency checks. The refusal branch mutation turns all four refusal
cases red. Cost/ID preservation, unknown costs, duplicate requests, budget denial,
owner isolation and deletion are tested. Full commands/results in ../evidence.md.

The English sequence's source/delivery/strict artifact gates pass. Browser QA
cannot run without Chrome/Chromium. The earlier workflow draft's layout failure
is retained as diagnostic evidence, and is not the delivered diagram.

## Operational and verification limits

Apply migration before backend and coordinate the short transition, since older
backends cannot reserve an unclassified decision afterward. No hosted change was
performed. Jev semantic accuracy, provisional confidence cutoff and Decisions
generation-ID lookup require live acceptance with explicit cost authorization;
lookup failure keeps reservations intact. Toolkit executable and Graft are absent.
These are documented limits, not successful or waived checks.
