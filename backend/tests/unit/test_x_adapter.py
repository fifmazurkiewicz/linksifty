import asyncio
import logging
from collections.abc import Callable

import httpx
import pytest

from linksifty.domain.acquisition import FetchResult
from linksifty.infrastructure.x_adapter import XAdapter

TEXT = "A complete explanation with evidence and a reproducible practical example. " * 5


def post(identifier: str = "100", parent: str | None = None, **extra: object) -> dict[str, object]:
    return {
        "id": identifier,
        "author_id": "50",
        "conversation_id": "100",
        "text": TEXT,
        "referenced_posts": [{"type": "replied_to", "id": parent}] if parent else [],
        **extra,
    }


def acquire(
    handler: Callable[[httpx.Request], httpx.Response], url: str = "https://x.com/user/status/100"
) -> FetchResult:
    return asyncio.run(XAdapter("test-x-token", transport=httpx.MockTransport(handler)).fetch(url))


def test_long_post_uses_complete_text_and_fixed_official_endpoint() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.host == "api.x.com"
        assert request.headers["authorization"] == "Bearer test-x-token"
        assert "note_tweet" in request.url.params["tweet.fields"]
        assert "referenced_tweets" in request.url.params["tweet.fields"]
        assert "author_id" in request.url.params["tweet.fields"]
        assert "expansions" not in request.url.params
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200, json={"data": post(text="preview…", note_post={"text": TEXT})}
            )
        assert request.url.path == "/2/tweets/search/all"
        assert request.url.params["query"] == "conversation_id:100 from:50"
        assert request.url.params["start_time"] == "2006-03-21T00:00:00Z"
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.failure is None
    assert TEXT in (result.text or "")
    assert "preview" not in (result.text or "")
    assert len(requests) == 2


def test_thread_from_middle_follows_pagination_and_parent_order() -> None:
    paths: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/2/tweets/101":
            return httpx.Response(200, json={"data": post("101", "100")})
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post()})
        if request.url.params.get("next_token") == "next":
            return httpx.Response(
                200, json={"data": [post("101", "100")], "meta": {"result_count": 1}}
            )
        return httpx.Response(
            200,
            json={"data": [post("102", "101")], "meta": {"result_count": 1, "next_token": "next"}},
        )

    result = acquire(respond, "https://twitter.com/user/status/101?s=20")
    assert result.failure is None
    assert result.text is not None
    assert result.text.index("/100") < result.text.index("/101") < result.text.index("/102")
    assert len(paths) == 4


@pytest.mark.parametrize(
    "status,reason",
    [
        (401, "x_access_denied"),
        (402, "x_access_denied"),
        (403, "x_access_denied"),
        (404, "x_not_found"),
        (429, "x_rate_limited"),
        (500, "unavailable"),
        (302, "unavailable"),
    ],
)
def test_provider_failure_does_not_retry(status: int, reason: str) -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(status, headers={"location": "https://example.com/steal"})

    result = acquire(respond)
    assert result.text is None
    assert result.failure == reason
    assert len(calls) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"data": None},
        {"data": post("999")},
        {"data": post(), "errors": [{"title": "Partial result"}]},
        {"data": post(note_post={})},
        {"data": post(text="truncated…")},
        {"data": post(attachments={"media_keys": ["image"]})},
        {"data": post(article={"title": "Preview"})},
        {"data": post(referenced_posts=[{"type": "quoted", "id": "90"}])},
    ],
)
def test_incomplete_lookup_never_returns_text(payload: object) -> None:
    result = acquire(lambda _: httpx.Response(200, json=payload))
    assert result.text is None
    assert result.failure is not None


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.test/user/status/100",
        "https://x.com.evil.test/user/status/100",
        "https://token@x.com/user/status/100",
        "https://x.com:8443/user/status/100",
        "https://x.com/user",
        "https://x.com/user/status/not-an-id",
        "https://x.com/user/status/100/extra",
        "https://x.com/user/status/100\n",
    ],
)
def test_invalid_url_makes_no_request(url: str) -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid URL reached X")

    assert acquire(forbidden, url).text is None


@pytest.mark.parametrize(
    "posts",
    [
        [post("102", "99")],
        [post("102", "101"), post("101", "102")],
        [post("101", "100", author_id="51")],
    ],
)
def test_thread_gaps_cycles_or_wrong_author_fail_closed(posts: list[dict[str, object]]) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post()})
        return httpx.Response(200, json={"data": posts, "meta": {"result_count": len(posts)}})

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "partial_content"


@pytest.mark.parametrize(
    "url",
    [
        "https://www.x.com/user/status/100/",
        "https://mobile.twitter.com/user/status/100",
        "https://m.twitter.com/user/status/100",
        "https://x.com/i/web/status/100",
    ],
)
def test_supported_url_variants_use_the_same_post_identity(url: str) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post()})
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    assert acquire(respond, url).failure is None


@pytest.mark.parametrize(
    "page",
    [
        {},
        {"data": [post("101", "100")]},
        {"data": [post("101", "100")], "meta": {"result_count": 0}},
        {"meta": {"result_count": 1}},
        {"data": [post("101", "100", conversation_id="999")], "meta": {"result_count": 1}},
        {
            "data": [post("101", "100")],
            "meta": {"result_count": 1},
            "errors": [{"title": "Missing data"}],
        },
    ],
)
def test_partial_search_response_never_returns_the_successful_root(page: object) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post()})
        return httpx.Response(200, json=page)

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "partial_content"


