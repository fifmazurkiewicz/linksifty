"""Bounded search discovery. Search snippets are never evidence or persisted."""

import httpx

from linksifty.application.research_contracts import SearchResponse
from linksifty.infrastructure.langfuse_telemetry import LangfuseTelemetry


class BraveSearch:
    def __init__(
        self, key: str, client: httpx.AsyncClient, *, telemetry: LangfuseTelemetry | None = None
    ) -> None:
        self._telemetry = telemetry or LangfuseTelemetry()
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
                self._telemetry.event("brave.http_response", {"status_code": response.status_code})
                if response.status_code != 200:
                    return SearchResponse()  # Never assume an unsuccessful request was free.
                confirmed = True
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 500000:
                        self._telemetry.event("brave.invalid_response", {"reason": "too_large"})
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
        except (httpx.HTTPError, ValueError) as error:
            self._telemetry.event(
                "brave.request_failed", {"exception": type(error).__name__, "confirmed": confirmed}
            )
            return SearchResponse(confirmed=confirmed)
