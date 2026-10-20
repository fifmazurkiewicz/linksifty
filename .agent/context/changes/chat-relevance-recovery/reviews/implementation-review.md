# Independent implementation review — 2026-10-21

Outcome: approve the local change; no actionable findings. A fresh reviewer
agent reviewed without editing code and independently reran the 93 focused
backend regressions (all pass).

## Scope and acceptance

Compared the chat-only working diff to HEAD: application contracts/service,
OpenRouter adapter, four backend test files, AnalysisChat and its frontend tests,
deployment/architecture guidance and this change context. Pre-existing
README/admin/App/auth-flow changes were excluded and preserved.

The reported 0.86 relevant probability with 0.79 normalized confidence reaches
research; classifier context uses the actual summary, and fixed uncertainty
replies do not buy another call. Existing billing settlement, owner scope,
duplicate fencing, bounded searches and malformed-response failures remain.
Search/factual answer quality is model behavior; the prompt and mocked replay
do not establish live accuracy. Historical failed rows retain a factual failure
explanation without unsupported charge or question-quality claims.

## Safety, privacy and conventions

The probability policy intentionally broadens admission from approximately
0.8667 to 0.8 selected probability. This is a documented bounded-chat policy,
not a model accuracy guarantee. Unsafe/off-topic decisions do not reach answering
or research; low selected probabilities only clarify. Input trust, citations,
budget admission, no automatic retries and server-only credentials remain.
No new dependencies, migration, services or paid provider verification.

## Evidence and limits

- Independent focused backend run: 93 pass; scoped whitespace check passes.
- Author's full gates: 595 backend tests, strict mypy, Ruff lint/format;
  91 frontend tests, lint/build pass.
- Deliberate reintroduction of the confidence gate fails the screenshot replay;
  source restored and 93 focused tests pass.
- Graft and agent-toolkit unavailable. Diagram validation, delivery and strict
  artifact check pass; browser check skipped because Chrome is unavailable.
- No production deployment or paid live search/answer acceptance is claimed.

No review-decision dispositions or derived board are needed without findings.
