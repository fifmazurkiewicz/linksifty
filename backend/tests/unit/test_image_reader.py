import asyncio
import json
from decimal import Decimal

import httpx
import pytest

from linksifty.domain.acquisition import SourceImage
from linksifty.infrastructure.openrouter_images import OpenRouterImageReader

IMAGE = SourceImage(
    url="https://pbs.twimg.com/media/image.png",
    source_url="https://x.com/i/web/status/100",
    mime_type="image/png",
    data=b"validated-image-bytes",
)
READING = {
    "image_id": "image1",
    "complete": True,
    "transcription": "Exact visible source text.",
    "description": "An arrow connects input A to output B.",
}


def test_image_reader_uses_bounded_inline_bytes_and_preserves_provenance() -> None:
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        body = json.loads(request.content)
        assert body["model"] == "openai/gpt-4o-mini"
        assert body["max_tokens"] == 8192
        assert body["provider"]["allow_fallbacks"] is False
        assert body["provider"]["max_price"] == {"prompt": 1, "completion": 5, "request": 0}
        image = body["messages"][1]["content"][1]
        assert image["image_url"]["url"].startswith("data:image/png;base64,")
        assert image["image_url"]["detail"] == "high"
        return httpx.Response(
            200,
            json={
                "id": "generation",
                "usage": {"cost": 0.004},
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps({"images": [READING]})},
                    }
                ],
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            reader = OpenRouterImageReader("private-key", "openai/gpt-4o-mini", client)
            assert reader.estimate() == Decimal("0.16896")
            result = await reader.extract((IMAGE,))
        assert result.cost == Decimal("0.004")
        assert result.generation_id == "generation"
        assert result.text is not None
        assert "Exact visible source text." in result.text
        assert IMAGE.url in result.text and IMAGE.source_url in result.text
        assert "Model-extracted" in result.text
        assert len(calls) == 1

    asyncio.run(run())


@pytest.mark.parametrize(
    "readings",
    [
        [],
        [dict(READING, complete=False)],
        [dict(READING, image_id="unknown")],
        [READING, READING],
        [dict(READING, transcription="", description="")],
    ],
)
def test_incomplete_or_wrong_image_coverage_keeps_cost_but_never_returns_source(
    readings: object,
) -> None:
    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "id": "gen",
                        "usage": {"cost": "0.003"},
                        "choices": [
                            {
                                "finish_reason": "stop",
                                "message": {"content": json.dumps({"images": readings})},
                            }
                        ],
                    },
                )
            )
        ) as client:
            result = await OpenRouterImageReader("key", "openai/gpt-4o-mini", client).extract(
                (IMAGE,)
            )
        assert result.text is None
        assert result.cost == Decimal("0.003")
        assert result.failure_reason == "image_reading_failed"

    asyncio.run(run())


def test_unknown_cost_and_truncated_output_never_returns_extracted_source() -> None:
    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "id": "gen",
                        "choices": [
                            {
                                "finish_reason": "length",
                                "message": {"content": json.dumps({"images": [READING]})},
                            }
                        ],
                    },
                )
            )
        ) as client:
            result = await OpenRouterImageReader("key", "openai/gpt-4o-mini", client).extract(
                (IMAGE,)
            )
        assert result.text is None
        assert result.cost is None
        assert result.generation_id == "gen"

    asyncio.run(run())


def test_transport_failure_never_retries() -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        raise httpx.ReadTimeout("private request detail", request=request)

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterImageReader("key", "openai/gpt-4o-mini", client).extract(
                (IMAGE,)
            )
        assert result.text is None and result.cost is None
        assert len(calls) == 1

    asyncio.run(run())


@pytest.mark.parametrize("count,complete", [(11, True), (12, True), (12, False), (13, True)])
def test_dedicated_image_model_supports_complete_twelve_image_batch(
    count: int, complete: bool
) -> None:
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        body = json.loads(request.content)
        assert body["model"] == "openai/gpt-4.1-mini"
        assert (
            body["response_format"]["json_schema"]["schema"]["properties"]["images"]["maxItems"]
            == 12
        )
        return httpx.Response(
            200,
            json={
                "id": "image-generation",
                "usage": {"cost": "0.007"},
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "images": [
                                        dict(
                                            READING,
                                            image_id=f"image{i}",
                                            complete=complete or i != count,
                                        )
                                        for i in range(1, count + 1)
                                    ]
                                }
                            )
                        },
                    }
                ],
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            reader = OpenRouterImageReader("key", "openai/gpt-4.1-mini", client)
            assert reader.estimate() == Decimal("0.16896")
            result = await reader.extract((IMAGE,) * count)
        if count > 12:
            assert not calls and result.text is None and result.cost == 0
        elif not complete:
            assert len(calls) == 1 and result.text is None and result.cost == Decimal("0.007")
        else:
            assert len(calls) == 1 and result.failure_reason is None
            assert (result.text or "").count("Model-extracted image transcription:") == count

    asyncio.run(run())


def test_unknown_image_model_never_sends_a_paid_request() -> None:
    calls: list[httpx.Request] = []

    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: calls.append(request) or httpx.Response(500)
            )
        ) as client:
            with pytest.raises(ValueError, match="no verified context/cost bound"):
                await OpenRouterImageReader("key", "unverified/model", client).extract((IMAGE,))
        assert not calls

    asyncio.run(run())


@pytest.mark.parametrize(
    "case,check",
    [
        ("provider", "provider_http_400"),
        ("cost", "cost_unknown"),
        ("length", "finish_length"),
        ("schema", "reading_schema"),
        ("coverage", "image_coverage"),
        ("incomplete", "image_incomplete"),
        ("empty", "empty_reading"),
        ("invalid", "response_invalid"),
    ],
)
def test_image_rejection_diagnostic_is_specific_private_and_keeps_accounting(
    case: str, check: str, caplog: pytest.LogCaptureFixture
) -> None:
    calls: list[httpx.Request] = []
    private = "PRIVATE_SOURCE_AND_PROVIDER_MESSAGE"
    reading = dict(READING, transcription=private)
    if case == "schema":
        reading.pop("description")
    if case == "coverage":
        reading["image_id"] = "unknown"
    if case == "incomplete":
        reading["complete"] = False
    if case == "empty":
        reading.update(transcription="", description="")
    body: dict[str, object] = {
        "id": "private-generation-id",
        "usage": {} if case == "cost" else {"cost": "0.003"},
        "choices": [
            {
                "finish_reason": "length" if case == "length" else "stop",
                "message": {"content": json.dumps({"images": [reading]})},
            }
        ],
    }
    if case == "provider":
        body = {"error": {"message": private}}

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if case == "invalid":
            return httpx.Response(200, text=private)
        return httpx.Response(400 if case == "provider" else 200, json=body)

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterImageReader(
                "private-key", "openai/gpt-4.1-mini", client
            ).extract((IMAGE,))
        assert result.text is None and result.failure_reason == "image_reading_failed"
        assert result.failure_check == check
        assert result.cost == (
            None
            if case in {"cost", "invalid"}
            else Decimal(0)
            if case == "provider"
            else Decimal("0.003")
        )
        assert result.generation_id == (
            None if case in {"provider", "invalid"} else "private-generation-id"
        )
        assert len(calls) == 1

    asyncio.run(run())
    assert f"check={check}" in caplog.text
    assert private not in caplog.text
    assert "private-key" not in caplog.text
    assert "private-generation-id" not in caplog.text
