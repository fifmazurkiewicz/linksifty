"""Bounded search discovery. Search snippets are never evidence or persisted."""

import httpx

from linksifty.application.research_contracts import SearchResponse


class BraveSearch:
    def __init__(self, key: str, client: httpx.AsyncClient) -> None:
        self._key = key
        self._client = client

    async def search(self, query: str) -> SearchResponse:
        confirmed = False
        try:
            async with self._client.stream(
                "GET",
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self._key, "Accept": "application/json"},
                params={"q": query[:300], "count": "10", "safesearch": "strict"},
                timeout=15,
                follow_redirects=False,
            ) as response:
                if response.status_code != 200:
                    return SearchResponse()  # Never assume an unsuccessful request was free.
                confirmed = True
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 500000:
                        return SearchResponse(confirmed=True)
            import json

            data = json.loads(body)
            web = data.get("web", {}) if isinstance(data, dict) else {}
            results = web.get("results", []) if isinstance(web, dict) else []
            if not isinstance(results, list):
                return SearchResponse(confirmed=True)
            urls = tuple(
                row["url"]
                for row in results[:10]
                if isinstance(row, dict) and isinstance(row.get("url"), str)
            )
            return SearchResponse(confirmed=True, urls=urls)
        except (httpx.HTTPError, ValueError):
            return SearchResponse(confirmed=confirmed)
