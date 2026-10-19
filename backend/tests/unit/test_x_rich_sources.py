import asyncio
import struct
import zlib
from collections.abc import Callable

import httpx
import pytest

from linksifty.domain.acquisition import FetchResult
from linksifty.infrastructure.x_adapter import XAdapter

TEXT = "Complete article body with substantive evidence, conditions and conclusions. " * 8
IMAGE_URL = "https://pbs.twimg.com/media/example.png"


def png(width: int = 2, height: int = 2) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress((b"\x00" + b"\x00" * width * 3) * height))
        + chunk(b"IEND", b"")
    )


def post(**extra: object) -> dict[str, object]:
    return {"id": "100", "author_id": "50", "conversation_id": "100", "text": TEXT, **extra}


def acquire(handler: Callable[[httpx.Request], httpx.Response]) -> FetchResult:
    return asyncio.run(
        XAdapter("private-test-token", transport=httpx.MockTransport(handler)).fetch(
            "https://x.com/user/status/100"
        )
    )


@pytest.mark.parametrize("field", ["text", "plain_text"])
def test_full_article_body_replaces_post_preview(field: str) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(
                        text="Article preview…",
                        article={"title": "Article title", field: TEXT, "entities": {}},
                    )
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.failure is None
    assert TEXT in (result.text or "")
    assert "Article title" in (result.text or "")
    assert "Article preview…" not in (result.text or "")


@pytest.mark.parametrize(
    "article",
    [
        {"title": "Only a title"},
        {"title": "Preview", "preview_text": TEXT},
        {"title": "Body truncated", "text": "Incomplete…"},
    ],
)
def test_preview_only_articles_never_return_assessment_source(article: object) -> None:
    result = acquire(lambda _: httpx.Response(200, json={"data": post(article=article)}))
    assert result.text is None
    assert result.failure == "x_article_incomplete"


