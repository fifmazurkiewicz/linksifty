import asyncio
import json
from unittest.mock import create_autospec
from uuid import uuid4

import httpx
import pytest
from langfuse import Langfuse

from linksifty.application.chat_contracts import ChatInput
from linksifty.infrastructure.langfuse_telemetry import LangfuseTelemetry
from linksifty.infrastructure.openrouter_client import OpenRouterClient


@pytest.mark.parametrize("operation", ["classification", "answer"])
@pytest.mark.parametrize("outcome", ["success", "rejected", "invalid", "timeout", "uncertain"])
def test_chat_generations_capture_diagnostics_without_secrets_or_retries(
    operation: str, outcome: str
) -> None:
    async def run() -> None:
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

        exporter = InMemorySpanExporter()
        calls = []

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            if outcome == "timeout":
                raise httpx.ReadTimeout("private-test-key reader@example.test")
            if outcome == "rejected":
                return httpx.Response(401, json={"error": {"message": "No allowed provider"}})
            if outcome == "invalid":
                return httpx.Response(200, text="Malformed result reader@example.test")
            body = {
                "id": "gen-chat-test",
                "usage": {"cost": 0.00002, "prompt_tokens": 31, "completion_tokens": 9},
            }
            if operation == "classification":
                body["answers"] = {
                    name: {
                        "type": "choice",
                        "choice": choice,
                        "confidence": 0.5 if outcome == "uncertain" else 0.99,
                        "probabilities": {option: int(option == choice) for option in options},
                    }
                    for name, choice, options in (
                        ("scope", "relevant", ("relevant", "off_topic", "unsafe")),
                        ("language", "en", ("pl", "en")),
                    )
                }
                if outcome == "uncertain":
                    body["answers"]["scope"]["probabilities"] = {
                        "relevant": 0.6,
                        "off_topic": 0.3,
                        "unsafe": 0.1,
                    }
                    body["answers"]["scope"]["confidence"] = 0.4
            else:
                body["choices"] = [
                    {
                        "finish_reason": "length" if outcome == "uncertain" else "stop",
                        "message": {
                            "content": json.dumps(
                                {"search_query": None, "paragraphs": [], "insufficient": True}
                            )
                        },
                    }
                ]
            return httpx.Response(200, json=body)

        with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200))) as sdk_http:
            sdk = Langfuse(
                public_key=f"pk-local-{uuid4()}",
                secret_key="sk-local-placeholder",
                tracer_provider=TracerProvider(),
                span_exporter=exporter,
                httpx_client=sdk_http,
            )
            telemetry = LangfuseTelemetry(sdk, secrets=("private-test-key",))
            try:
                async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
                    provider = OpenRouterClient(
                        "private-test-key", "openai/gpt-4o-mini", http, telemetry
                    )
                    with telemetry.scope("chat", "opaque-turn"):
                        payload = ChatInput(
                            question="Explain this private-test-key reader@example.test",
                            passages={},
                            history=[],
                        )
                        result = (
                            await provider.classify(payload)
                            if operation == "classification"
                            else await provider.reply(payload, allow_search=True)
                        )
                sdk.flush()
                spans = exporter.get_finished_spans()
                generation = next(s for s in spans if s.name == f"openrouter.chat.{operation}")
                root = next(s for s in spans if s.name == "chat")
                assert all(s.context.trace_id == root.context.trace_id for s in spans)
                assert generation.parent and generation.parent.span_id == root.context.span_id
                assert (
                    json.loads((root.attributes or {})["langfuse.observation.metadata.turn_id"])
                    == "opaque-turn"
                )
                exported = str([dict(s.attributes or {}) for s in spans])
                assert "Explain this" in exported
                assert "private-test-key" not in exported and "reader@example.test" not in exported
                assert len(calls) == 1
                if outcome == "success" or (
                    outcome == "uncertain" and operation == "classification"
                ):
                    assert result.failure_reason is None
                    assert "gen-chat-test" in exported
                    assert (
                        json.loads(
                            (generation.attributes or {})["langfuse.observation.cost_details"]
                        )["total"]
                        == 0.00002
                    )
                    assert json.loads(
                        (generation.attributes or {})["langfuse.observation.usage_details"]
                    ) == {"input": 31, "output": 9}
                    output = json.loads(
                        (generation.attributes or {})["langfuse.observation.output"]
                    )
                    assert (
                        output
                        == {
                            "category": "uncertain" if outcome == "uncertain" else "relevant",
                            "language": "en",
                        }
                        if operation == "classification"
                        else output
                        == {"search_query": None, "paragraphs": [], "insufficient": True}
                    )
                    if outcome == "uncertain":
                        assert "0.4" in exported and "probabilities" in exported
                else:
                    assert result.failure_reason and result.failure_reason in exported
                    assert (generation.attributes or {})["langfuse.observation.level"] == "ERROR"
                    if outcome == "rejected":
                        assert "401" in exported and "No allowed provider" in exported
                    if outcome == "invalid":
                        assert "Malformed result" in exported
            finally:
                telemetry.close()

    asyncio.run(run())


@pytest.mark.parametrize("phase", ["start", "update", "end"])
def test_broken_telemetry_cannot_stop_chat_or_repeat_provider_requests(phase: str) -> None:
    async def run() -> None:
        sdk = create_autospec(Langfuse, instance=True)
        if phase == "start":
            sdk.start_observation.side_effect = RuntimeError("offline")
        else:
            getattr(sdk.start_observation.return_value, phase).side_effect = RuntimeError("offline")
        sdk.create_event.side_effect = RuntimeError("offline")
        calls = []

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(429, json={"error": "rate limited"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
            provider = OpenRouterClient("test", "openai/gpt-4o-mini", http, LangfuseTelemetry(sdk))
            context = ChatInput(question="Why?", passages={}, history=[])
            for result in (
                await provider.classify(context),
                await provider.reply(context, allow_search=False),
            ):
                assert result.failure_reason == "provider_rejected" and result.cost == 0
        assert len(calls) == 2

    asyncio.run(run())
