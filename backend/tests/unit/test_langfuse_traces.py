import asyncio
import json
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, create_autospec, patch
from uuid import uuid4

import httpx
from langfuse import Langfuse

from linksifty.application.processing_contracts import (
    AssessmentProvider,
    ProcessingJob,
    ProcessingStore,
)
from linksifty.application.processing_service import ProcessingService
from linksifty.infrastructure.langfuse_telemetry import LangfuseTelemetry
from linksifty.infrastructure.openrouter_client import OpenRouterClient


def test_rejected_generation_keeps_input_output_and_reason_without_credentials() -> None:
    async def run() -> None:
        client = create_autospec(Langfuse, instance=True)
        telemetry = LangfuseTelemetry(client)
        content = json.dumps({"note": "Invalid response for diagnosis"})
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "usage": {"cost": "0.001"},
                        "choices": [{"finish_reason": "stop", "message": {"content": content}}],
                    },
                )
            )
        ) as http:
            result = await OpenRouterClient(
                "server-only-test-key", "openai/gpt-4o-mini", http, telemetry
            ).assess(
                "Article evidence " * 30
                + "Authorization: Bearer pretend-private-token reader@example.test"
            )
        assert result.failure_reason == "invalid_schema"
        generation = client.start_observation.call_args_list[0].kwargs
        assert "Article evidence" in str(generation["input"])
        exported = str(client.mock_calls)
        assert "Invalid response for diagnosis" in exported
        assert "invalid_schema" in exported
        assert "pretend-private-token" not in exported
        assert "reader@example.test" not in exported
        assert "server-only-test-key" not in exported
        assert "[REDACTED]" in exported

    asyncio.run(run())


def test_events_are_redacted_and_telemetry_failure_is_isolated() -> None:
    client = create_autospec(Langfuse, instance=True)
    telemetry = LangfuseTelemetry(client)
    telemetry.event(
        "search.result",
        {"url": "https://user:password@example.test/a?api_key=hidden-value", "count": 2},
    )
    exported = str(client.mock_calls)
    assert "hidden-value" not in exported and "user:password" not in exported
    assert "search.result" in exported and "count" in exported
    client.create_event.side_effect = RuntimeError("offline")
    telemetry.event("search.result", {"count": 2})


def test_session_setup_failure_does_not_stop_processing_or_leak_context() -> None:
    client = create_autospec(Langfuse, instance=True)
    telemetry = LangfuseTelemetry(client)
    with patch(
        "linksifty.infrastructure.langfuse_telemetry.propagate_attributes",
        side_effect=RuntimeError("telemetry offline"),
    ):
        with telemetry.scope("processing", "opaque-job"):
            telemetry.event("processing.finished", {"outcome": "returned"})
    client.start_as_current_observation.return_value.__exit__.assert_called_once()
    client.create_event.assert_called_once()


def test_processing_trace_explains_skipped_search_recovery_and_failure() -> None:
    async def run() -> None:
        client = create_autospec(Langfuse, instance=True)
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.reconcile.return_value = None
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            source_text="Complete article source with enough evidence. " * 20,
            reservation_id=uuid4(),
            reservation_state="reserved",
            generation_id="gen-uncertain",
        )
        service = ProcessingService(
            cast(ProcessingStore, store),
            cast(AssessmentProvider, provider),
            AsyncMock(),
            telemetry=LangfuseTelemetry(client),
        )
        await service._execute(job)
        exported = str(client.mock_calls)
        for expected in (
            "processing",
            "search.skipped",
            "not_requested",
            "model.recovery",
            "source.reused",
            "cost_unknown",
            "processing.finished",
        ):
            assert expected in exported
        assert str(job.user_id) not in exported and str(job.lease_token) not in exported
        provider.assess.assert_not_awaited()
        store.settle.assert_not_awaited()

    asyncio.run(run())


