import asyncio
import json
from decimal import Decimal
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

import httpx
import pytest

from linksifty.application.processing_contracts import ProcessingJob, ProcessingStore, Reservation
from linksifty.application.processing_service import ProcessingService
from linksifty.application.research_contracts import (
    SearchCandidate,
    SearchProvider,
    SearchResponse,
    SourceDecision,
    SourceSelection,
    SourceSelector,
)
from linksifty.domain.acquisition import FetchResult
from linksifty.infrastructure.brave_client import BraveSearch
from linksifty.infrastructure.source_selector import JevSourceSelector

PRIMARY = (
    "Opik agent observability diagnoses production failures and repairs agent harnesses. " * 12
)
CANDIDATES = (
    SearchCandidate(
        "https://walmart.com/seller/17817", "Retail seller", "Unrelated retail products"
    ),
    SearchCandidate("https://www.comet.com/docs/opik/", "Opik observability", "AI agent debugging"),
)


@pytest.mark.parametrize(
    "outcome", ["valid", "uncertain", "missing", "injection", "unknown_cost", "http"]
)
def test_jev_selection_validates_all_candidates_cost_and_typed_decisions(outcome: str) -> None:
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        sent = json.loads(request.content)
        assert request.url.path == "/api/alpha/decisions"
        assert sent["model"] == "typesafe/jev-1.13"
        assert sent["provider"]["allow_fallbacks"] is False
        assert sent["provider"]["max_price"] == {"prompt": 0.042, "completion": 0, "request": 0}
        assert "Unrelated retail products" in json.dumps(sent)
        assert len(json.dumps(sent).encode()) < 30000
        answers = {
            f"candidate_{i}": {
                "type": "choice",
                "choice": choice,
                "confidence": 0.5 if outcome == "uncertain" else 0.95,
                "probabilities": {
                    "relevant": 0.95 if choice == "relevant" else 0.05,
                    "irrelevant": 0.95 if choice == "irrelevant" else 0.05,
                },
            }
            for i, choice in enumerate(("irrelevant", "relevant"))
        }
        if outcome == "missing":
            answers.pop("candidate_1")
        if outcome == "injection":
            answers["candidate_1"]["choice"] = "https://evil.test"
        return httpx.Response(
            403 if outcome == "http" else 200,
            json={
                "id": "selection-generation",
                "usage": {} if outcome == "unknown_cost" else {"cost": "0.0001"},
                "answers": answers,
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            selector = JevSourceSelector("test-key", client)
            assert selector.estimate(20) == Decimal("0.02688")
            result = await selector.select(PRIMARY, "Opik agent observability", CANDIDATES)
        assert len(calls) == 1
        assert result.generation_id == "selection-generation"
        assert result.cost == (None if outcome == "unknown_cost" else Decimal("0.0001"))
        if outcome in {"missing", "injection", "http"}:
            assert result.failure_reason and not result.decisions
        else:
            assert [d.candidate_id for d in result.decisions] == [0, 1]
            assert [d.relevant for d in result.decisions] == [False, True]

    asyncio.run(run())


def test_brave_metadata_is_bounded_and_not_dropped() -> None:
    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "web": {
                            "results": [
                                {"url": c.url, "title": c.title, "description": c.snippet}
                                for c in CANDIDATES
                            ]
                        }
                    },
                )
            )
        ) as client:
            response = await BraveSearch("key", client).search("Opik")
        assert response.candidates == CANDIDATES
        assert response.urls == tuple(c.url for c in CANDIDATES)

    asyncio.run(run())


