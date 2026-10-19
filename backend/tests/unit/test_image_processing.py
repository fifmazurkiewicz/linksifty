import asyncio
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

import pytest

from linksifty.application.media_contracts import ImageReader, MediaResult
from linksifty.application.processing_contracts import (
    AssessmentProvider,
    ProcessingJob,
    ProcessingStore,
    Telemetry,
)
from linksifty.application.processing_service import ProcessingService
from linksifty.domain.acquisition import FetchResult, SourceImage

TEXT = "Complete primary evidence with concrete, reproducible details. " * 8
IMAGE = SourceImage(
    url="https://pbs.twimg.com/media/source.png",
    source_url="https://x.com/i/web/status/100",
    mime_type="image/png",
    data=b"validated-image",
)


@pytest.mark.parametrize(
    "outcome", ["complete", "unreadable", "uncertain", "budget", "unconfigured"]
)
def test_image_reading_is_budgeted_and_complete_before_assessment(outcome: str) -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.begin_x_fetch.return_value = True
        store.save_source.return_value = True
        store.reserve.return_value = None
        reservation = uuid4()
        store.reserve_images = AsyncMock(return_value=None if outcome == "budget" else reservation)
        store.record_image_generation = AsyncMock()
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.estimate.return_value = Decimal("0.14848")
        reader = create_autospec(ImageReader, instance=True)
        reader.estimate.return_value = Decimal("0.16896")
        reader.extract.return_value = MediaResult(
            text="Model-extracted image transcription: " + TEXT if outcome == "complete" else None,
            readable_text=TEXT if outcome == "complete" else None,
            generation_id="generation",
            cost=None if outcome == "uncertain" else Decimal("0.004"),
            failure_reason=None if outcome == "complete" else "image_reading_failed",
            failure_check="image_incomplete" if outcome == "unreadable" else None,
        )
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            original_url="https://x.com/user/status/100",
        )
        telemetry = create_autospec(Telemetry, instance=True)
        service = ProcessingService(
            cast(ProcessingStore, store),
            cast(AssessmentProvider, provider),
            AsyncMock(),
            x_fetch=AsyncMock(return_value=FetchResult(text=TEXT, images=(IMAGE,))),
            image_reader=None if outcome == "unconfigured" else cast(ImageReader, reader),
            telemetry=cast(Telemetry, telemetry),
        )
        await service.process(job)
        provider.assess.assert_not_awaited()
        if outcome == "complete":
            store.reserve_images.assert_awaited_once_with(job, Decimal("0.16896"))
            store.record_image_generation.assert_awaited_once_with(job, reservation, "generation")
            store.settle.assert_awaited_once_with(job.user_id, reservation, Decimal("0.004"))
            assert "Model-extracted" in store.save_source.await_args.args[1]
            store.reserve.assert_awaited_once()
        else:
            store.save_source.assert_not_awaited()
            store.reserve.assert_not_awaited()
            if outcome in {"budget", "unconfigured"}:
                reader.extract.assert_not_awaited()
            elif outcome == "uncertain":
                store.settle.assert_not_awaited()
                store.stage.assert_awaited_with(
                    job, "image_reading_uncertain", "awaiting_manual_content"
                )
            else:
                telemetry.event.assert_any_call(
                    "image.reading",
                    {
                        "images": 1,
                        "failure": "image_reading_failed",
                        "check": "image_incomplete",
                        "cost_known": True,
                    },
                )
                store.settle.assert_awaited_once()
                store.stage.assert_awaited_with(
                    job, "image_reading_failed", "awaiting_manual_content"
                )

    asyncio.run(run())


@pytest.mark.parametrize("image_count", [1, 11])
def test_runtime_composes_article_images_reading_accounting_and_source_cache(
    image_count: int,
) -> None:
    import io
    import json
    from dataclasses import replace

    import httpx
    from PIL import Image

    from linksifty.config import Settings
    from linksifty.main import create_app

    buffer = io.BytesIO()
    Image.new("RGB", (2, 2)).save(buffer, format="PNG")
    reservation = str(uuid4())
    events: list[str] = []
    saved: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        host, path = request.url.host, request.url.path
        if host == "api.x.com":
            if path == "/2/tweets/100":
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "id": "100",
                            "author_id": "50",
                            "conversation_id": "100",
                            "text": "Preview…",
                            "article": {"title": "Complete article", "text": TEXT},
                            "attachments": {
                                "media_keys": [f"image{i}" for i in range(image_count)]
                            },
                        },
                        "includes": {
                            "media": [
                                {
                                    "media_key": f"image{i}",
                                    "type": "photo",
                                    "url": f"https://pbs.twimg.com/media/source{i}.png",
                                }
                                for i in range(image_count)
                            ]
                        },
                    },
                )
            return httpx.Response(200, json={"meta": {"result_count": 0}})
        if host == "pbs.twimg.com":
            assert "authorization" not in request.headers
            return httpx.Response(
                200, content=buffer.getvalue(), headers={"content-type": "image/png"}
            )
        if host == "openrouter.ai":
            events.append("inference")
            sent = json.loads(request.content)
            assert sent["max_tokens"] == 8192
            assert sent["model"] == "openai/gpt-4.1-mini"
            assert len(sent["messages"][1]["content"]) == 2 * image_count
            return httpx.Response(
                200,
                json={
                    "id": "image-gen",
                    "usage": {"cost": "0.004"},
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {
                                "content": json.dumps(
                                    {
                                        "images": [
                                            {
                                                "image_id": f"image{i}",
                                                "complete": True,
                                                "transcription": TEXT,
                                                "description": "Input points to output.",
                                            }
                                            for i in range(1, image_count + 1)
                                        ]
                                    }
                                )
                            },
                        }
                    ],
                },
            )
        assert host == "supabase.example"
        name = path.rsplit("/", 1)[-1]
        events.append(name)
        if name == "begin_x_fetch":
            return httpx.Response(200, json=[{"admitted": True}])
        if name == "reserve_image_reading":
            return httpx.Response(200, json=[{"id": reservation}])
        if name == "save_job_source":
            saved.append(json.loads(request.content)["p_text"])
        if name == "reserve_analysis":
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=[{}])

    async def run() -> None:
        config = replace(
            Settings.for_test(),
            demo_mode=False,
            x_api_reads_enabled=True,
            x_api_bearer_token="test-x-token",
        )
        app = create_app(config, transport=httpx.MockTransport(respond))
        async with app.router.lifespan_context(app):
            processor = cast(ProcessingService, app.state.processing)
            await processor.process(
                ProcessingJob(
                    id=uuid4(),
                    item_id=uuid4(),
                    user_id=uuid4(),
                    lease_token=uuid4(),
                    original_url="https://x.com/user/status/100",
                )
            )

    asyncio.run(run())
    assert len(saved) == 1
    assert "Complete article" in saved[0] and "Model-extracted image transcription" in saved[0]
    assert "Preview…" not in saved[0]
    assert events.index("reserve_image_reading") < events.index("inference")
    assert (
        events.index("record_image_generation")
        < events.index("settle_analysis")
        < events.index("save_job_source")
        < events.index("reserve_analysis")
    )