def test_search_access_failure_is_not_downgraded_to_recent_search_or_root_only() -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post()})
        return httpx.Response(403)

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "x_access_denied"
    assert calls == ["/2/tweets/100", "/2/tweets/search/all"]


def test_pagination_is_bounded_and_never_silently_truncated() -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post()})
        return httpx.Response(
            200, json={"meta": {"result_count": 0, "next_token": str(len(calls))}}
        )

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "partial_content"
    assert len(calls) == 11


@pytest.mark.parametrize("large_body", [False, True])
def test_response_and_utf8_source_limits_never_return_a_prefix(large_body: bool) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200, json={"data": post(text="é" * (600_000 if large_body else 60_000))}
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "too_large"


def test_short_thread_does_not_pass_minimum_by_adding_source_urls() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post(text="Short root")})
        return httpx.Response(
            200,
            json={
                "data": [post(str(i), "100", text="Short reply") for i in range(101, 106)],
                "meta": {"result_count": 5},
            },
        )

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "too_short"


def test_legacy_long_post_field_is_preserved_without_extra_reads() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200, json={"data": post(text="preview…", note_tweet={"text": TEXT})}
            )
        reply = post("101", "100")
        reply["referenced_tweets"] = reply.pop("referenced_posts")
        return httpx.Response(200, json={"data": [reply], "meta": {"result_count": 1}})

    result = acquire(respond)
    assert result.failure is None
    assert TEXT in (result.text or "")
    assert "preview" not in (result.text or "")


def test_timeout_is_explicit_and_is_not_retried() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("simulated", request=request)

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "unavailable"


@pytest.mark.parametrize("status", [400, 401, 402, 403, 404, 429, 500])
@pytest.mark.parametrize("endpoint", ["post_lookup", "full_archive_search"])
def test_rejected_request_logs_status_and_endpoint_without_private_data(
    caplog: pytest.LogCaptureFixture, status: int, endpoint: str
) -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if endpoint == "full_archive_search" and request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post()})
        return httpx.Response(
            status,
            json={"detail": "private-provider-detail", "data": post()},
            headers={"x-request-id": "private-request-id"},
        )

    with caplog.at_level(logging.WARNING):
        result = acquire(respond, "https://x.com/private_user/status/100?s=private-query")

    assert result.text is None
    assert len(calls) == (2 if endpoint == "full_archive_search" else 1)
    assert f"x_api_request_failed endpoint={endpoint} status={status}" in caplog.text
    for private in (
        "test-x-token",
        "private-provider-detail",
        "private-request-id",
        "private_user",
        "private-query",
        TEXT,
        "conversation_id:100",
        "/2/tweets/100",
    ):
        assert private not in caplog.text


@pytest.mark.parametrize("invalid_json", [False, True])
def test_transport_and_decode_errors_log_type_without_exception_details(
    caplog: pytest.LogCaptureFixture, invalid_json: bool
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if invalid_json:
            return httpx.Response(
                200, content=b"private-invalid-body", headers={"content-type": "application/json"}
            )
        raise httpx.ReadTimeout("private-exception-detail", request=request)

    with caplog.at_level(logging.WARNING):
        result = acquire(respond)

    assert result.text is None
    assert "x_fetch_failed" in caplog.text
    assert f"error_type={'JSONDecodeError' if invalid_json else 'ReadTimeout'}" in caplog.text
    for private in ("private-invalid-body", "private-exception-detail", "test-x-token"):
        assert private not in caplog.text


@pytest.mark.parametrize(
    "extra,check",
    [
        ({"attachments": {"media_keys": ["private-media"]}}, "attachments_present"),
        ({"article": {"title": "private-article"}}, "article_present"),
        ({"withheld": {"country_codes": ["private-country"]}}, "withheld_content"),
        ({"note_post": None}, "missing_long_text"),
        ({"text": "private-truncated-text…"}, "empty_or_truncated_text"),
        ({"referenced_posts": [{"type": "quoted", "id": "90"}]}, "unsupported_references"),
        ({"id": "999"}, "lookup_id_mismatch"),
    ],
)
def test_content_rejection_logs_the_specific_check_without_source_data(
    caplog: pytest.LogCaptureFixture, extra: dict[str, object], check: str
) -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json={"data": post(**extra)})

    result = acquire(respond)

    assert result.text is None
    assert result.failure == "partial_content"
    assert len(calls) == 1
    assert f"x_fetch_failed reason=partial_content check={check}" in caplog.text
    for private in (
        "private-media",
        "private-article",
        "private-country",
        "private-truncated-text",
        TEXT,
    ):
        assert private not in caplog.text


@pytest.mark.parametrize(
    "payload,check",
    [
        ({"data": post(), "errors": [{"detail": "private-error"}]}, "provider_partial_errors"),
        ({"data": None}, "invalid_post_payload"),
        ({"data": post("999")}, "lookup_id_mismatch"),
    ],
)
def test_response_rejection_logs_the_specific_check(
    caplog: pytest.LogCaptureFixture, payload: object, check: str
) -> None:
    result = acquire(lambda _: httpx.Response(200, json=payload))
    assert result.text is None
    assert result.failure == "partial_content"
    assert f"check={check}" in caplog.text
    assert "private-error" not in caplog.text
    assert TEXT not in caplog.text


def test_invalid_search_logs_schema_check_and_discards_successful_lookup(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post()})
        return httpx.Response(200, json={"meta": {"result_count": "private-invalid-count"}})

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "partial_content"
    assert "check=invalid_search_payload" in caplog.text
    assert "private-invalid-count" not in caplog.text