def test_twenty_full_metadata_candidates_fit_one_bounded_request() -> None:
    calls: list[httpx.Request] = []
    candidates = tuple(
        SearchCandidate(f"https://source{i}.example/article", "t" * 160, "s" * 320)
        for i in range(20)
    )

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        payload = json.loads(request.content)
        assert len(request.content) < 30000
        assert len(payload["questions"]) == 20
        return httpx.Response(
            200,
            json={
                "id": "twenty",
                "usage": {"cost": "0.001"},
                "answers": {
                    f"candidate_{i}": {
                        "type": "choice",
                        "choice": "irrelevant",
                        "confidence": 0.95,
                        "probabilities": {"relevant": 0.05, "irrelevant": 0.95},
                    }
                    for i in range(20)
                },
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await JevSourceSelector("key", client).select(PRIMARY * 20, "Opik", candidates)
        assert len(calls) == 1 and result.failure_reason is None
        assert len(result.decisions) == 20

    asyncio.run(run())


@pytest.mark.parametrize(
    "outcome",
    ["valid", "uncertain", "budget", "failure", "unknown_cost", "missing", "unconfigured"],
)
def test_only_admitted_relevant_candidates_are_fetched_and_cached(outcome: str) -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = store.save_research.return_value = True
        store.reserve_search.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=60
        )
        reservation = uuid4()
        store.reserve_selection.return_value = None if outcome == "budget" else reservation
        search = create_autospec(SearchProvider, instance=True)
        search.search.return_value = SearchResponse(
            confirmed=True, urls=tuple(c.url for c in CANDIDATES), candidates=CANDIDATES
        )
        selector = create_autospec(SourceSelector, instance=True)
        selector.estimate.return_value = Decimal("0.002688")
        selector.select.return_value = SourceSelection(
            decisions=[
                SourceDecision(
                    candidate_id=i,
                    relevant=bool(i),
                    confidence=0.5 if outcome == "uncertain" else 0.95,
                )
                for i in range(1 if outcome == "missing" else 2)
            ],
            generation_id="selection-generation",
            cost=None if outcome == "unknown_cost" else Decimal("0.0001"),
            failure_reason="provider_failed" if outcome == "failure" else None,
        )
        fetch = AsyncMock(return_value=FetchResult(text="Relevant external evidence. " * 30))
        service = ProcessingService(
            store,
            None,
            fetch,
            search=search,
            search_price=Decimal("0.005"),
            selector=None if outcome == "unconfigured" else selector,
        )
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            web_search=True,
            original_url="https://x.com/author/status/2111753928031531232",
        )
        text = "https://x.com/i/web/status/2111753928031531232\nauthor_id=50\n" + PRIMARY
        result = await service.research(job, text)
        if outcome == "unconfigured":
            search.search.assert_not_awaited()
        else:
            query = search.search.await_args.args[0]
            assert (
                "Opik" in query and "2111753928031531232" not in query and "author_id" not in query
            )
        if outcome == "valid":
            fetch.assert_awaited_once_with(CANDIDATES[1].url)
            assert len(result.sources) == 1 and result.sources[0].url == CANDIDATES[1].url
            assert "Unrelated retail products" not in result.model_dump_json()
            store.record_selection_generation.assert_awaited_once_with(
                job, reservation, "selection-generation"
            )
            assert job.selection_reservation_id == reservation
        else:
            fetch.assert_not_awaited()
            assert not result.sources
        if outcome == "unknown_cost":
            assert result.status == "uncertain"
            assert store.settle.await_count == 1  # Brave only; Jev hold remains.
        if outcome == "budget":
            selector.select.assert_not_awaited()
        before = selector.select.await_count
        await service.research(job, text)
        assert selector.select.await_count == before
        job.search_context = None
        await service.research(job, text)
        assert selector.select.await_count == before

    asyncio.run(run())


@pytest.mark.parametrize("outcome", ["transport", "oversize"])
def test_selection_never_retries_and_releases_only_unsent_request(outcome: str) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("mocked timeout", request=request)

    async def run() -> None:
        candidates = (
            CANDIDATES
            if outcome == "transport"
            else tuple(
                SearchCandidate("https://example.test/" + "x" * 1980, "t" * 160, "s" * 320)
                for _ in range(20)
            )
        )
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await JevSourceSelector("key", client).select(PRIMARY, "Opik", candidates)
        assert not result.decisions
        assert calls == (1 if outcome == "transport" else 0)
        assert result.cost == (None if outcome == "transport" else Decimal(0))
        assert result.failure_reason == (
            "provider_unreachable" if outcome == "transport" else "input_too_large"
        )

    asyncio.run(run())


@pytest.mark.parametrize("empty_topic", [True, False])
def test_no_topic_or_no_candidates_does_not_buy_selection(empty_topic: bool) -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = store.save_research.return_value = True
        store.reserve_search.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=60
        )
        search = create_autospec(SearchProvider, instance=True)
        search.search.return_value = SearchResponse(confirmed=True)
        selector = create_autospec(SourceSelector, instance=True)
        service = ProcessingService(
            store,
            None,
            AsyncMock(),
            search=search,
            search_price=Decimal("0.005"),
            selector=selector,
        )
        job = ProcessingJob(
            id=uuid4(), item_id=uuid4(), user_id=uuid4(), lease_token=uuid4(), web_search=True
        )
        text = (
            "https://x.com/a/status/2111753928031531232\nauthor_id=50\n" if empty_topic else PRIMARY
        )
        result = await service.research(job, text)
        assert not result.sources
        assert search.search.await_count == (0 if empty_topic else 1)
        selector.select.assert_not_awaited()
        store.reserve_selection.assert_not_awaited()

    asyncio.run(run())
