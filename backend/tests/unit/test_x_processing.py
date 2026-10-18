import asyncio
import json
from dataclasses import replace
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

import httpx
import pytest

from linksifty.application.processing_contracts import (
    AssessmentProvider,
    ProcessingJob,
    ProcessingStore,
)
from linksifty.application.processing_service import ProcessingService
from linksifty.config import Settings
from linksifty.domain.acquisition import FetchFailure, FetchResult
from linksifty.infrastructure.x_adapter import XAdapter
from linksifty.main import create_app


@pytest.mark.parametrize(
    "admitted,reason", [(False, "x_attempt_uncertain"), (True, "x_access_denied")]
)
def test_x_failure_or_prior_attempt_never_calls_model(
    admitted: bool, reason: str, caplog: pytest.LogCaptureFixture
) -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.begin_x_fetch.return_value = admitted
        provider = create_autospec(AssessmentProvider, instance=True)
        ordinary_fetch = AsyncMock()
        x_fetch = AsyncMock(return_value=FetchResult(failure=FetchFailure.X_ACCESS_DENIED))
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            original_url="https://x.com/user/status/100",
        )
        service = ProcessingService(
            cast(ProcessingStore, store),
            cast(AssessmentProvider, provider),
            ordinary_fetch,
            x_fetch=x_fetch,
        )
        await service.process(job)
        ordinary_fetch.assert_not_awaited()
        assert x_fetch.await_count == int(admitted)
        store.begin_x_fetch.assert_awaited_once_with(job)
        store.stage.assert_awaited_with(job, reason, "awaiting_manual_content")
        store.save_source.assert_not_awaited()
        store.reserve.assert_not_awaited()
        provider.assess.assert_not_awaited()
        assert f"source_fetch_failed job_id={job.id} provider=x reason={reason}" in caplog.text
        assert job.original_url not in caplog.text

    asyncio.run(run())


def test_unconfigured_x_does_not_consume_attempt_or_fetch_html() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        provider = create_autospec(AssessmentProvider, instance=True)
        fetch = AsyncMock()
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            original_url="https://x.com/user/status/100",
        )
        await ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), fetch
        ).process(job)
        store.stage.assert_awaited_with(job, "x_not_configured", "awaiting_manual_content")
        store.begin_x_fetch.assert_not_awaited()
        fetch.assert_not_awaited()
        provider.assess.assert_not_awaited()

    asyncio.run(run())


def test_x_content_is_cached_before_model_budget_and_cache_is_reused() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.begin_x_fetch.return_value = True
        store.save_source.return_value = True
        store.reserve.return_value = None
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.estimate.return_value = Decimal("0.02")
        text = "Complete source evidence with practical, reproducible examples. " * 10
        x_fetch = AsyncMock(return_value=FetchResult(text=text))
        fetch = AsyncMock()
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            original_url="https://x.com/user/status/100",
        )
        service = ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), fetch, x_fetch=x_fetch
        )
        await service.process(job)
        store.save_source.assert_awaited_once_with(job, text)
        job.source_text = text
        await service.process(job)
        x_fetch.assert_awaited_once()
        store.begin_x_fetch.assert_awaited_once()
        fetch.assert_not_awaited()

    asyncio.run(run())


@pytest.mark.parametrize("enabled", [False, True])
def test_runtime_wires_x_only_after_operator_enablement(enabled: bool) -> None:
    paths: list[str] = []
    saved: list[str] = []
    text = "A complete public post with practical evidence and examples. " * 10

    def respond(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.host == "api.x.com":
            assert request.headers["authorization"] == "Bearer test-x-token"
            assert "apikey" not in request.headers
            if request.url.path == "/2/tweets/100":
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "id": "100",
                            "author_id": "50",
                            "conversation_id": "100",
                            "text": text,
                        }
                    },
                )
            assert request.url.path == "/2/tweets/search/all"
            return httpx.Response(200, json={"meta": {"result_count": 0}})
        assert request.url.host == "supabase.example"
        assert "test-x-token" not in request.headers.get("authorization", "")
        if request.url.path.endswith("begin_x_fetch"):
            return httpx.Response(200, json=[{"admitted": True}])
        if request.url.path.endswith("save_job_source"):
            saved.append(json.loads(request.content)["p_text"])
        if request.url.path.endswith("reserve_analysis"):
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=[{}])

    async def run() -> None:
        config = replace(
            Settings.for_test(),
            demo_mode=False,
            x_api_bearer_token="test-x-token",
            x_api_reads_enabled=enabled,
        )
        app = create_app(config, transport=httpx.MockTransport(respond))
        async with app.router.lifespan_context(app):
            processor = cast(ProcessingService, app.state.processing)
            job = ProcessingJob(
                id=uuid4(),
                item_id=uuid4(),
                user_id=uuid4(),
                lease_token=uuid4(),
                original_url="https://x.com/user/status/100",
            )
            await processor.process(job)

    asyncio.run(run())
    assert ("/rest/v1/rpc/begin_x_fetch" in paths) is enabled
    assert ("/2/tweets/100" in paths) is enabled
    assert len(saved) == int(enabled)
    if enabled:
        assert text in saved[0]


def test_short_x_post_is_not_padded_into_passing_completeness() -> None:
    async def run() -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/2/tweets/100":
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "id": "100",
                            "author_id": "50",
                            "conversation_id": "100",
                            "text": "Short post",
                        }
                    },
                )
            return httpx.Response(200, json={"meta": {"result_count": 0}})

        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.begin_x_fetch.return_value = True
        provider = create_autospec(AssessmentProvider, instance=True)
        adapter = XAdapter("test-x-token", transport=httpx.MockTransport(respond))
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            original_url="https://x.com/user/status/100",
        )
        await ProcessingService(
            cast(ProcessingStore, store),
            cast(AssessmentProvider, provider),
            AsyncMock(),
            x_fetch=adapter.fetch,
        ).process(job)
        store.save_source.assert_not_awaited()
        provider.assess.assert_not_awaited()
        store.stage.assert_awaited_with(job, "too_short", "awaiting_manual_content")

    asyncio.run(run())
