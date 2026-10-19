import asyncio
import json
from decimal import Decimal

import httpx

from linksifty.application.processing_contracts import EvidenceSource
from linksifty.application.research_contracts import (
    SearchCandidate,
    SourceDecision,
    SourceSelection,
)
from linksifty.infrastructure.brave_client import BraveSearch
from linksifty.infrastructure.openrouter_client import OpenRouterClient


class RelevantSelector:
    def estimate(self, candidate_count: int) -> Decimal:
        return Decimal("0.02688")

    async def select(
        self, text: str, query: str, candidates: tuple[SearchCandidate, ...]
    ) -> SourceSelection:
        return SourceSelection(
            cost=Decimal("0.0001"),
            generation_id="selection-gen",
            decisions=[
                SourceDecision(candidate_id=i, relevant=True, confidence=0.95)
                for i in range(len(candidates))
            ],
        )


def test_selected_social_links_are_preserved_for_discussions_without_becoming_evidence() -> None:
    from unittest.mock import create_autospec
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
        urls = (
            "https://x.com/author/status/100?s=20",
            "https://twitter.com/author/status/100",
            "https://x.com/other/status/200",
            "https://reddit.com/r/test/comments/abc",
            "https://article.example/evidence",
        )
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.save_research.return_value = True
        store.reserve_search.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=60
        )
        store.reserve_selection.return_value = uuid4()
        search = create_autospec(SearchProvider, instance=True)
        search.search.return_value = SearchResponse(
            confirmed=True, urls=urls, candidates=tuple(SearchCandidate(url) for url in urls)
        )

        async def fetch(url: str) -> FetchResult:
            return (
                FetchResult(text="Independent article evidence. " * 20, omitted_media=("image",))
                if url.startswith("https://article.example")
                else FetchResult(failure=FetchFailure.UNSUPPORTED)
            )

        service = ProcessingService(
            store,
            None,
            fetch,
            search=search,
            search_price=Decimal("0.001"),
            selector=RelevantSelector(),
        )
        context = await service.research(
            ProcessingJob(
                id=uuid4(),
                user_id=uuid4(),
                item_id=uuid4(),
                lease_token=uuid4(),
                original_url="https://primary.example",
                web_search=True,
            ),
            "Primary article about practical testing. " * 20,
        )
        assert context.status == "ready"
        assert context.sources[0].omitted_media == ["image"]
        assert [source.url for source in context.sources] == ["https://article.example/evidence"]
        assert [source.url for source in context.discussion_sources] == [
            "https://x.com/i/web/status/100",
            "https://x.com/i/web/status/200",
            "https://reddit.com/r/test/comments/abc",
        ]
        assert len({source.id for source in context.discussion_sources}) == 3
        store.save_research.assert_awaited_once()

    asyncio.run(run())


def test_brave_uses_header_auth_and_bounds_candidates() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Subscription-Token"] == "test-key"
        assert "test-key" not in str(request.url)
        assert request.url.params["count"] == "20"
        return httpx.Response(
            200,
            json={"web": {"results": [{"url": f"https://source{i}.example"} for i in range(25)]}},
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await BraveSearch("test-key", client).search("public claim")
            assert result.confirmed
            assert len(result.urls) == 20

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
                "passage_id": "source1:1",
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
            assert result.failure_reason == "invalid_schema"

    asyncio.run(run())


def test_research_checks_at_most_twenty_pages_and_never_repeats_uncertain_search() -> None:
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
            confirmed=True, urls=tuple(f"https://source{i}.example" for i in range(25))
        )
        search.search.return_value = SearchResponse(
            confirmed=True,
            urls=search.search.return_value.urls,
            candidates=tuple(SearchCandidate(url) for url in search.search.return_value.urls),
        )
        store.reserve_selection.return_value = uuid4()
        fetch = AsyncMock(
            side_effect=[FetchResult(text=(f"evidence {i} " * 100)) for i in range(20)]
        )
        service = ProcessingService(
            store,
            None,
            fetch,
            search=search,
            search_price=Decimal("0.005"),
            selector=RelevantSelector(),
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
        assert len(result.sources) == 20
        assert fetch.await_count == 20
        search.search.assert_awaited_once()
        store.settle.assert_any_await(job.user_id, job.search_reservation_id, Decimal("0.005"))
        assert store.settle.await_count == 2
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
        search.search.return_value = SearchResponse(
            confirmed=True,
            urls=search.search.return_value.urls,
            candidates=tuple(SearchCandidate(url) for url in search.search.return_value.urls),
        )
        store.reserve_selection.return_value = uuid4()
        fetch = AsyncMock(
            side_effect=[
                FetchResult(text=duplicate),
                FetchResult(text=duplicate),
                FetchResult(failure=FetchFailure.UNAVAILABLE),
            ]
        )
        service = ProcessingService(
            store,
            None,
            fetch,
            search=search,
            search_price=Decimal("0.005"),
            selector=RelevantSelector(),
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
        assert call.kwargs.get("input") is None and "output" not in call.kwargs


def test_valid_external_passage_is_accepted_with_its_own_source_id() -> None:
    from linksifty.domain.models import CriterionName

    payload = {
        "note": "Compared evidence",
        "criteria": [
            {
                "name": name.value,
                "score": 3,
                "rationale": "External passage",
                "passage_id": "source1:1",
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