def test_static_image_is_acquired_without_x_credentials_and_without_lowering_minimum() -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host or "")
        if request.url.host == "pbs.twimg.com":
            assert "authorization" not in request.headers and "cookie" not in request.headers
            return httpx.Response(200, content=png(), headers={"content-type": "image/png"})
        if request.url.path == "/2/tweets/100":
            assert "attachments.media_keys" in request.url.params["expansions"]
            return httpx.Response(
                200,
                json={
                    "data": post(text="Short caption", attachments={"media_keys": ["3_image"]}),
                    "includes": {
                        "media": [{"media_key": "3_image", "type": "photo", "url": IMAGE_URL}]
                    },
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.failure is None
    assert len(result.images) == 1
    assert result.images[0].data == png()
    assert result.images[0].url == IMAGE_URL
    assert result.images[0].source_url == "https://x.com/i/web/status/100"
    assert calls.count("pbs.twimg.com") == 1


@pytest.mark.parametrize(
    "url",
    [
        "http://pbs.twimg.com/media/image.png",
        "https://evil.test/a.png",
        "https://pbs.twimg.com.evil.test/a.png",
        "https://key@pbs.twimg.com/a.png",
        "https://pbs.twimg.com:444/a.png",
        "https://127.0.0.1/a.png",
    ],
)
def test_untrusted_media_url_is_rejected_before_any_media_request(url: str) -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host or "")
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(attachments={"media_keys": ["3_image"]}),
                    "includes": {"media": [{"media_key": "3_image", "type": "photo", "url": url}]},
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "x_media_unavailable"
    assert all(host == "api.x.com" for host in calls)


@pytest.mark.parametrize("kind", ["video", "animated_gif"])
@pytest.mark.parametrize("url", [IMAGE_URL, None])
def test_video_is_explicitly_unsupported_not_silently_omitted(kind: str, url: str | None) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(attachments={"media_keys": ["media"]}),
                    "includes": {"media": [{"media_key": "media", "type": kind, "url": url}]},
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "x_media_unsupported"


@pytest.mark.parametrize(
    "status,body,mime",
    [
        (302, b"", "image/png"),
        (206, b"prefix", "image/png"),
        (200, b"not-an-image", "image/png"),
        (200, png()[:-15], "image/png"),
        (200, png(), "text/html"),
    ],
)
def test_incomplete_or_invalid_image_never_returns_text(
    status: int, body: bytes, mime: str
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.host == "pbs.twimg.com":
            return httpx.Response(
                status,
                content=body,
                headers={"content-type": mime, "location": "https://evil.test/image.png"},
            )
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(attachments={"media_keys": ["image"]}),
                    "includes": {
                        "media": [{"media_key": "image", "type": "photo", "url": IMAGE_URL}]
                    },
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.text is None
    assert result.failure == "x_media_unavailable"


def test_quoted_article_includes_its_body_cover_and_embedded_post() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.host == "pbs.twimg.com":
            return httpx.Response(200, content=png(), headers={"content-type": "image/png"})
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(referenced_tweets=[{"type": "quoted", "id": "90"}]),
                    "includes": {
                        "tweets": [
                            post(
                                id="90",
                                author_id="70",
                                conversation_id="90",
                                text="Preview…",
                                article={
                                    "title": "Full article",
                                    "text": TEXT,
                                    "cover_media": {"media_key": "cover"},
                                    "entities": {"posts": ["80"]},
                                },
                            ),
                            post(
                                id="80",
                                author_id="80",
                                conversation_id="80",
                                text="Embedded evidence " * 25,
                            ),
                        ],
                        "media": [{"media_key": "cover", "type": "photo", "url": IMAGE_URL}],
                    },
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.failure is None
    assert "Full article" in (result.text or "")
    assert "Embedded evidence" in (result.text or "")
    assert "Preview…" not in (result.text or "")
    assert len(result.images) == 1
    assert result.images[0].source_url.endswith("/90")


@pytest.mark.parametrize(
    "kind,expected", [("unstyled", None), ("unknown-embed", "x_article_incomplete")]
)
def test_draftjs_body_is_complete_and_unknown_blocks_fail_closed(
    kind: str, expected: str | None
) -> None:

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(
                        article={
                            "title": "Article",
                            "content_state": {"blocks": [{"type": kind, "text": TEXT}]},
                        }
                    )
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.failure == expected
    assert (result.text is not None) is (expected is None)


def test_missing_article_embedded_source_never_returns_outer_post() -> None:
    result = acquire(
        lambda _: httpx.Response(
            200,
            json={
                "data": post(
                    article={"title": "Article", "text": TEXT, "entities": {"posts": ["90"]}}
                )
            },
        )
    )
    assert result.text is None
    assert result.failure == "partial_content"


def test_image_count_and_declared_size_are_checked_before_reading_large_bytes() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.host == "pbs.twimg.com":
            return httpx.Response(
                200, content=b"", headers={"content-type": "image/png", "content-length": "6000000"}
            )
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(attachments={"media_keys": ["image"]}),
                    "includes": {
                        "media": [{"media_key": "image", "type": "photo", "url": IMAGE_URL}]
                    },
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    assert acquire(respond).text is None


@pytest.mark.parametrize("kind", ["pixels", "animation", "count"])
def test_image_decode_and_count_bounds_require_manual_content(kind: str) -> None:
    import io

    from PIL import Image

    if kind == "pixels":
        data = png(5000, 4001)
    elif kind == "animation":
        buffer = io.BytesIO()
        Image.new("RGB", (2, 2), "red").save(
            buffer,
            format="PNG",
            save_all=True,
            append_images=[Image.new("RGB", (2, 2), "blue")],
        )
        data = buffer.getvalue()
    else:
        data = png()
    media_count = 13 if kind == "count" else 1
    media_calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.host == "pbs.twimg.com":
            media_calls.append(str(request.url))
            return httpx.Response(200, content=data, headers={"content-type": "image/png"})
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(attachments={"media_keys": [str(i) for i in range(media_count)]}),
                    "includes": {
                        "media": [
                            {"media_key": str(i), "type": "photo", "url": f"{IMAGE_URL}?id={i}"}
                            for i in range(media_count)
                        ]
                    },
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.text is None and not result.images
    assert result.failure == ("too_large" if kind == "count" else "x_media_unavailable")
    if kind == "count":
        assert not media_calls


@pytest.mark.parametrize(
    "article,check",
    [
        ({"title": "private-title"}, "article_body_missing"),
        ({"text": TEXT}, "article_title_missing"),
        ({"title": "private-title", "text": ""}, "article_body_empty"),
        ({"title": "private-title", "text": "private-body…"}, "article_body_truncated"),
        (
            {"title": "private-title", "text": TEXT, "preview_text": TEXT},
            "article_body_preview",
        ),
        (
            {"title": "private-title", "text": TEXT, "cover_media": {"private-key": "secret"}},
            "article_media_invalid",
        ),
        (
            {
                "title": "private-title",
                "content_state": {"blocks": [{"type": "private-kind", "text": TEXT}]},
            },
            "article_block_type_unsupported",
        ),
        (
            {"title": "private-title", "text": TEXT, "content_state": {"blocks": []}},
            "article_body_disagrees_with_blocks",
        ),
        (
            {"title": "private-title", "text": TEXT, "entities": {"posts": ["private-post"]}},
            "article_post_id_invalid",
        ),
    ],
)
def test_article_failure_logs_exact_check_without_content(
    caplog: pytest.LogCaptureFixture, article: dict[str, object], check: str
) -> None:
    result = acquire(lambda _: httpx.Response(200, json={"data": post(article=article)}))
    assert result.text is None and not result.images
    assert result.failure == "x_article_incomplete"
    assert f"check={check}" in caplog.text
    for private in ("private-title", "private-body", "private-key", "secret", "private-kind", TEXT):
        assert private not in caplog.text


@pytest.mark.parametrize("field", ["cover_media", "media_entities"])
@pytest.mark.parametrize("expanded", [True, False])
def test_article_media_key_references_require_expanded_valid_image(
    field: str, expanded: bool
) -> None:
    media_key = "3_400"
    article = {
        "title": "Article",
        "text": TEXT,
        field: media_key if field == "cover_media" else [media_key],
    }
    image_requests: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.host == "pbs.twimg.com":
            image_requests.append(str(request.url))
            return httpx.Response(200, content=png(), headers={"content-type": "image/png"})
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(article=article),
                    "includes": {
                        "media": [{"media_key": media_key, "type": "photo", "url": IMAGE_URL}]
                        if expanded
                        else []
                    },
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    if expanded:
        assert result.failure is None and TEXT in (result.text or "")
        assert len(result.images) == 1 and result.images[0].data == png()
        assert image_requests == [IMAGE_URL]
    else:
        assert result.text is None and not result.images
        assert result.failure == "x_media_unavailable"
        assert not image_requests


def test_quoted_article_hydrates_media_and_preserves_eleven_images_and_code() -> None:
    calls: list[str] = []
    snippets = ["print('exact code')", "def agent():\n    return 42", "git clone example"]
    article = {
        "title": "Captured schema, synthetic content",
        "plain_text": TEXT,
        "cover_media": "article0",
        "media_entities": [f"article{i}" for i in range(1, 10)],
        "entities": {
            "code": [
                {"code": code, "content": f"```python\n{code}\n```", "language": "python"}
                for code in snippets
            ],
            "mentions": [],
            "urls": [],
        },
    }
    quoted = post(id="90", conversation_id="90", text="Article preview…", article=article)

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url.copy_with(query=None)))
        if request.url.host == "pbs.twimg.com":
            assert "authorization" not in request.headers and "cookie" not in request.headers
            return httpx.Response(200, content=png(), headers={"content-type": "image/png"})
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(
                        attachments={"media_keys": ["outer"]},
                        referenced_tweets=[{"type": "quoted", "id": "90"}],
                    ),
                    "includes": {
                        "tweets": [quoted],
                        "media": [
                            {"media_key": "outer", "type": "photo", "url": f"{IMAGE_URL}?outer"}
                        ],
                    },
                },
            )
        if request.url.path == "/2/tweets/90":
            assert "article.media_entities" in request.url.params["expansions"]
            return httpx.Response(
                200,
                json={
                    "data": quoted,
                    "includes": {
                        "media": [
                            {
                                "media_key": f"article{i}",
                                "type": "photo",
                                "url": f"{IMAGE_URL}?article={i}",
                            }
                            for i in range(10)
                        ]
                    },
                },
            )
        assert request.url.path == "/2/tweets/search/all"
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = acquire(respond)
    assert result.failure is None
    assert len(result.images) == 11
    assert sum(image.source_url.endswith("/90") for image in result.images) == 10
    assert "position unspecified" in (result.text or "")
    for code in snippets:
        assert code in (result.text or "")
    assert calls.count("https://api.x.com/2/tweets/90") == 1
    assert sum("api.x.com" in call for call in calls) == 3


