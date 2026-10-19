"""Owner-scoped, explicitly requested reader replies; never assessment evidence."""

from collections.abc import Awaitable, Callable
from typing import Literal, Protocol
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, Field

from linksifty.domain.x_urls import x_post_id


class DiscussionReply(BaseModel):
    id: str = Field(pattern=r"^[0-9]{1,19}$")
    author_id: str = Field(pattern=r"^[0-9]{1,19}$")
    username: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_]{1,15}$")
    text: str = Field(min_length=1, max_length=4000)
    truncated: bool = False
    has_media: bool = False


class DiscussionResult(BaseModel):
    status: Literal["ready", "unavailable"]
    replies: list[DiscussionReply] = Field(default_factory=list, max_length=20)


class Discussion(BaseModel):
    source_id: str
    url: str
    platform: Literal["x", "reddit"] | None = None
    status: Literal["not_requested", "fetching", "ready", "unavailable", "unsupported"] = (
        "not_requested"
    )
    replies: list[DiscussionReply] = Field(default_factory=list, max_length=20)


class DiscussionClaim(Discussion):
    admitted: bool
    attempt_id: UUID


class DiscussionHistory(BaseModel):
    available: bool
    sources: list[Discussion]


def discussion_platform(url: str) -> Literal["x", "reddit"] | None:
    if x_post_id(url) is not None:
        return "x"
    try:
        target = urlsplit(url)
        if (
            target.scheme in {"https", "http"}
            and target.hostname
            in {"reddit.com", "www.reddit.com", "old.reddit.com", "new.reddit.com"}
            and target.username is None
            and target.password is None
            and target.port in {None, 80 if target.scheme == "http" else 443}
            and "\\" not in url
            and not any(ord(char) <= 32 or ord(char) == 127 for char in url)
        ):
            return "reddit"
    except ValueError:
        pass
    return None


class DiscussionStore(Protocol):
    async def history(self, user_id: UUID, item_id: UUID) -> list[Discussion] | None: ...
    async def begin(
        self, user_id: UUID, item_id: UUID, source_id: str
    ) -> DiscussionClaim | None: ...
    async def finish(
        self, user_id: UUID, item_id: UUID, attempt_id: UUID, result: DiscussionResult
    ) -> Discussion | None: ...


class DiscussionService:
    def __init__(
        self,
        store: DiscussionStore,
        fetch: Callable[[str], Awaitable[DiscussionResult]] | None,
    ) -> None:
        self._store = store
        self._fetch = fetch

    async def history(self, user_id: UUID, item_id: UUID) -> DiscussionHistory:
        sources = await self._store.history(user_id, item_id)
        if sources is None:
            raise ValueError("not_found")
        visible: list[Discussion] = []
        for source in sources:
            platform = discussion_platform(source.url)
            if platform is not None:
                visible.append(
                    source.model_copy(
                        update={
                            "platform": platform,
                            "status": "unsupported" if platform == "reddit" else source.status,
                        }
                    )
                )
        return DiscussionHistory(available=self._fetch is not None, sources=visible)

    async def load(
        self, user_id: UUID, item_id: UUID, source_id: str, *, consent: bool
    ) -> Discussion:
        if not consent:
            raise ValueError("consent_required")
        history = await self.history(user_id, item_id)
        source = next((source for source in history.sources if source.source_id == source_id), None)
        if source is None:
            raise ValueError("not_found")
        if source.platform != "x":
            raise ValueError("unsupported")
        if self._fetch is None:
            raise ValueError("not_configured")
        claim = await self._store.begin(user_id, item_id, source_id)
        if claim is None:
            raise ValueError("not_found")
        if not claim.admitted:
            return Discussion.model_validate(claim.model_dump()).model_copy(
                update={"platform": "x"}
            )
        if x_post_id(claim.url) != x_post_id(source.url):
            raise ValueError("source_changed")
        result = await self._fetch(claim.url)
        saved = await self._store.finish(user_id, item_id, claim.attempt_id, result)
        if saved is None:
            raise ValueError("not_found")
        return saved.model_copy(update={"platform": "x"})
