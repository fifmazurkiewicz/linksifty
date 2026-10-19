import asyncio
import json
from decimal import Decimal
from unittest.mock import create_autospec

import httpx
import pytest
from langfuse import Langfuse

from linksifty.application.chat_contracts import ChatCitation, ChatInput
from linksifty.infrastructure.langfuse_telemetry import LangfuseTelemetry
from linksifty.infrastructure.openrouter_client import OpenRouterClient


def test_sonnet_chat_routes_latest_polish_question_with_separate_cost_bound() -> None:
    async def run() -> None:
        calls = []
        sdk = create_autospec(Langfuse, instance=True)

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            body = json.loads(request.content)
            assert body["model"] == "anthropic/claude-sonnet-5.5"
            assert body["max_tokens"] == 8192
            assert body["reasoning"] == {"effort": "low", "exclude": True}
            assert body["provider"]["max_price"] == {"prompt": 2, "completion": 10, "request": 0}
            assert body["provider"]["require_parameters"] is True
            assert body["provider"]["allow_fallbacks"] is False
            prompt = body["messages"][0]["content"]
            assert "2–4 sentences" in prompt and "ambiguous" in prompt
            assert "Do not retell the saved summary" in prompt
            context = json.loads(body["messages"][-1]["content"])
            assert context["question"] == "do czego to służy?"
            assert context["reply_language"] == "pl"
            assert context["history"][-1]["content"] == "Earlier generic English summary"
            return httpx.Response(
                200,
                json={
                    "id": "gen-sonnet",
                    "usage": {"cost": "0.012"},
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {
                                "content": json.dumps(
                                    {
                                        "search_query": None,
                                        "paragraphs": [
                                            {
                                                "text": "Ulepsza narzędzia i instrukcje agenta.",
                                                "passage_ids": ["primary:1"],
                                            }
                                        ],
                                        "insufficient": False,
                                    }
                                )
                            },
                        }
                    ],
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = OpenRouterClient(
                "test",
                "openai/gpt-4o-mini",
                client,
                LangfuseTelemetry(sdk),
                chat_model="anthropic/claude-sonnet-5.5",
            )
            assert provider.estimate("") == Decimal("0.14848")
            assert provider.chat_estimate() == Decimal("2.08192")
            result = await provider.reply(
                ChatInput(
                    question="do czego to służy?",
                    reply_language="pl",
                    passages={
                        "primary:1": ChatCitation(
                            passage_id="primary:1",
                            excerpt="Improves the tools and instructions of agents.",
                        )
                    },
                    history=[{"role": "assistant", "content": "Earlier generic English summary"}],
                ),
                allow_search=False,
            )
        assert result.cost == Decimal("0.012") and result.draft
        assert result.draft.paragraphs[0].passage_ids == ["primary:1"]
        assert len(calls) == 1
        assert sdk.start_observation.call_args.kwargs["model"] == "anthropic/claude-sonnet-5.5"

    asyncio.run(run())


def test_unverified_chat_model_fails_before_http() -> None:
    async def run() -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            raise AssertionError("Unverified model must not make a paid request")

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = OpenRouterClient(
                "test", "openai/gpt-4o-mini", client, chat_model="unknown/model"
            )
            with pytest.raises(ValueError, match="verified"):
                provider.chat_estimate()
            with pytest.raises(ValueError, match="verified"):
                await provider.reply(
                    ChatInput(question="Why?", passages={}, history=[]), allow_search=True
                )

    asyncio.run(run())


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
            assert "including every subject in a comparison" in prompt
            assert "Earlier research does not establish" in prompt
            assert "search_queries" in prompt
            assert "Never replace an unanswered question with a summary" in prompt
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
@pytest.mark.parametrize("chat_model", ["openai/gpt-4o-mini", "anthropic/claude-sonnet-5.5"])
def test_invalid_or_rejected_chat_preserves_cost_without_retry(
    status: int, body: dict[str, object], cost: Decimal | None, chat_model: str
) -> None:
    async def run() -> None:
        calls = []

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(status, json=body)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient(
                "test", "openai/gpt-4o-mini", client, chat_model=chat_model
            ).reply(ChatInput(question="Why?", passages={}, history=[]), allow_search=True)
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
