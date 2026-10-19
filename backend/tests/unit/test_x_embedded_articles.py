"""Captured Article shapes with synthetic text and fully mocked X reads."""

import asyncio
from collections.abc import Callable

import httpx
import pytest

from linksifty.domain.acquisition import FetchResult
from linksifty.infrastructure.x_adapter import XAdapter
from linksifty.infrastructure.x_content import XContentFailure, parse_article

TEXT = "Complete Article evidence with conditions, reproducible detail and conclusions. " * 8


def post(identifier: str, **extra: object) -> dict[str, object]:
    return {
        "id": identifier,
        "author_id": identifier,
        "conversation_id": identifier,
        "text": TEXT,
        **extra,
    }


def article(*identifiers: str) -> dict[str, object]:
    return {
        "title": "Full Article",
        "plain_text": TEXT,
        "entities": {"tweets": [{"id": identifier} for identifier in identifiers]},
    }


def acquire(handler: Callable[[httpx.Request], httpx.Response]) -> FetchResult:
    return asyncio.run(
        XAdapter("offline-test-token", transport=httpx.MockTransport(handler)).fetch(
            "https://x.com/user/status/100"
        )
    )


@pytest.mark.parametrize("keys", [("tweets",), ("posts",), ("tweets", "posts")])
def test_article_embed_aliases_are_validated_and_deduplicated(keys: tuple[str, ...]) -> None:
    parsed = parse_article(
        {
            "title": "Article",
            "plain_text": TEXT,
            "entities": {key: [{"id": "80"}, {"id": "80"}, "70"] for key in keys},
        }
    )
    assert parsed.post_ids == ("80", "70")


@pytest.mark.parametrize("value", [None, {}, "80", [{"id": 80}], [{"id": "bad"}], [{}]])
def test_invalid_tweets_cannot_be_hidden_by_valid_posts(value: object) -> None:
    with pytest.raises(XContentFailure):
        parse_article(
            {
                "title": "Article",
                "plain_text": TEXT,
                "entities": {"posts": ["80"], "tweets": value},
            }
        )


@pytest.mark.parametrize("expanded", [False, True])
def test_quoted_article_retains_code_and_embedded_text_once(expanded: bool) -> None:
    calls: list[str] = []
    snippets = [f"print('sample {index}')" for index in range(9)]
    rich_article = article("80", "70", "80")
    rich_article["cover_media"] = "3_cover"
    rich_article["media_entities"] = ["3_unexpanded"]
    rich_article["entities"] = {
        "tweets": [{"id": "80"}, {"id": "70"}, {"id": "80"}],
        "posts": [{"id": "80"}],
        "code": [{"code": code, "language": "none"} for code in snippets],
        "urls": [{"text": "https://example.test"}],
    }
    embeds = [
        post("80", text="Preview…", note_tweet={"text": "First embedded evidence. " * 20}),
        post("70", text="Second embedded evidence. " * 20),
    ]

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.x.com"
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(
                        "100",
                        referenced_tweets=[{"type": "quoted", "id": "90"}],
                        attachments={"media_keys": ["13_video"]},
                    ),
                    "includes": {
                        "tweets": [
                            post("90", text="Article preview…", article=rich_article),
                            *(embeds if expanded else []),
                        ],
                        "media": [{"media_key": "13_video", "type": "video"}],
                    },
                },
            )
        if request.url.path in {"/2/tweets/80", "/2/tweets/70"}:
            assert "article" in request.url.params["tweet.fields"].split(",")
            return httpx.Response(
                200, json={"data": embeds[0 if request.url.path.endswith("/80") else 1]}
            )
        assert request.url.path == "/2/tweets/search/all"
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.failure is None and result.text is not None
    assert "Full Article" in result.text and TEXT in result.text
    assert "First embedded evidence." in result.text and "Second embedded evidence." in result.text
    assert "Preview…" not in result.text and "Article preview…" not in result.text
    for identifier in ("80", "70"):
        assert result.text.count(f"embedded: https://x.com/i/web/status/{identifier}") == 1
        assert result.text.count(f"author_id={identifier}\n") == 1
    for snippet in snippets:
        assert result.text.count(snippet) == 1
    assert set(result.omitted_media) == {"image", "video"} and not result.images
    assert calls == [
        "/2/tweets/100",
        *([] if expanded else ["/2/tweets/80", "/2/tweets/70"]),
        "/2/tweets/search/all",
    ]


