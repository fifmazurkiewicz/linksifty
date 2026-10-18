import asyncio
import json
from decimal import Decimal

import httpx
import pytest

from linksifty.application.chat_contracts import ChatInput
from linksifty.infrastructure.openrouter_client import OpenRouterClient


@pytest.mark.parametrize("allow_search", [True, False])
def test_chat_request_constrains_search_grounding_output_and_cost(allow_search: bool) -> None:
    async def run() -> None:
        requests = []

        def respond(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            requests.append(body)
            prompt = body["messages"][0]["content"]
            assert "untrusted data" in prompt
            assert "ONLY the supplied evidence" in prompt
            assert "Previous assistant answers" in prompt
            assert ("ONE" if allow_search else "search_query MUST be null") in prompt
            assert body["provider"]["allow_fallbacks"] is False
            assert body["max_tokens"] == 4096
            assert body["response_format"]["json_schema"]["strict"] is True
            return httpx.Response(
                200,
                json={
                    "id": "gen-chat",
                    "usage": {"cost": 0.001},
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {
                                "content": json.dumps(
                                    {"search_query": None, "paragraphs": [], "insufficient": True}
                                )
                            },
                        }
                    ],
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = OpenRouterClient("test-key", "openai/gpt-4o-mini", client)
            result = await provider.reply(
                ChatInput(question="Why?", history=[], passages={}), allow_search=allow_search
            )
        assert len(requests) == 1
        assert result.draft and result.draft.insufficient
        assert result.generation_id == "gen-chat"
        assert result.cost == Decimal("0.001")

    asyncio.run(run())


@pytest.mark.parametrize(
    "status,body,cost",
    [
        (
            200,
            {
                "id": "gen-bad",
                "usage": {"cost": 0.002},
                "choices": [{"finish_reason": "length", "message": {"content": "{}"}}],
            },
            Decimal("0.002"),
        ),
        (
            200,
            {
                "id": "gen-bad",
                "usage": {"cost": 0.003},
                "choices": [{"finish_reason": "stop", "message": {"content": "invalid json"}}],
            },
            Decimal("0.003"),
        ),
        (429, {"error": "rate limited"}, Decimal(0)),
        (503, {"error": "uncertain"}, None),
    ],
)
def test_invalid_or_rejected_chat_preserves_cost_without_retry(
    status: int, body: dict[str, object], cost: Decimal | None
) -> None:
    async def run() -> None:
        calls = []

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(status, json=body)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).reply(
                ChatInput(question="Why?", passages={}, history=[]), allow_search=True
            )
        assert result.draft is None and result.failure_reason
        assert result.cost == cost
        assert len(calls) == 1

    asyncio.run(run())


def test_oversized_chat_context_never_makes_a_paid_request() -> None:
    async def run() -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            raise AssertionError("No paid call is allowed")

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).reply(
                ChatInput(question="a" * 120000, passages={}, history=[]), allow_search=True
            )
        assert result.cost == 0
        assert result.failure_reason == "input_too_large"

    asyncio.run(run())
