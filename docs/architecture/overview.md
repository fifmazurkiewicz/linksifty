# Linksifty architecture overview

## Boundaries

- **Web client:** future Vite and React TypeScript application in `web/`; responsible for UI and authenticated API calls only.
- **API:** FastAPI application in `src/linksifty/`; owns HTTP contracts, authorization checks, service composition, and error mapping.
- **Domain services:** fetching, assessment, scoring, chat, and processing lifecycle. They do not use FastAPI request or response types.
- **Scoring:** a pure function taking validated criterion scores and a user threshold. It has no database, LLM, network, or HTTP dependency.
- **Supabase:** Auth and PostgreSQL. RLS and API-side user-id filtering both prevent cross-user item access.
- **External integrations:** OpenRouter, X API, and article retrieval occur server-side through narrow adapters. Tests replace every adapter with fakes.
- **Worker:** future asynchronous processor changes item state after submission. The user need not remain on the page.

## Processing flow

1. Authenticated user submits one to five canonicalized links.
2. API checks user scope, pending/trial allowance, duplicate items, and remaining spend budget.
3. Worker fetches source content. Failed or incomplete retrieval changes the item to awaiting manual content and stops.
4. Validated content is assessed into a typed eight-criterion result. A pure scorer derives score and verdict.
5. The completed item, source provenance, assessment, and score are stored under the submitting user's ID.

## Trust boundaries

Links, fetched pages, pasted text, LLM responses, MCP outputs, and external API responses are untrusted input. Pydantic models validate every boundary. Credentials live only in server environment variables. Administrators manage account approval only; their role never grants access to other users’ links, notes, assessments, or chats.
