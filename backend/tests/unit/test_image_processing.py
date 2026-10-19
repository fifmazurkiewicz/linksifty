import asyncio
from typing import cast
from uuid import uuid4

import pytest

from linksifty.application.processing_contracts import (
    ProcessingJob,
)
from linksifty.application.processing_service import ProcessingService

TEXT = "Complete primary evidence with concrete, reproducible details. " * 8


@pytest.mark.parametrize("image_count", [1, 11])
def test_runtime_caches_article_text_and_scope_without_media_costs(
    image_count: int,
) -> None:
    import json
    from dataclasses import replace

    import httpx

    from linksifty.config import Settings
    from linksifty.main import create_app

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
            raise AssertionError("Text-only acquisition must not fetch media")
        if host == "openrouter.ai":
            raise AssertionError("Text-only acquisition must not invoke vision")
        assert host == "supabase.example"
        name = path.rsplit("/", 1)[-1]
        events.append(name)
        if name == "begin_x_fetch":
            return httpx.Response(200, json=[{"admitted": True}])
        if name == "reserve_image_reading":
            return httpx.Response(200, json=[{"id": reservation}])
        if name == "save_text_job_source":
            assert json.loads(request.content)["p_media_types"] == ["image"]
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
    assert "Complete article" in saved[0] and "Model-extracted" not in saved[0]
    assert "Preview…" not in saved[0]
    assert "reserve_image_reading" not in events
    assert "inference" not in events
    assert "record_image_generation" not in events
    assert events.index("save_text_job_source") < events.index("reserve_analysis")