@pytest.mark.parametrize("outcome", ["missing", "denied", "changed"])
def test_quoted_article_lookup_failure_never_retries_or_returns_partial_source(
    outcome: str,
) -> None:
    calls: list[str] = []
    quoted = post(
        id="90",
        conversation_id="90",
        article={
            "title": "Article",
            "plain_text": TEXT,
            "cover_media": "missing",
        },
    )

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(referenced_tweets=[{"id": "90", "type": "quoted"}]),
                    "includes": {"tweets": [quoted]},
                },
            )
        assert request.url.path == "/2/tweets/90"
        return httpx.Response(
            403 if outcome == "denied" else 200,
            json={
                "data": {**quoted, "text": "changed"} if outcome == "changed" else quoted,
            },
        )

    result = acquire(respond)
    assert result.text is None and not result.images
    assert (
        result.failure
        == {
            "missing": "x_media_unavailable",
            "denied": "x_access_denied",
            "changed": "partial_content",
        }[outcome]
    )
    assert calls == ["/2/tweets/100", "/2/tweets/90"]


@pytest.mark.parametrize(
    "code",
    [
        None,
        "not a list",
        [{}],
        [{"code": 5}],
        [{"code": ""}],
        [{"code": "bad\x00code"}],
        [{"code": "print(1)", "content": "contradictory"}],
    ],
)
def test_malformed_article_code_is_explicitly_rejected(code: object) -> None:
    from linksifty.infrastructure.x_content import XContentFailure, parse_article

    with pytest.raises(XContentFailure) as failure:
        parse_article({"title": "Article", "plain_text": TEXT, "entities": {"code": code}})
    assert failure.value.reason == "x_article_incomplete"
    assert failure.value.check == "article_code_invalid"


