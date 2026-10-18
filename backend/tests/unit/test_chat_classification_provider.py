import asyncio
import json
from decimal import Decimal

import httpx
import pytest

from linksifty.application.chat_contracts import ChatCitation, ChatInput
from linksifty.infrastructure.openrouter_client import OpenRouterClient


def decision_body(category: str = "relevant", language: str = "pl") -> dict[str, object]:
    return {
        "id": "gen-dec-test",
        "usage": {"cost": 0.00002},
        "answers": {
            "scope": {
                "type": "choice",
                "choice": category,
                "confidence": 0.99,
                "probabilities": {
                    key: int(key == category) for key in ("relevant", "off_topic", "unsafe")
                },
            },
            "language": {
                "type": "choice",
                "choice": language,
                "confidence": 1,
                "probabilities": {"pl": int(language == "pl"), "en": int(language == "en")},
            },
        },
    }


@pytest.mark.parametrize("category", ["relevant", "off_topic", "unsafe"])
def test_jev_uses_decisions_api_with_bounded_topic_history_and_cost_caps(category: str) -> None:
    async def run() -> None:
        calls = []

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            assert str(request.url) == "https://openrouter.ai/api/alpha/decisions"
            body = json.loads(request.content)
            assert body["model"] == "typesafe/jev-1.13"
            assert body["provider"]["allow_fallbacks"] is False
            assert body["provider"]["max_price"] == {"prompt": 0.042, "completion": 0, "request": 0}
            assert set(body["questions"]["scope"]["criteria"]) == {
                "relevant",
                "off_topic",
                "unsafe",
            }
            assert "untrusted data" in body["questions"]["scope"]["instructions"]
            assert "unsafe takes precedence" in body["questions"]["scope"]["instructions"]
            assert body["state"]["question"] == "gdzie mogę założyć ike?"
            assert "IKE" in body["state"]["original"]
            assert body["state"]["history"][0]["content"] == "Co to jest IKE?"
            assert "foreign.test" not in json.dumps(body["state"])
            assert len(request.content) < 32000
            return httpx.Response(200, json=decision_body(category))

        payload = ChatInput(
            question="gdzie mogę założyć ike?",
            passages={
                "primary:1": ChatCitation(
                    passage_id="primary:1", excerpt="IKE to konto emerytalne. " * 1000
                ),
                "analysis:1": ChatCitation(
                    passage_id="analysis:1", excerpt="Saved analysis of IKE"
                ),
                "chat1:1": ChatCitation(
                    passage_id="chat1:1",
                    excerpt="Unrelated old research",
                    source_url="https://foreign.test",
                ),
            },
            history=[{"role": "user", "content": "Co to jest IKE?"}],
        )
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = OpenRouterClient("test-key", "openai/gpt-4o-mini", client)
            assert provider.classification_estimate() == Decimal("0.002688")
            result = await provider.classify(payload)
        assert result.classification and result.classification.category == category
        assert result.classification.language == "pl"
        assert result.generation_id == "gen-dec-test" and result.cost == Decimal("0.00002")
        assert len(calls) == 1

    asyncio.run(run())


@pytest.mark.parametrize(
    "change",
    [
        {"choice": "other"},
        {"type": "noul"},
        {"confidence": 0.1},
        {"confidence": True},
        {"probabilities": {"relevant": 1}},
        {"probabilities": {"relevant": -1, "off_topic": 1, "unsafe": 1}},
        {"probabilities": {"relevant": 0, "off_topic": 0, "unsafe": 1}},
        {"probabilities": {"relevant": 1, "off_topic": 1, "unsafe": 1}},
        {"probabilities": {"relevant": True, "off_topic": 0, "unsafe": 0}},
    ],
)
def test_invalid_or_uncertain_classification_preserves_charge_and_never_retries(
    change: dict[str, object],
) -> None:
    async def run() -> None:
        calls = []
        body = decision_body()
        body["answers"]["scope"].update(change)

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(200, json=body)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).classify(
                ChatInput(question="Why?", passages={}, history=[])
            )
        assert result.classification is None and result.failure_reason
        assert result.cost == Decimal("0.00002") and result.generation_id == "gen-dec-test"
        assert len(calls) == 1

    asyncio.run(run())


@pytest.mark.parametrize("status,cost", [(429, Decimal(0)), (503, None)])
def test_classifier_http_failures_keep_unknown_cost_reserved(
    status: int, cost: Decimal | None
) -> None:
    async def run() -> None:
        calls = []

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(status, json={"error": "unavailable"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).classify(
                ChatInput(question="Why?", passages={}, history=[])
            )
        assert result.classification is None and result.failure_reason == "provider_rejected"
        assert result.cost == cost and len(calls) == 1

    asyncio.run(run())


def test_oversized_question_and_transport_error_cannot_bypass_classification() -> None:
    async def run() -> None:
        calls = []

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            raise httpx.ReadTimeout("Uncertain outcome")

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = OpenRouterClient("test", "openai/gpt-4o-mini", client)
            oversized = await provider.classify(
                ChatInput(question="a" * 32000, passages={}, history=[])
            )
            assert oversized.cost == 0 and oversized.failure_reason == "input_too_large"
            assert not calls
            failed = await provider.classify(ChatInput(question="Why?", passages={}, history=[]))
            assert failed.cost is None and failed.failure_reason == "provider_unreachable"
            assert len(calls) == 1

    asyncio.run(run())
