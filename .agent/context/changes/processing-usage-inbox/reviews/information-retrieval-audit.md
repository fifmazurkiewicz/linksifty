# Information acquisition and checking audit — 2026-10-15

Outcome: **revise / full product retrieval scope incomplete**. Read-only code review against original MVP, completion plan C2/C3/C7 and narrower processing-usage scope. No implementation, hosted queries or paid calls performed. Graft unavailable; focused source/documentation reads used.

## Coverage

| Requirement | Evidence | Status |
| --- | --- | --- |
| Fetch submitted public HTTP/HTTPS page | infrastructure/http_fetcher.py, mocked DNS/transport tests | Implemented locally; screenshot suggests hosted pipeline progressed to paid attempt |
| Redirect/IP safety, body/time/MIME bounds, readable text | fetcher, domain/content_policy.py; 42 fetcher + 2 policy tests | Implemented; completeness is heuristic, not universal extraction/JS rendering |
| Blocked/partial/X/manual fallback | fetcher and processing_service.py | Implemented manual fallback; no official X adapter |
| Analyze single supplied text | OpenRouterClient.assess; eight-criterion schema | Implemented; screenshot has zero successful ready results, hosted acceptance unproven |
| Exact excerpts and persisted offsets | adapter validation + service citation construction | Implemented for the submitted source; text match does not establish factual truth |
| Deterministic score/verdict | domain/scoring.py, domain/models.py | Implemented with tests |
| Discover additional independent sources | No search adapter or search execution in main/service/provider | Missing in full product; explicitly excluded from latest narrow change |
| Fetch/check at most five external cited sources | Completion plan C7.2 planned; no implementation | Missing |
| Deduplicate reposts and track independent confirmation/conflict | No external-source pipeline/storage orchestration | Missing |
| Official X post/thread retrieval | No x_adapter.py; X requests manual text | Missing; C7.1 planned |
| Grounded follow-up/source-search chat | No chat service/routes/component execution | Missing; M6 planned |
| Live status for external searching | Only fetch/check/analyze/save stages exist | Missing with external search; existing stage stream does not perform search |

The model prompt says “Do not browse”; the request contains only supplied text, no search tools/plugins. The independent_corroboration rubric dimension therefore cannot be presented as proof that independent sites were consulted.

## REV-008 — broad source-checking scope remains absent (high)

The original product allows up to five relevant external sources for corroboration. C7.2/M6 remain planned and the latest processing scope explicitly excluded external search. This is an unfinished product capability, not proof that the narrow approved change was implemented incorrectly. Return to C7.2 planning: distinguish discovering sources from checking links already cited in an article; define provider, independence/dedup, source IDs/excerpts, max-five and shared cost bounds before implementation. Canonical disposition: review-decisions.md#rev-008--external-source-checking-absent.

## REV-009 — unusable provider output has no diagnostic category (medium)

OpenRouterClient.assess collapses non-stop completion, invalid schema, missing/duplicate criteria, missing exact excerpts, empty rationale/note and some HTTP failures to an assessment-less ModelResult. ProcessingService maps this to invalid_model_output. The supplied screenshot is consistent with this state and shows spent 0.00251 USD, reserved 0 and Ready 0, but does not identify the actual rejection reason or attribute spending to individual attempts. Paid work can be charged without an accepted result; this is correctly accounted but not diagnosable from current UI/logs. Add safe reason enums/metadata without raw prompts, personal content, provider payloads or secrets; test each rejection path, then use authorized hosted evidence to identify and fix the actual cause. Do not lower evidence validation or repeat paid attempts blindly. Canonical disposition: review-decisions.md#rev-009--opaque-model-output-rejection.

## Verification

Focused pytest: **62 passed** (fetcher 42, content policy 2, OpenRouter 5, processing service 9, scoring 4). These use mocks and do not prove real provider reliability or independent fact checking. This review changes documentation only. No new paid, hosted or browser execution. Existing unrelated release gates remain open.
