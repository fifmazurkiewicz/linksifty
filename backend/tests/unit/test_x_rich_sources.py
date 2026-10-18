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
def test_video_is_explicitly_unsupported_not_silently_omitted(kind: str) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": post(attachments={"media_keys": ["media"]}),
                    "includes": {"media": [{"media_key": "media", "type": kind, "url": IMAGE_URL}]},
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
    media_count = 5 if kind == "count" else 1
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
