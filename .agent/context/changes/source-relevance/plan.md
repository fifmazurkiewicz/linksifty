# Source relevance implementation plan

Goal: exclude unrelated comparison pages before downloading them, with accountable
Jev selection. Approved in-chat design; canonical state is progress.md.

- [x] T1 Query and selection: test numeric-ID regression, transient Brave metadata,
  typed Jev responses/coverage/confidence/cost/bounds/no retries. Add pure query
  helper, SourceSelector boundary and Jev adapter; reuse existing choice validator.
- [x] T2 Budgeted orchestration: add reserve/record/claim/reconciliation support and
  migration 000017, including disabling old unsaved research opt-ins. Gate all extra page downloads on admitted, validated decisions.
  Test no-selector/no-candidate/budget/unknown/failure/cache/recovery and trace privacy.
  SQL tests cover owner/lease/expiry/account/budget/one admission/late generation/
  deletion/privileges; overlap tests cover same-job and shared-budget races.
- [x] T3 Disclosure and delivery: update search opt-in and uncertain research copy,
  configuration composition/capabilities, setup, architecture and roadmap. Maintain
  English editable workflow and boards after canonical records. Run full Python
  tests, strict mypy, Ruff, frontend tests/lint/build, local SQL/concurrency gates,
  agent-toolkit check. Record mutation evidence and implementation review.

Paid/remote integrations are mocked. No new dependency, live provider call,
credential read, automatic retries or saved-result rewrite. Missing runtimes are
reported. Do not publish an auto-deploying revision before migration activation.
