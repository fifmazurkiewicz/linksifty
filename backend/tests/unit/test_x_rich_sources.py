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
def test_ignored_media_url_never_reaches_any_media_host(url: str) -> None:
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
    assert TEXT in (result.text or "")
    assert result.images == ()
    assert result.failure is None
    assert all(host == "api.x.com" for host in calls)


@pytest.mark.parametrize("kind", ["video", "animated_gif"])
@pytest.mark.parametrize("url", [IMAGE_URL, None])
def test_video_is_explicitly_marked_as_omitted(kind: str, url: str | None) -> None:
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
    assert TEXT in (result.text or "")
    assert result.images == ()
    assert result.failure is None
    assert result.omitted_media == (("gif",) if kind == "animated_gif" else ("video",))


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
    assert result.images == ()
    assert result.omitted_media == ("image",)


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
def test_article_media_presence_does_not_require_expansion(field: str, expanded: bool) -> None:
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
    assert result.failure is None and TEXT in (result.text or "")
    assert result.images == () and result.omitted_media == ("image",)
    assert not image_requests


def test_quoted_article_preserves_code_without_hydrating_or_downloading_media() -> None:
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
    assert result.images == ()
    assert set(result.omitted_media) == {"image"}
    assert "position unspecified" in (result.text or "")
    for code in snippets:
        assert code in (result.text or "")
    assert calls.count("https://api.x.com/2/tweets/90") == 0
    assert sum("api.x.com" in call for call in calls) == 2
    assert all("api.x.com" in call for call in calls)


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
