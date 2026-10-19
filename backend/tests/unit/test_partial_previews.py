import asyncio
import json
from decimal import Decimal
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from linksifty.api.auth import current_user
from linksifty.application.item_contracts import ItemRecord
from linksifty.application.item_service import ItemService
from linksifty.application.processing_contracts import (
    AssessmentProvider,
    ModelResult,
    ProcessingJob,
    ProcessingStore,
)
from linksifty.application.processing_service import ProcessingService
from linksifty.config import Settings
from linksifty.domain.acquisition import FetchFailure, FetchResult
from linksifty.infrastructure.http_fetcher import fetch_public_text
from linksifty.infrastructure.openrouter_client import OpenRouterClient
from linksifty.infrastructure.x_adapter import XAdapter
from linksifty.main import create_app

TEXT = "A guide to organizing email into a file-based knowledge library. " * 8
OVERVIEW = "The fetched text describes a file-based knowledge library for organizing email."


def test_failed_x_read_preserves_only_reachable_readable_text() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/100"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "100",
                        "author_id": "50",
                        "conversation_id": "100",
                        "text": "Article teaser",
                        "referenced_tweets": [{"type": "quoted", "id": "90"}],
                    },
                    "includes": {
                        "tweets": [
                            {
                                "id": "90",
                                "author_id": "70",
                                "conversation_id": "90",
                                "text": "Preview…",
                                "article": {
                                    "title": "Email library",
                                    "plain_text": TEXT,
                                    "entities": {"tweets": [{"id": "80"}]},
                                },
                            },
                            {
                                "id": "999",
                                "author_id": "99",
                                "conversation_id": "999",
                                "text": "UNRELATED MATERIAL",
                            },
                        ]
                    },
                },
            )
        return httpx.Response(404)

    result = asyncio.run(
        XAdapter("test", transport=httpx.MockTransport(respond)).fetch(
            "https://x.com/user/status/100"
        )
    )
    assert result.text is None and result.failure is not None
    assert TEXT.strip() in (result.partial_text or "")
    assert "UNRELATED MATERIAL" not in (result.partial_text or "")


def test_x_partial_api_error_can_preview_validated_matching_post_text() -> None:
    def respond(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {"id": "100", "author_id": "50", "conversation_id": "100", "text": TEXT},
                "errors": [{"title": "Some requested context is unavailable"}],
            },
        )

    result = asyncio.run(
        XAdapter("test", transport=httpx.MockTransport(respond)).fetch(
            "https://x.com/user/status/100"
        )
    )
    assert result.failure == FetchFailure.PARTIAL and result.text is None
    assert TEXT.strip() == result.partial_text


def test_missing_repost_original_still_has_a_preview_of_returned_rt_text() -> None:
    def respond(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {
                    "id": "100",
                    "author_id": "50",
                    "conversation_id": "100",
                    "text": "RT @author: Building an email knowledge library…",
                    "referenced_tweets": [{"type": "retweeted", "id": "90"}],
                }
            },
        )

    result = asyncio.run(
        XAdapter("test", transport=httpx.MockTransport(respond)).fetch(
            "https://x.com/user/status/100"
        )
    )
    assert result.text is None and result.failure == FetchFailure.PARTIAL
    assert "email knowledge library" in (result.partial_text or "")


@pytest.mark.parametrize("status,html", [(200, "<html><body>" + TEXT), (206, TEXT)])
def test_partial_web_body_is_preview_only(status: int, html: str) -> None:
    result = asyncio.run(
        fetch_public_text(
            "https://8.8.8.8/article",
            transport=httpx.MockTransport(
                lambda _: httpx.Response(status, text=html, headers={"content-type": "text/html"})
            ),
        )
    )
    assert result.text is None and result.failure == FetchFailure.PARTIAL
    assert TEXT.strip() in (result.partial_text or "")


@pytest.mark.parametrize(
    "admitted,cost", [(False, Decimal("0.001")), (True, Decimal("0.001")), (True, None)]
)
def test_partial_preview_uses_budget_without_assessing(
    admitted: bool, cost: Decimal | None
) -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        reservation = uuid4()
        store.reserve_preview.return_value = reservation if admitted else None
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.estimate.return_value = Decimal("0.14848")
        result = ModelResult(overview=OVERVIEW, generation_id="gen-preview", cost=cost)
        provider.preview.return_value = result
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            original_url="https://example.test/a",
        )
        fetch = AsyncMock(return_value=FetchResult(failure=FetchFailure.PARTIAL, partial_text=TEXT))
        await ProcessingService(store, provider, fetch).process(job)
        provider.assess.assert_not_awaited()
        store.save_source.assert_not_awaited()
        store.complete.assert_not_awaited()
        store.stage.assert_any_await(job, "partial_content", "awaiting_manual_content")
        if admitted:
            provider.preview.assert_awaited_once_with(TEXT)
            store.record_preview.assert_awaited_once_with(job, reservation, result)
            if cost is not None:
                store.settle.assert_awaited_once_with(job.user_id, reservation, cost)
            else:
                store.settle.assert_not_awaited()
        else:
            provider.preview.assert_not_awaited()

    asyncio.run(run())


