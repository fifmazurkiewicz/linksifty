import asyncio
import json
from decimal import Decimal

import httpx

from linksifty.application.processing_contracts import EvidenceSource
from linksifty.infrastructure.brave_client import BraveSearch
from linksifty.infrastructure.openrouter_client import OpenRouterClient


def test_brave_uses_header_auth_and_bounds_candidates() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Subscription-Token"] == "test-key"
        assert "test-key" not in str(request.url)
        assert request.url.params["count"] == "10"
        return httpx.Response(
            200,
            json={"web": {"results": [{"url": f"https://source{i}.example"} for i in range(20)]}},
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await BraveSearch("test-key", client).search("public claim")
            assert result.confirmed
            assert len(result.urls) == 10

    asyncio.run(run())


def test_provider_records_why_a_paid_response_was_rejected() -> None:
    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "usage": {"cost": "0.01"},
                        "choices": [{"finish_reason": "length", "message": {"content": "{}"}}],
                    },
                )
            )
        ) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess("source")
            assert result.failure_reason == "output_truncated"
            assert result.cost == Decimal("0.01")

    asyncio.run(run())


def test_external_excerpt_cannot_be_attributed_to_primary_source() -> None:
    from linksifty.domain.models import CriterionName

    payload = {
        "note": "Note",
        "criteria": [
            {
                "name": n.value,
                "score": 3,
                "rationale": "Supported",
                "excerpt": "external evidence passage",
                "source_id": "primary",
            }
            for n in CriterionName
        ],
    }

    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "usage": {"cost": "0.01"},
                        "choices": [
                            {"finish_reason": "stop", "message": {"content": json.dumps(payload)}}
                        ],
                    },
                )
            )
        ) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess(
                "primary source",
                sources=[
                    EvidenceSource(
                        id="ext1", url="https://source.example", text="external evidence passage"
                    )
                ],
            )
            assert result.assessment is None
            assert result.failure_reason == "invalid_citation"

    asyncio.run(run())


def test_research_checks_at_most_five_pages_and_never_repeats_uncertain_search() -> None:
    from unittest.mock import AsyncMock, create_autospec
    from uuid import uuid4

    from linksifty.application.processing_contracts import (
        ProcessingJob,
        ProcessingStore,
        Reservation,
    )
    from linksifty.application.processing_service import ProcessingService
    from linksifty.application.research_contracts import SearchProvider, SearchResponse
    from linksifty.domain.acquisition import FetchResult

    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.save_research.return_value = True
        store.reserve_search.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=60
        )
        search = create_autospec(SearchProvider, instance=True)
        search.search.return_value = SearchResponse(
            confirmed=True, urls=tuple(f"https://source{i}.example" for i in range(10))
        )
        fetch = AsyncMock(
            side_effect=[FetchResult(text=(f"evidence {i} " * 100)) for i in range(5)]
        )
        service = ProcessingService(
            store, None, fetch, search=search, search_price=Decimal("0.005")
        )
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            web_search=True,
            original_url="https://original.example/public-claim",
        )
        result = await service.research(job, "original primary " * 100)
        assert result.status == "ready"
        assert len(result.sources) == 5
        assert fetch.await_count == 5
        search.search.assert_awaited_once()
        store.settle.assert_awaited_once_with(
            job.user_id, job.search_reservation_id, Decimal("0.005")
        )
        await service.research(job, "original primary " * 100)
        assert search.search.await_count == 1
        job.search_context = None
        result = await service.research(job, "original primary " * 100)
        assert result.status == "uncertain"
        assert search.search.await_count == 1

    asyncio.run(run())


def test_research_does_not_count_reposts_or_failed_fetches() -> None:
    from unittest.mock import AsyncMock, create_autospec
    from uuid import uuid4

    from linksifty.application.processing_contracts import (
        ProcessingJob,
        ProcessingStore,
        Reservation,
    )
    from linksifty.application.processing_service import ProcessingService
    from linksifty.application.research_contracts import SearchProvider, SearchResponse
    from linksifty.domain.acquisition import FetchFailure, FetchResult

    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.save_research.return_value = True
        store.reserve_search.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=60
        )
        search = create_autospec(SearchProvider, instance=True)
        search.search.return_value = SearchResponse(
            confirmed=True,
            urls=(
                "https://original.example/other",
                "https://a.example",
                "https://a.example/repost",
                "https://b.example",
                "https://c.example",
            ),
        )
        duplicate = "identical source passage " * 20
        fetch = AsyncMock(
            side_effect=[
                FetchResult(text=duplicate),
                FetchResult(text=duplicate),
                FetchResult(failure=FetchFailure.UNAVAILABLE),
            ]
        )
        service = ProcessingService(
            store, None, fetch, search=search, search_price=Decimal("0.005")
        )
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            web_search=True,
            original_url="https://original.example/article",
        )
        result = await service.research(job, "primary text " * 30)
        assert len(result.sources) == 1
        assert fetch.await_count == 3

    asyncio.run(run())


def test_failed_telemetry_never_repeats_operation_or_exports_content() -> None:
    from unittest.mock import create_autospec

    from langfuse import Langfuse

    from linksifty.application.processing_contracts import ModelResult
    from linksifty.infrastructure.langfuse_telemetry import LangfuseTelemetry

    client = create_autospec(Langfuse, instance=True)
    client.start_as_current_observation.side_effect = RuntimeError("offline")
    client.start_observation.side_effect = RuntimeError("offline")
    telemetry = LangfuseTelemetry(client)
    operations = []
    with telemetry.scope("processing", "opaque-job-id"):
        with telemetry.generation("model") as record:
            operations.append("called")
            record(ModelResult(failure_reason="invalid_schema", cost=Decimal("0.001")))
    assert operations == ["called"]
    for call in client.start_observation.call_args_list:
        assert "input" not in call.kwargs and "output" not in call.kwargs


def test_valid_external_passage_is_accepted_with_its_own_source_id() -> None:
    from linksifty.domain.models import CriterionName

    payload = {
        "note": "Compared evidence",
        "criteria": [
            {
                "name": name.value,
                "score": 3,
                "rationale": "External passage",
                "excerpt": "exact external evidence",
                "source_id": "external-1",
            }
            for name in CriterionName
        ],
    }

    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "usage": {"cost": "0.01"},
                        "choices": [
                            {"finish_reason": "stop", "message": {"content": json.dumps(payload)}}
                        ],
                    },
                )
            )
        ) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess(
                "primary material",
                sources=[
                    EvidenceSource(
                        id="external-1",
                        url="https://evidence.example",
                        text="exact external evidence",
                    )
                ],
            )
            assert result.assessment is not None
            assert result.assessment.criteria[0].source_id == "external-1"

    asyncio.run(run())
