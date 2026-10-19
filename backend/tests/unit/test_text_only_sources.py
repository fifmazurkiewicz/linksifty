import asyncio
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

import httpx
import pytest

from linksifty.application.processing_contracts import (
    AssessmentProvider,
    ProcessingJob,
    ProcessingStore,
)
from linksifty.application.processing_service import ProcessingService
from linksifty.domain.acquisition import FetchResult
from linksifty.infrastructure.x_adapter import XAdapter

TEXT = (
    "Complete source text with substantive evidence, reproducible detail and qualifications. " * 8
)


@pytest.mark.parametrize(
    "kind,expected",
    [("photo", "image"), ("video", "video"), ("animated_gif", "gif"), ("missing", "attachment")],
)
def test_x_uses_complete_text_and_media_metadata_without_downloading(
    kind: str, expected: str
) -> None:
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.host == "api.x.com", "media must never be downloaded"
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "100",
                        "author_id": "50",
                        "conversation_id": "100",
                        "text": TEXT,
                        "attachments": {"media_keys": ["media"]},
                    },
                    "includes": {
                        "media": [] if kind == "missing" else [{"media_key": "media", "type": kind}]
                    },
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = asyncio.run(
        XAdapter("test", transport=httpx.MockTransport(respond)).fetch(
            "https://x.com/user/status/100"
        )
    )
    assert result.failure is None and TEXT in (result.text or "")
    assert result.omitted_media == (expected,)
    assert result.images == ()
    assert len(calls) == 2


@pytest.mark.parametrize("text", ["Watch this video", "Only a truncated preview…"])
def test_media_presence_never_makes_short_or_truncated_text_readable(text: str) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/tweets/100":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "100",
                        "author_id": "50",
                        "conversation_id": "100",
                        "text": text,
                        "attachments": {"media_keys": ["media"]},
                    },
                    "includes": {"media": [{"media_key": "media", "type": "video"}]},
                },
            )
        return httpx.Response(200, json={"meta": {"result_count": 0}})

    result = asyncio.run(
        XAdapter("test", transport=httpx.MockTransport(respond)).fetch(
            "https://x.com/user/status/100"
        )
    )
    assert result.text is None
    assert result.failure in {"too_short", "partial_content"}


def test_processing_saves_text_scope_without_any_image_reservation() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.begin_x_fetch.return_value = True
        store.save_source.return_value = True
        store.reserve.return_value = None
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.estimate.return_value = Decimal("0.01")
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            original_url="https://x.com/user/status/100",
        )
        fetch = AsyncMock(
            return_value=FetchResult(
                text=TEXT, readable_text=TEXT, omitted_media=("image", "video")
            )
        )
        service = ProcessingService(
            cast(ProcessingStore, store),
            cast(AssessmentProvider, provider),
            AsyncMock(),
            x_fetch=fetch,
        )
        await service.process(job)
        store.save_source.assert_awaited_once_with(job, TEXT, omitted_media=("image", "video"))
        store.reserve_images.assert_not_awaited()
        store.record_image_generation.assert_not_awaited()
        store.reserve.assert_awaited_once()

    asyncio.run(run())
