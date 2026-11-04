# Progress

2026-11-04: frontend-only scope confirmed. Caught HTTP/network/parsing/stream failures now report through the existing privacy-filtered SDK, while normal4xx/cancellation stay silent. Local evidence and independent source review are complete. Publication/CI and updated public artifact are in progress.

A single synthetic diagnostic through the frontend adapter was accepted in `linksifty-web`, environment `test`, event `6b10529bc6bf40a7b0d3ec59072c4760`. This used an isolated Node process, not the user's Safari. It verifies the adapter/key/ingestion; it does not verify Safari-specific blocking or the backend. Backend/Render changes are explicitly outside the owner-selected scope.

[Plan](plan.md) · [Evidence](evidence.md) · [Review decisions](reviews/review-decisions.md).
