import asyncio
import json
from decimal import Decimal
from unittest.mock import AsyncMock, create_autospec
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

from linksifty.api.auth import current_user
from linksifty.application.processing_contracts import (
    AssessmentProvider,
    ModelResult,
    ProcessingStore,
)
from linksifty.application.processing_service import ProcessingService
from linksifty.config import Settings
from linksifty.domain.models import CriterionName
from linksifty.infrastructure.openrouter_client import OpenRouterClient
from linksifty.main import create_app

USER = UUID("11111111-1111-4111-8111-111111111111")
ITEM = UUID("22222222-2222-4222-8222-222222222222")
TEXT = "Complete source text about running small language models locally. " * 10
TITLE = "Running small language models locally"


@pytest.mark.parametrize("invalid", [False, True])
def test_analysis_returns_a_title_even_when_citations_fail(invalid: bool) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = json.loads(request.content)
        assert "title" in body["response_format"]["json_schema"]["schema"]["required"]
        payload = {
            "title": TITLE,
            "note": "Source-grounded note",
            "criteria": [
                {
                    "name": n.value,
                    "score": 3,
                    "rationale": "Supported",
                    "passage_id": "invented:99" if invalid else "primary:1",
                }
                for n in CriterionName
            ],
        }
        return httpx.Response(
            200,
            json={
                "id": "gen-title",
                "usage": {"cost": "0.0001"},
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}],
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess(TEXT)
        assert result.title == TITLE
        assert (result.assessment is None) is invalid
        assert result.cost == Decimal("0.0001")
        assert calls == 1

    asyncio.run(run())


@pytest.mark.parametrize("title", [TITLE, "   ", "x" * 161, "bad\x00title", "bad\nheading"])
def test_title_only_call_is_bounded_and_validated(title: str) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["max_tokens"] == 128
        assert body["provider"]["allow_fallbacks"] is False
        assert set(body["response_format"]["json_schema"]["schema"]["properties"]) == {"title"}
        assert json.loads(body["messages"][-1]["content"])["text"] == TEXT
        return httpx.Response(
            200,
            json={
                "id": "gen-title-only",
                "usage": {"cost": "0.0001"},
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps({"title": title})}}
                ],
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).title(TEXT)
        assert result.title == (TITLE if title == TITLE else None)
        assert result.cost == Decimal("0.0001")
        assert result.generation_id == "gen-title-only"
        assert result.assessment is None

    asyncio.run(run())


def test_title_endpoint_requires_confirmation_and_uses_authenticated_owner() -> None:
    service = create_autospec(ProcessingService, instance=True)
    service.generate_title.return_value = TITLE
    app = create_app(Settings(demo_mode=True))
    app.state.processing = service
    app.dependency_overrides[current_user] = lambda: USER
    client = TestClient(app)
    for payload in (
        {},
        {"confirmed": False},
        {"confirmed": "true"},
        {"confirmed": True, "user_id": str(ITEM)},
    ):
        assert client.post(f"/v1/items/{ITEM}/title", json=payload).status_code == 422
    service.generate_title.assert_not_awaited()
    response = client.post(f"/v1/items/{ITEM}/title", json={"confirmed": True})
    assert response.status_code == 200
    assert response.json() == {"title": TITLE}
    service.generate_title.assert_awaited_once_with(USER, ITEM)
    assert (
        TestClient(create_app(Settings()))
        .post(f"/v1/items/{ITEM}/title", json={"confirmed": True})
        .status_code
        == 401
    )


@pytest.mark.parametrize("admitted", [False, True])
def test_title_generation_reserves_before_call_and_does_not_rerun_analysis(admitted: bool) -> None:
    from linksifty.application.processing_contracts import TitleGenerationError, TitleReservation

    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.estimate.return_value = Decimal("0.14848")
        store.reserve_title.return_value = (
            TitleReservation(id=ITEM, text=TEXT) if admitted else None
        )
        provider.title.return_value = ModelResult(
            title=TITLE, generation_id="gen-backfill", cost=Decimal("0.0001")
        )
        store.record_title.return_value = True
        service = ProcessingService(store, provider, AsyncMock())
        if admitted:
            assert await service.generate_title(USER, ITEM) == TITLE
            provider.title.assert_awaited_once_with(TEXT)
            store.record_title.assert_awaited_once_with(
                USER, ITEM, ITEM, provider.title.return_value
            )
            store.settle.assert_awaited_once_with(USER, ITEM, Decimal("0.0001"))
        else:
            with pytest.raises(TitleGenerationError):
                await service.generate_title(USER, ITEM)
            provider.title.assert_not_awaited()
            store.settle.assert_not_awaited()
        store.reserve_title.assert_awaited_once_with(USER, ITEM, Decimal("0.14848"))
        provider.assess.assert_not_awaited()
        store.complete.assert_not_awaited()

    asyncio.run(run())


@pytest.mark.parametrize("cost", [None, Decimal("0.0001")])
def test_failed_title_generation_retains_generation_and_only_settles_known_cost(
    cost: Decimal | None,
) -> None:
    from linksifty.application.processing_contracts import TitleGenerationError, TitleReservation

    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.estimate.return_value = Decimal("0.14848")
        store.reserve_title.return_value = TitleReservation(id=ITEM, text=TEXT)
        result = ModelResult(
            generation_id="gen-invalid-title", cost=cost, failure_reason="invalid_title"
        )
        provider.title.return_value = result
        store.record_title.return_value = False
        with pytest.raises(TitleGenerationError):
            await ProcessingService(store, provider, AsyncMock()).generate_title(USER, ITEM)
        provider.title.assert_awaited_once_with(TEXT)
        store.record_title.assert_awaited_once_with(USER, ITEM, ITEM, result)
        if cost is None:
            store.settle.assert_not_awaited()
        else:
            store.settle.assert_awaited_once_with(USER, ITEM, cost)

    asyncio.run(run())
