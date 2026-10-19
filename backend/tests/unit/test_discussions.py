import asyncio
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

import pytest

from linksifty.application.discussions import (
    Discussion,
    DiscussionClaim,
    DiscussionReply,
    DiscussionResult,
    DiscussionService,
    DiscussionStore,
)


def test_reply_loading_is_explicit_owner_scoped_and_cached_once() -> None:
    async def run() -> None:
        user, item, attempt = uuid4(), uuid4(), uuid4()
        source = Discussion(source_id="primary", url="https://x.com/user/status/100")
        store = create_autospec(DiscussionStore, instance=True)
        store.history.return_value = [source]
        store.begin.return_value = DiscussionClaim(
            **source.model_dump(), admitted=True, attempt_id=attempt
        )
        reply = DiscussionReply(id="101", author_id="70", text="A reader's actual reply.")
        result = DiscussionResult(status="ready", replies=[reply])
        store.finish.return_value = source.model_copy(
            update={"status": "ready", "replies": [reply]}
        )
        fetch = AsyncMock(return_value=result)
        service = DiscussionService(store, fetch)
        history = await service.history(user, item)
        assert history.available and history.sources[0].platform == "x"
        fetch.assert_not_awaited()
        loaded = await service.load(user, item, "primary", consent=True)
        assert loaded.replies == [reply]
        store.begin.assert_awaited_once_with(user, item, "primary")
        store.finish.assert_awaited_once_with(user, item, attempt, result)
        fetch.assert_awaited_once_with(source.url)
        store.begin.return_value = DiscussionClaim(
            **loaded.model_dump(), admitted=False, attempt_id=attempt
        )
        assert (await service.load(user, item, "primary", consent=True)).status == "ready"
        fetch.assert_awaited_once()

    asyncio.run(run())


@pytest.mark.parametrize("reason", ["consent", "foreign", "not_configured", "reddit"])
def test_rejected_discussion_requests_never_admit_or_fetch(reason: str) -> None:
    async def run() -> None:
        store = create_autospec(DiscussionStore, instance=True)
        source = Discussion(source_id="primary", url="https://x.com/user/status/100")
        if reason == "reddit":
            source.url = "https://www.reddit.com/r/example/comments/abc/topic"
        store.history.return_value = None if reason == "foreign" else [source]
        fetch = AsyncMock()
        service = DiscussionService(store, None if reason == "not_configured" else fetch)
        with pytest.raises(ValueError):
            await service.load(uuid4(), uuid4(), "primary", consent=reason != "consent")
        store.begin.assert_not_awaited()
        fetch.assert_not_awaited()

    asyncio.run(run())


def test_uncertain_admission_and_failed_persistence_never_repeat_the_provider_call() -> None:
    async def run() -> None:
        store = create_autospec(DiscussionStore, instance=True)
        source = Discussion(source_id="primary", url="https://x.com/user/status/100")
        store.history.return_value = [source]
        claim = DiscussionClaim(
            **source.model_dump(exclude={"status"}),
            status="fetching",
            admitted=True,
            attempt_id=uuid4(),
        )
        store.begin.return_value = claim
        fetch = AsyncMock(return_value=DiscussionResult(status="unavailable"))
        store.finish.side_effect = RuntimeError("simulated persistence outage")
        service = DiscussionService(store, fetch)
        with pytest.raises(RuntimeError):
            await service.load(uuid4(), uuid4(), "primary", consent=True)
        store.begin.return_value = claim.model_copy(update={"admitted": False})
        assert (await service.load(uuid4(), uuid4(), "primary", consent=True)).status == "fetching"
        fetch.assert_awaited_once()

    asyncio.run(run())


def test_social_source_list_filters_unsafe_and_ordinary_links_without_fetching() -> None:
    async def run() -> None:
        store = create_autospec(DiscussionStore, instance=True)
        store.history.return_value = [
            Discussion(source_id="primary", url="https://example.test/article"),
            Discussion(source_id="x", url="https://x.com/reader/status/100?s=20"),
            Discussion(source_id="reddit", url="https://old.reddit.com/r/test/comments/abc"),
            Discussion(source_id="unsafe", url="javascript:alert(1)"),
            Discussion(source_id="spoof", url="https://reddit.com.evil.test/thread"),
        ]
        result = await DiscussionService(store, None).history(uuid4(), uuid4())
        assert not result.available
        assert [(source.source_id, source.status) for source in result.sources] == [
            ("x", "not_requested"),
            ("reddit", "unsupported"),
        ]

    asyncio.run(run())
