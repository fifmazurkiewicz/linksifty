"""Opt-in X wire diagnostics, with mocked HTTP and no credentials."""

import asyncio
import logging
import re
from collections.abc import AsyncIterator

import httpx
import pytest

from linksifty.infrastructure.x_adapter import XAdapter


@pytest.mark.parametrize("status", [200, 403])
def test_debug_pairs_request_and_response_and_redacts_secrets(
    caplog: pytest.LogCaptureFixture, status: int
) -> None:
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            status,
            json={
                "article": {"title": "Diagnostic article", "cover_media": ["image-key"]},
                "detail": "Bearer test-x-token opaque-other-key person@example.com",
                "access_token": "hidden-token-value",
            },
            headers={"set-cookie": "private-cookie"},
        )

    adapter = XAdapter(
        "test-x-token",
        transport=httpx.MockTransport(respond),
        debug=True,
        secrets=("opaque-other-key",),
    )
    with caplog.at_level(logging.WARNING):
        result = asyncio.run(adapter.fetch("https://x.com/user/status/100"))

    assert result.failure is not None
    assert len(calls) == 1
    assert "event=request" in caplog.text
    assert "event=response" in caplog.text
    assert '"method": "GET"' in caplog.text
    assert '"url": "https://api.x.com/2/tweets/100"' in caplog.text
    assert '"tweet.fields"' in caplog.text
    assert f'"status": {status}' in caplog.text
    assert "Diagnostic article" in caplog.text
    assert "cover_media" in caplog.text
    assert "[REDACTED]" in caplog.text
    identifiers = re.findall(r"request_id=([a-f0-9]+)", caplog.text)
    assert len(identifiers) >= 2 and len(set(identifiers)) == 1
    for private in (
        "test-x-token",
        "opaque-other-key",
        "person@example.com",
        "hidden-token-value",
        "private-cookie",
        "Authorization",
    ):
        assert private not in caplog.text


@pytest.mark.parametrize(
    "body", [b"not JSON: Bearer test-x-token", b"x" * 1_000_001], ids=["invalid", "oversized"]
)
def test_debug_handles_invalid_and_oversized_responses_without_weakening_rejection(
    caplog: pytest.LogCaptureFixture, body: bytes
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body, headers={"content-type": "application/json"})

    adapter = XAdapter("test-x-token", transport=httpx.MockTransport(respond), debug=True)
    result = asyncio.run(adapter.fetch("https://x.com/user/status/100"))
    assert result.failure == ("too_large" if len(body) > 1_000_000 else "partial_content")
    assert "event=response" in caplog.text
    assert "test-x-token" not in caplog.text
    if len(body) > 1_000_000:
        assert "truncated=true" in caplog.text
        assert "[TRUNCATED" in caplog.text
    for record in caplog.records:
        assert len(record.getMessage()) < 4500


def test_debug_records_transport_failure_without_exception_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("private transport detail", request=request)

    adapter = XAdapter("test-x-token", transport=httpx.MockTransport(respond), debug=True)
    result = asyncio.run(adapter.fetch("https://x.com/user/status/100"))
    assert result.failure == "unavailable"
    assert "event=request" in caplog.text
    assert "event=transport_error" in caplog.text
    assert "ReadTimeout" in caplog.text
    assert "private transport detail" not in caplog.text


def test_debug_defaults_off_even_when_logger_is_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "private body"})

    adapter = XAdapter("test-x-token", transport=httpx.MockTransport(respond))
    with caplog.at_level(logging.DEBUG, logger="linksifty.infrastructure.x_adapter"):
        result = asyncio.run(adapter.fetch("https://x.com/user/status/100"))
    assert result.failure == "x_access_denied"
    assert "x_api_debug" not in caplog.text
    assert "private body" not in caplog.text


def test_debug_preserves_success_and_shows_thread_search_parameters(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "100",
                        "author_id": "50",
                        "conversation_id": "100",
                        "text": "A complete explanation with evidence and reproducible examples. "
                        * 5,
                    }
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    adapter = XAdapter("test-x-token", transport=httpx.MockTransport(respond), debug=True)
    result = asyncio.run(adapter.fetch("https://x.com/user/status/100"))
    assert result.failure is None
    assert '"query": "conversation_id:100 from:50"' in caplog.text
    assert '"url": "https://api.x.com/2/tweets/search/all"' in caplog.text
    assert caplog.text.count("event=request") == caplog.text.count("event=response") == 2


def test_debug_redacts_before_chunking_or_truncating_json(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "x" * 3990 + "test-x-token" + "y" * 40000})

    adapter = XAdapter("test-x-token", transport=httpx.MockTransport(respond), debug=True)
    result = asyncio.run(adapter.fetch("https://x.com/user/status/100"))
    assert result.failure == "x_access_denied"
    parts = [record.getMessage() for record in caplog.records if "event=response" in record.message]
    payload = "".join(part.split(" payload=", 1)[1] for part in parts)
    assert "[REDACTED]" in payload
    assert "test-x-token" not in payload
    assert "[TRUNCATED" in payload
    assert len(parts) > 1
    assert all("truncated=true" in part and len(part) < 4500 for part in parts)


@pytest.mark.parametrize("status", [200, 403])
def test_interrupted_debug_body_preserves_failure_and_logs_one_response(
    caplog: pytest.LogCaptureFixture, status: int
) -> None:
    class InterruptedBody(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield b'{"detail": "partial'
            raise httpx.ReadError("private stream error")

    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            status, stream=InterruptedBody(), headers={"content-type": "application/json"}
        )

    adapter = XAdapter("test-x-token", transport=httpx.MockTransport(respond), debug=True)
    result = asyncio.run(adapter.fetch("https://x.com/user/status/100"))
    assert result.failure == ("unavailable" if status == 200 else "x_access_denied")
    assert calls == 1
    assert caplog.text.count("event=response") == 1
    assert "event=transport_error" in caplog.text
    assert "private stream error" not in caplog.text
