# Relevant external source selection

2026-10-18. Owner asks to use Jev to choose research sites after a saved X
assessment lists unrelated retail/seller pages. The supplied Langfuse screenshot
shows these URLs in Brave search.response, before assessment generation.

Observed repository cause: ProcessingService.research uses the last URL path
component as the query; the submitted X URL therefore produces a numeric post ID.
BraveSearch retains URLs only, and research filters readable/unique pages without
a topical relevance check. This is search orchestration, not a model choosing Walmart.

Success: topic-based queries; Jev selects topical candidate sites before downloads;
unrelated/uncertain candidates never become comparison evidence. Preserve source
fetch safety, owner scope, monthly budget, one-search cap and no paid retries.
Avoid a retailer blacklist: relevance depends on the article topic. Existing
saved assessments are not silently rewritten or reprocessed.
