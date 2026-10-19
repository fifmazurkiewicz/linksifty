# English/Polish generated output

- Request: generated content must use English or Polish, including partial previews.
  The owner confirmed this applies to all generated content.
- Decision: use a shared provider instruction for generated prose. Source-driven
  previews, titles and assessments use Polish for Polish sources and English
  otherwise. Chat keeps its validated reply-language field and defaults to English
  for other question languages. Preserve names, code and exact source quotations.
- Scope: existing OpenRouter prompts, one request-contract regression test and
  README. No new model call, retry, dependency, language detector, setting, API or
  migration. Stored results remain historical. Graft is unavailable in this session;
  focused source searches covered the generation entrypoints and chat classifier.
- Execution: four request-contract tests failed before the fix and pass after it.
  Deliberately restoring source-language instructions makes all four fail again;
  the correct implementation was restored.
- Complete: 575 backend tests, strict mypy and Ruff lint/format pass. Independent
  review approves with no actionable findings. `agent-toolkit check` is unavailable.
  Tests cover prompt requests only; no real model-language compliance is claimed.
