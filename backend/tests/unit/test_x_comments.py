import asyncio

import httpx
import pytest

from linksifty.infrastructure.x_adapter import XAdapter


def test_x_replies_are_a_bounded_text_snapshot_not_an_assessment_source() -> None:
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.host == "api.x.com"
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "100",
                        "author_id": "50",
                        "conversation_id": "90",
                        "text": "Root preview…",
                    }
                },
            )
        assert request.url.path == "/2/tweets/search/all"
        assert request.url.params["query"] == "conversation_id:90 is:reply"
        assert request.url.params["max_results"] == "20"
        assert "author_id" in request.url.params["expansions"].split(",")
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "101",
                        "author_id": "70",
                        "conversation_id": "90",
                        "text": "Preview…",
                        "note_tweet": {"text": "Exact reader reply. " * 300},
                        "attachments": {"media_keys": ["video"]},
                        "referenced_tweets": [{"id": "90", "type": "replied_to"}],
                    }
                ],
                "includes": {"users": [{"id": "70", "username": "reader_70"}]},
                "meta": {"result_count": 1, "next_token": "do-not-follow"},
            },
        )

    async def run() -> None:
        result = await XAdapter("test-token", transport=httpx.MockTransport(respond)).comments(
            "https://x.com/author/status/100"
        )
        assert result.status == "ready" and len(result.replies) == 1
        reply = result.replies[0]
        assert reply.id == "101" and reply.author_id == "70" and reply.username == "reader_70"
        assert reply.text.startswith("Exact reader reply.") and len(reply.text) == 4000
        assert reply.truncated and reply.has_media
        assert len(calls) == 2

    asyncio.run(run())


@pytest.mark.parametrize("failure", ["denied", "wrong_id", "wrong_conversation", "invalid_count"])
def test_comment_failures_return_unavailable_without_retries(failure: str) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if failure == "denied":
            return httpx.Response(429)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "999" if failure == "wrong_id" else "100",
                        "author_id": "50",
                        "conversation_id": "100",
                        "text": "Post text",
                    }
                },
            )
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "101",
                        "author_id": "70",
                        "conversation_id": "999",
                        "text": "Unrelated reply",
                        "referenced_tweets": [{"id": "100", "type": "replied_to"}],
                    }
                ],
                "meta": {"result_count": 0 if failure == "invalid_count" else 1},
            },
        )

    async def run() -> None:
        result = await XAdapter("test-token", transport=httpx.MockTransport(respond)).comments(
            "https://x.com/author/status/100"
        )
        assert result.status == "unavailable" and not result.replies
        assert calls == (1 if failure in {"denied", "wrong_id"} else 2)

    asyncio.run(run())


def test_invalid_comment_url_never_reaches_transport() -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("unsafe URL reached transport")

    async def run() -> None:
        result = await XAdapter("test-token", transport=httpx.MockTransport(forbidden)).comments(
            "https://x.com.evil.test/user/status/100"
        )
        assert result.status == "unavailable"

    asyncio.run(run())