def test_real_sdk_exports_article_generation_and_events_in_one_trace() -> None:
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from linksifty.application.processing_contracts import ModelResult

    exporter = InMemorySpanExporter()
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={}))
    ) as http:
        client = Langfuse(
            public_key=f"pk-local-{uuid4()}",
            secret_key="sk-local-placeholder",
            tracer_provider=TracerProvider(),
            span_exporter=exporter,
            httpx_client=http,
        )
        telemetry = LangfuseTelemetry(client, secrets=("opaque-configured-key",))
        try:
            with telemetry.scope("processing", "opaque-job"):
                telemetry.event("source.fetched", {"text": "Article text opaque-configured-key"})
                with telemetry.generation(
                    "test-model", input=[{"role": "user", "content": "Article text"}]
                ) as record:
                    record(
                        ModelResult(
                            failure_reason="invalid_citation",
                            input_tokens=17,
                            output_tokens=8,
                            cost=Decimal("0.001"),
                        )
                    )
            client.flush()
            spans = exporter.get_finished_spans()
            root = next(span for span in spans if span.name == "processing")
            assert all(
                (span.attributes or {}).get("session.id") == "linksifty:job:opaque-job"
                for span in spans
            )
            assert all(span.context.trace_id == root.context.trace_id for span in spans)
            assert all(
                span.parent and span.parent.span_id == root.context.span_id
                for span in spans
                if span.name != "processing"
            )
            exported = str([dict(span.attributes or {}) for span in spans])
            assert "Article text" in exported and "invalid_citation" in exported
            assert "opaque-configured-key" not in exported
            assert "17" in exported and "0.001" in exported
            with telemetry.scope("processing", "opaque-job"):
                with telemetry.scope("source.fetch", "opaque-job"):
                    telemetry.event("source.reused", {"text": "Article text"})
            with telemetry.scope("processing", "other-job"):
                telemetry.event("processing.finished", {"outcome": "returned"})
            with telemetry.scope("orphan.reconciliation", "opaque-reservation"):
                telemetry.event("budget.settled", {"provider": "openrouter"})
            client.flush()
            spans = exporter.get_finished_spans()
            roots = [span for span in spans if span.name == "processing"]
            assert len(roots) == 3
            assert len({span.context.trace_id for span in roots}) == 3
            for index, root in enumerate(roots):
                expected_session = "linksifty:job:" + ("opaque-job" if index < 2 else "other-job")
                assert all(
                    (span.attributes or {}).get("session.id") == expected_session
                    for span in spans
                    if span.context.trace_id == root.context.trace_id
                )
            orphan = next(span for span in spans if span.name == "orphan.reconciliation")
            assert all(
                "session.id" not in (span.attributes or {})
                for span in spans
                if span.context.trace_id == orphan.context.trace_id
            )
        finally:
            telemetry.close()


def test_brave_http_failure_is_visible_without_sending_credentials() -> None:
    from linksifty.infrastructure.brave_client import BraveSearch

    async def run() -> None:
        client = create_autospec(Langfuse, instance=True)
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(401))
        ) as http:
            result = await BraveSearch(
                "private-search-key", http, telemetry=LangfuseTelemetry(client)
            ).search("public query")
        assert not result.confirmed
        exported = str(client.mock_calls)
        assert "brave.http_response" in exported and "401" in exported
        assert "private-search-key" not in exported

    asyncio.run(run())


def test_article_and_search_trace_contains_sources_citations_and_saved_result() -> None:
    from linksifty.application.processing_contracts import Reservation
    from linksifty.domain.acquisition import FetchResult
    from linksifty.domain.models import CriterionName
    from linksifty.infrastructure.brave_client import BraveSearch

    primary = "Primary article evidence with a reproducible practical example. " * 10
    secondary = "Independent external evidence with specific supporting facts. " * 10

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.search.brave.com":
            return httpx.Response(
                200,
                json={
                    "web": {
                        "results": [
                            {"url": "https://secondary.example/article"},
                            {"url": "https://secondary.example/duplicate-host"},
                        ]
                    }
                },
            )
        messages = json.loads(request.content)["messages"]
        sources = json.loads(messages[1]["content"])
        assert primary == sources[0]["text"] and secondary == sources[1]["text"]
        payload = {
            "note": "Verified note",
            "criteria": [
                {
                    "name": name.value,
                    "score": 3,
                    "rationale": "Supported by independent passage",
                    "source_id": sources[1]["id"],
                    "excerpt": "Independent external evidence",
                }
                for name in CriterionName
            ],
        }
        return httpx.Response(
            200,
            json={
                "usage": {"cost": "0.001"},
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}],
            },
        )

    async def run() -> None:
        client = create_autospec(Langfuse, instance=True)
        telemetry = LangfuseTelemetry(client)
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = store.save_source.return_value = True
        store.save_research.return_value = store.record_result.return_value = True
        store.complete.return_value = True
        store.reserve_search.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=Decimal(75)
        )
        store.reserve.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=Decimal(75)
        )
        fetch = AsyncMock(side_effect=[FetchResult(text=primary), FetchResult(text=secondary)])
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            web_search=True,
            original_url="https://primary.example/article",
        )
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
            service = ProcessingService(
                cast(ProcessingStore, store),
                OpenRouterClient("private-model-key", "openai/gpt-4o-mini", http, telemetry),
                fetch,
                search=BraveSearch("private-search-key", http, telemetry=telemetry),
                search_price=Decimal("0.005"),
                telemetry=telemetry,
            )
            await service._execute(job)
        store.complete.assert_awaited_once()
        assert store.settle.await_count == 2
        exported = str(client.mock_calls)
        for expected in (
            primary,
            secondary,
            "search.request",
            "brave.http_response",
            "duplicate_host",
            "citation.result",
            "assessment.saved",
            "budget.settled",
        ):
            assert expected in exported
        assert "private-model-key" not in exported and "private-search-key" not in exported
        assert str(job.user_id) not in exported and str(job.lease_token) not in exported

    asyncio.run(run())
