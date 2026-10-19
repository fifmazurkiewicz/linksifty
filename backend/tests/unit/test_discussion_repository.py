import asyncio
import json
from uuid import uuid4

import httpx

from linksifty.application.discussions import DiscussionReply, DiscussionResult
from linksifty.infrastructure.discussion_repository import DiscussionRepository


def test_discussion_rpcs_always_carry_owner_item_and_the_server_attempt() -> None:
    user, item, attempt = uuid4(), uuid4(), uuid4()
    source = {
        "source_id": "primary",
        "url": "https://x.com/u/status/100",
        "status": "fetching",
        "replies": [],
    }

    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["p_user_id"] == str(user) and payload["p_item_id"] == str(item)
        if request.url.path.endswith("get_item_discussions"):
            return httpx.Response(200, json=[{"sources": [source]}])
        if request.url.path.endswith("begin_item_discussion"):
            assert payload["p_source_id"] == "primary"
            return httpx.Response(
                200, json=[{**source, "admitted": True, "attempt_id": str(attempt)}]
            )
        assert request.url.path.endswith("finish_item_discussion")
        assert payload["p_attempt_id"] == str(attempt) and payload["p_status"] == "ready"
        assert payload["p_replies"][0]["text"] == "Real reader text"
        return httpx.Response(
            200, json=[{**source, "status": "ready", "replies": payload["p_replies"]}]
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repository = DiscussionRepository("https://supabase.example", "test-key", client)
            assert await repository.history(user, item)
            claim = await repository.begin(user, item, "primary")
            assert claim is not None and claim.admitted
            result = await repository.finish(
                user,
                item,
                attempt,
                DiscussionResult(
                    status="ready",
                    replies=[DiscussionReply(id="101", author_id="70", text="Real reader text")],
                ),
            )
            assert result is not None and result.replies[0].text == "Real reader text"

    asyncio.run(run())
