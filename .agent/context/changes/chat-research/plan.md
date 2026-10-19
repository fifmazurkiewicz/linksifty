# Approved chat research change

The latest comparison question was sent correctly but the model repeated a saved
summary even though no supplied passage described the comparison subject.

Use the existing ChatService/OpenRouter/Brave/Supabase boundaries. Require the
model to identify missing evidence, search specifically for it, and reassess.
Allow at most two distinct public queries per question, with one refined query
only after a confirmed first search and an explicit remaining evidence gap.
Earlier turns never consume a new question's allowance. Ambiguous subjects need
clarification before search. Keep short direct answers and explicit reply language.

Extend the existing unique reservation slots with search_refined and answer_final;
retain classification, decision, search and answer. Each query and generation
reserves independently under the same owner budget lock. Duplicate request IDs,
uncertain calls, failed providers and exhausted budgets never cause paid retries.
Only complete fetched pages supply evidence. Keep cumulative research sources
when a later call fails. Give new turns eight minutes for the bounded three-model,
two-search path. Existing pending turns retain their original deadline.

Trade-off: a second search adds latency and charges; the UI must disclose two
possible search charges and up to three answer-model calls. Reuse evidence from
earlier turns and do not add an evaluator call, framework or dependency. Tests
mock every paid provider and separately exercise SQL admission/concurrency.

Acceptance: zero-search answers; one-search answers; two distinct searches then
search disabled; no third or repeated query; no continuation after uncertain
search; second-search budget denial; prior-history searches do not block a new
question; known final citation IDs, language propagation and source retention;
database owner, order, settlement, budget and replay fences; disclosure, tests,
documentation and workflow diagram current. Review then push the related changes.