@pytest.mark.parametrize(
    "overview,finish",
    [(OVERVIEW, "stop"), ("bad\nline", "stop"), ("", "stop"), (OVERVIEW, "length")],
)
def test_model_preview_is_bounded_and_retains_cost_on_invalid_output(
    overview: str, finish: str
) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = json.loads(request.content)
        assert body["max_tokens"] == 192 and body["provider"]["allow_fallbacks"] is False
        assert set(body["response_format"]["json_schema"]["schema"]["properties"]) == {"overview"}
        assert "incomplete" in body["messages"][0]["content"].lower()
        return httpx.Response(
            200,
            json={
                "id": "gen-preview",
                "usage": {"cost": "0.0001"},
                "choices": [
                    {
                        "finish_reason": finish,
                        "message": {"content": json.dumps({"overview": overview})},
                    }
                ],
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).preview(TEXT)
        assert result.overview == (OVERVIEW if overview == OVERVIEW and finish == "stop" else None)
        assert result.cost == Decimal("0.0001") and result.generation_id == "gen-preview"
        assert result.assessment is None and calls == 1

    asyncio.run(run())


@pytest.mark.parametrize("allowed", [False, True, "true"])
def test_submission_and_retry_require_explicit_typed_preview_consent(allowed: object) -> None:
    user, identifier = uuid4(), uuid4()
    record = ItemRecord(id=identifier, user_id=user, title="Source", status="queued", unread=True)
    service = create_autospec(ProcessingService, instance=True)
    service.resume.return_value = record
    items = create_autospec(ItemService, instance=True)
    items.submit.return_value = [record]
    app = create_app(Settings())
    app.state.items = items
    app.state.processing = service
    app.dependency_overrides[current_user] = lambda: user
    client = TestClient(app)
    response = client.post(
        "/v1/items",
        json={"sources": [{"url": "https://example.test/a"}], "allow_partial_preview": allowed},
    )
    retry = client.post(f"/v1/items/{identifier}/resume", json={"allow_partial_preview": allowed})
    if isinstance(allowed, str):
        assert response.status_code == retry.status_code == 422
        service.resume.assert_not_awaited()
    else:
        assert response.status_code == retry.status_code == 202
        if allowed:
            items.submit.assert_awaited_once_with(
                user, ["https://example.test/a"], allow_partial_preview=True
            )
            service.resume.assert_awaited_once_with(user, identifier, allow_partial_preview=True)
        else:
            service.resume.assert_awaited_once_with(user, identifier)


@pytest.mark.parametrize("partial", [None, "", "   "])
def test_missing_readable_text_never_admits_a_preview(partial: str | None) -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        provider = create_autospec(AssessmentProvider, instance=True)
        job = ProcessingJob(id=uuid4(), item_id=uuid4(), user_id=uuid4(), lease_token=uuid4())
        await ProcessingService(
            store,
            provider,
            AsyncMock(return_value=FetchResult(failure=FetchFailure.PARTIAL, partial_text=partial)),
        ).process(job)
        store.reserve_preview.assert_not_awaited()
        provider.preview.assert_not_awaited()
        provider.assess.assert_not_awaited()

    asyncio.run(run())


@pytest.mark.parametrize("kind", ["truncated", "unknown_entities", "withheld"])
def test_x_fragment_fallback_is_bounded_and_excludes_withheld_content(kind: str) -> None:
    def respond(_: httpx.Request) -> httpx.Response:
        data: dict[str, object] = {
            "id": "100",
            "author_id": "50",
            "conversation_id": "100",
            "text": "Short teaser",
            "article": {"title": "Available title", "plain_text": TEXT * 30 + "…", "entities": {}},
        }
        if kind == "unknown_entities":
            data["article"] = {
                "title": "Available title",
                "plain_text": TEXT * 30,
                "entities": {"unrecognized": []},
            }
        if kind == "withheld":
            data["withheld"] = {"country_codes": ["XX"]}
        return httpx.Response(200, json={"data": data})

    result = asyncio.run(
        XAdapter("test", transport=httpx.MockTransport(respond)).fetch(
            "https://x.com/user/status/100"
        )
    )
    assert result.text is None and result.failure is not None
    if kind == "withheld":
        assert result.partial_text is None
    else:
        assert (result.partial_text or "").startswith("Available title")
        assert len(result.partial_text or "") <= 6000


def test_partial_html_never_sends_scripts_or_navigation_as_preview() -> None:
    result = asyncio.run(
        fetch_public_text(
            "https://8.8.8.8/a",
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    206,
                    text="<html><script>SECRET SCRIPT</script><nav>Navigation</nav><body>" + TEXT,
                    headers={"content-type": "text/html"},
                )
            ),
        )
    )
    assert result.text is None
    assert TEXT.strip() in (result.partial_text or "")
    assert "SCRIPT" not in (result.partial_text or "") and "Navigation" not in (
        result.partial_text or ""
    )