@pytest.mark.parametrize("cyclic", [False, True])
def test_nested_embeds_reuse_lookup_expansions_and_detect_cycles(
    caplog: pytest.LogCaptureFixture, cyclic: bool
) -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post("100", article=article("90", "80"))})
        if request.url.path == "/2/tweets/90":
            return httpx.Response(
                200,
                json={
                    "data": post("90", article=article("80")),
                    "includes": {
                        "tweets": [post("80", **({"article": article("90")} if cyclic else {}))]
                    },
                },
            )
        assert request.url.path == "/2/tweets/search/all"
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    if cyclic:
        assert result.failure == "partial_content" and result.text is None
        assert "check=reference_cycle" in caplog.text
    else:
        assert result.failure is None and result.text is not None
        assert result.text.count("author_id=80\n") == 1
    assert calls == ["/2/tweets/100", "/2/tweets/90", *([] if cyclic else ["/2/tweets/search/all"])]


def test_embedded_article_discovered_in_thread_search_is_completed() -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post("100")})
        if request.url.path == "/2/tweets/search/all":
            return httpx.Response(
                200,
                json={
                    "data": [
                        post(
                            "101",
                            author_id="100",
                            conversation_id="100",
                            referenced_tweets=[{"type": "replied_to", "id": "100"}],
                            article=article("90"),
                        )
                    ],
                    "meta": {"result_count": 1},
                },
            )
        assert request.url.path == "/2/tweets/90"
        return httpx.Response(200, json={"data": post("90", text="Later embedded evidence. " * 20)})

    result = acquire(respond)
    assert result.failure is None and result.text is not None
    assert "Later embedded evidence." in result.text
    assert calls == ["/2/tweets/100", "/2/tweets/search/all", "/2/tweets/90"]


@pytest.mark.parametrize(
    "case,expected,check",
    [
        ("missing", "x_not_found", "http_status"),
        ("rate_limit", "x_rate_limited", "http_status"),
        ("timeout", "unavailable", None),
        ("truncated", "partial_content", "empty_or_truncated_text"),
        ("wrong_id", "partial_content", "lookup_id_mismatch"),
        ("conflict", "partial_content", "conflicting_post_versions"),
        ("partial", "partial_content", "provider_partial_errors"),
    ],
)
def test_failed_embedded_lookup_never_returns_partial_text_or_retries(
    caplog: pytest.LogCaptureFixture, case: str, expected: str, check: str | None
) -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post("100", article=article("90"))})
        assert request.url.path == "/2/tweets/90"
        if case in {"missing", "rate_limit"}:
            return httpx.Response(404 if case == "missing" else 429)
        if case == "timeout":
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        return httpx.Response(
            200,
            json={
                "data": post(
                    "99" if case == "wrong_id" else "90",
                    text="Preview…" if case == "truncated" else TEXT,
                ),
                **(
                    {"includes": {"tweets": [post("100", text="Changed version")]}}
                    if case == "conflict"
                    else {}
                ),
                **({"errors": [{"title": "Unavailable dependency"}]} if case == "partial" else {}),
            },
        )

    result = acquire(respond)
    assert result.text is None and result.failure == expected
    if check:
        assert f"check={check}" in caplog.text
    assert calls == ["/2/tweets/100", "/2/tweets/90"]


def test_embedded_reads_share_the_twelve_request_limit(caplog: pytest.LogCaptureFixture) -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        identifier = request.url.path.rsplit("/", 1)[-1]
        return httpx.Response(
            200, json={"data": post(identifier, article=article(str(int(identifier) - 1)))}
        )

    result = acquire(respond)
    assert result.text is None and result.failure == "partial_content"
    assert "check=request_limit" in caplog.text and len(calls) == 12
    assert len(set(calls)) == 12


def test_post_limit_stops_embedded_reads_before_spending(caplog: pytest.LogCaptureFixture) -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(
            200,
            json={
                "data": post("100", article=article("90")),
                "includes": {"tweets": [post(str(identifier)) for identifier in range(101, 200)]},
            },
        )

    result = acquire(respond)
    assert result.text is None and result.failure == "too_large"
    assert "check=post_count_limit" in caplog.text
    assert calls == ["/2/tweets/100"]


def test_embedded_reads_remain_inside_the_acquisition_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deadline = asyncio.timeout
    limits: list[float | None] = []
    calls: list[str] = []

    def short_deadline(delay: float | None) -> asyncio.Timeout:
        limits.append(delay)
        return deadline(0.02)

    async def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(200, json={"data": post("100", article=article("90"))})
        await asyncio.sleep(0.1)
        return httpx.Response(200, json={"data": post("90")})

    monkeypatch.setattr(asyncio, "timeout", short_deadline)
    result = asyncio.run(
        XAdapter("offline-test-token", transport=httpx.MockTransport(respond)).fetch(
            "https://x.com/user/status/100"
        )
    )
    assert result.text is None and result.failure == "unavailable"
    assert limits == [60] and calls == ["/2/tweets/100", "/2/tweets/90"]
