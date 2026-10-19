# Chat research progress

2026-10-20: owner approved the in-chat design and requested implementation and
push to main. Canonical execution record for this change. Graft unavailable;
focused source inspection used. Preserve unrelated uncommitted admin work.

- [x] Trace chat provider, service, ledger RPC, UI and existing tests.
- [x] Establish failing tests for two bounded searches, uncertainty and budget.
- [x] Implement durable slots, evidence-gap prompt and cost disclosure.
- [x] Update deployment documentation and editable/validated workflow diagram.
- [x] Run required verification and fresh independent implementation review.
- [x] Commit relevant chat changes and push main; report deployment requirements.

Scope includes the existing related chat-quality work (independent model and
reply language) already in the working tree. Paid evaluation and hosted database
migration execution are separate from this authorized source push.

Source committed as 1306e64. Latest evidence: 571 backend / 89 frontend tests,
strict typing, lint/format, frontend build, 51 SQL assertions and seven concurrent
gates pass. Independent code review reports no substantive findings. Workflow
schema/delivery/strict checks pass; browser QA and agent-toolkit unavailable.
Final independent artifact review approved with no actionable findings.
Source 1306e64 and verified artifacts f7d4435 pushed to origin/main successfully.
Unrelated admin edits remain local. Migration 000022 still requires hosted
application before matching deployment; no hosted quality claim.