def test_article_code_already_present_in_body_is_not_duplicated() -> None:
    from linksifty.infrastructure.x_content import parse_article

    result = parse_article(
        {
            "title": "Article",
            "plain_text": TEXT + "\nprint(42)",
            "entities": {"code": [{"code": "print(42)", "language": "python"}]},
        }
    )
    assert result.text.count("print(42)") == 1


def test_quoted_article_hydration_and_search_share_twelve_request_cap(
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls: list[str] = []
    quotes = [
        post(
            id=identifier,
            conversation_id=identifier,
            referenced_tweets=[{"type": "quoted", "id": "80"}] if identifier == "90" else [],
            article={"title": "Article", "plain_text": TEXT, "cover_media": identifier},
        )
        for identifier in ("90", "80")
    ]

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(referenced_tweets=[{"type": "quoted", "id": "90"}]),
                    "includes": {"tweets": quotes},
                },
            )
        if request.url.path in {"/2/tweets/90", "/2/tweets/80"}:
            identifier = request.url.path.rsplit("/", 1)[1]
            return httpx.Response(
                200,
                json={
                    "data": next(quote for quote in quotes if quote["id"] == identifier),
                    "includes": {
                        "media": [
                            {
                                "media_key": identifier,
                                "type": "photo",
                                "url": f"{IMAGE_URL}?id={identifier}",
                            }
                        ]
                    },
                },
            )
        assert request.url.path == "/2/tweets/search/all"
        return httpx.Response(
            200, json={"meta": {"result_count": 0, "next_token": str(len(calls))}}
        )

    result = acquire(respond)
    assert result.failure == "partial_content"
    assert len(calls) == 12
    assert "check=request_limit" in caplog.text


def test_unsafe_known_media_stops_before_billable_quoted_article_lookup() -> None:
    calls: list[str] = []
    quoted = post(
        id="90",
        conversation_id="90",
        article={
            "title": "Article",
            "plain_text": TEXT,
            "cover_media": "missing",
        },
    )

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(
                        attachments={"media_keys": ["unsafe"]},
                        referenced_tweets=[{"id": "90", "type": "quoted"}],
                    ),
                    "includes": {
                        "tweets": [quoted],
                        "media": [
                            {
                                "media_key": "unsafe",
                                "type": "photo",
                                "url": "https://evil.test/image",
                            }
                        ],
                    },
                },
            )
        return httpx.Response(200, json={"data": quoted})

    result = acquire(respond)
    assert result.failure == "x_media_unavailable" and result.text is None
    assert calls == ["/2/tweets/100"]
