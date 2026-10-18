"""Bounded official X post/thread reads. Never scrape or retry a rejected read."""

import asyncio
import json
import re
from typing import Annotated

import httpx
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

from linksifty.domain.acquisition import FetchFailure, FetchResult
from linksifty.domain.content_policy import ContentReadiness, evaluate_content
from linksifty.domain.x_urls import x_post_id

_MAX_POSTS = 100
_MAX_PAGES = 10
_MAX_BODY_BYTES = 1_000_000
_MAX_TEXT_BYTES = 100_000
# Keep the wire names used by X's lookup quickstart and SDK. Response aliases
# below also accept the renamed fields shown in parts of the API reference.
_FIELDS = "text,author_id,conversation_id,note_tweet,referenced_tweets,attachments,article,withheld"
_TRUNCATED = re.compile(r"(?:…|\.{3})(?:\s+https?://\S+)?\s*$")
_Identifier = Annotated[str, Field(pattern=r"^[0-9]{1,19}$")]


class _Reference(BaseModel):
    model_config = ConfigDict(strict=True)
    id: _Identifier
    type: str


class _Note(BaseModel):
    model_config = ConfigDict(strict=True)
    text: str = Field(min_length=1)


class _Post(BaseModel):
    model_config = ConfigDict(strict=True)
    id: _Identifier
    author_id: _Identifier
    conversation_id: _Identifier
    text: str = Field(min_length=1)
    note: _Note | None = Field(
        default=None, validation_alias=AliasChoices("note_post", "note_tweet")
    )
    references: list[_Reference] = Field(
        default_factory=list, validation_alias=AliasChoices("referenced_posts", "referenced_tweets")
    )
    attachments: dict[str, object] | None = None
    article: dict[str, object] | None = None
    withheld: dict[str, object] | None = None

    def content(self) -> str:
        if self.attachments or self.article is not None or self.withheld:
            raise _Failure(FetchFailure.PARTIAL)
        if "note" in self.model_fields_set:
            if self.note is None or not self.note.text.strip():
                raise _Failure(FetchFailure.PARTIAL)
            return self.note.text
        if not self.text.strip() or _TRUNCATED.search(self.text):
            raise _Failure(FetchFailure.PARTIAL)
        return self.text

    def parent(self) -> str | None:
        if len(self.references) > 1 or any(ref.type != "replied_to" for ref in self.references):
            raise _Failure(FetchFailure.PARTIAL)
        return self.references[0].id if self.references else None


class _Lookup(BaseModel):
    data: _Post


class _Meta(BaseModel):
    model_config = ConfigDict(strict=True)
    result_count: int = Field(ge=0, le=100)
    next_token: str | None = Field(default=None, min_length=1, max_length=1024)


class _Search(BaseModel):
    data: list[_Post] = Field(default_factory=list, max_length=100)
    meta: _Meta


class _Failure(Exception):
    def __init__(self, reason: FetchFailure) -> None:
        self.reason = reason


class XAdapter:
    def __init__(self, token: str, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._token = token
        self._transport = transport

    async def fetch(self, url: str) -> FetchResult:
        identifier = x_post_id(url)
        if identifier is None:
            return FetchResult(failure=FetchFailure.UNSAFE_URL)
        try:
            async with asyncio.timeout(60):
                async with httpx.AsyncClient(
                    transport=self._transport, trust_env=False, follow_redirects=False, timeout=10
                ) as client:
                    return await self._thread(client, identifier)
        except _Failure as failure:
            return FetchResult(failure=failure.reason)
        except (ValidationError, ValueError, UnicodeError):
            return FetchResult(failure=FetchFailure.PARTIAL)
        except (httpx.HTTPError, TimeoutError):
            return FetchResult(failure=FetchFailure.UNAVAILABLE)

    async def _get(self, client: httpx.AsyncClient, path: str, **params: str) -> dict[str, object]:
        async with client.stream(
            "GET",
            f"https://api.x.com/2/tweets/{path}",
            params={"tweet.fields": _FIELDS, **params},
            headers={"Authorization": f"Bearer {self._token}", "Accept": "application/json"},
        ) as response:
            failure = {
                401: FetchFailure.X_ACCESS_DENIED,
                402: FetchFailure.X_ACCESS_DENIED,
                403: FetchFailure.X_ACCESS_DENIED,
                404: FetchFailure.X_NOT_FOUND,
                429: FetchFailure.X_RATE_LIMITED,
            }.get(response.status_code)
            if failure is not None:
                raise _Failure(failure)
            if response.status_code != 200:
                raise _Failure(FetchFailure.UNAVAILABLE)
            if response.headers.get("content-type", "").split(";", 1)[0] != "application/json":
                raise _Failure(FetchFailure.PARTIAL)
            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > _MAX_BODY_BYTES:
                    raise _Failure(FetchFailure.TOO_LARGE)
            payload: object = json.loads(body)
            if not isinstance(payload, dict) or payload.get("errors"):
                raise _Failure(FetchFailure.PARTIAL)
            return payload

    async def _lookup(self, client: httpx.AsyncClient, identifier: str) -> _Post:
        post = _Lookup.model_validate(await self._get(client, identifier)).data
        if post.id != identifier:
            raise _Failure(FetchFailure.PARTIAL)
        return post

    async def _thread(self, client: httpx.AsyncClient, identifier: str) -> FetchResult:
        selected = await self._lookup(client, identifier)
        root = (
            selected
            if selected.conversation_id == identifier
            else await self._lookup(client, selected.conversation_id)
        )
        if (
            root.conversation_id != root.id
            or root.author_id != selected.author_id
            or root.parent() is not None
        ):
            raise _Failure(FetchFailure.PARTIAL)
        posts = {root.id: root}
        # Validate before requesting more potentially billed resources.
        root.content()
        selected.content()
        selected.parent()
        token: str | None = None
        seen_tokens: set[str] = set()
        for _ in range(_MAX_PAGES):
            query = {
                "query": f"conversation_id:{root.id} from:{root.author_id}",
                "max_results": "100",
                "start_time": "2006-03-21T00:00:00Z",
                "sort_order": "recency",
            }
            if token is not None:
                query["next_token"] = token
            page = _Search.model_validate(await self._get(client, "search/all", **query))
            if page.meta.result_count != len(page.data):
                raise _Failure(FetchFailure.PARTIAL)
            for post in page.data:
                if post.author_id != root.author_id or post.conversation_id != root.id:
                    raise _Failure(FetchFailure.PARTIAL)
                if post.id in posts and self._identity(posts[post.id]) != self._identity(post):
                    raise _Failure(FetchFailure.PARTIAL)
                posts[post.id] = post
                if len(posts) > _MAX_POSTS:
                    raise _Failure(FetchFailure.TOO_LARGE)
            token = page.meta.next_token
            if token is None:
                break
            if token in seen_tokens:
                raise _Failure(FetchFailure.PARTIAL)
            seen_tokens.add(token)
        else:
            raise _Failure(FetchFailure.PARTIAL)
        if identifier not in posts or self._identity(posts[identifier]) != self._identity(selected):
            raise _Failure(FetchFailure.PARTIAL)
        ordered = [root]
        remaining = {key: value for key, value in posts.items() if key != root.id}
        visited = {root.id}
        while remaining:
            ready = sorted(
                (post for post in remaining.values() if post.parent() in visited),
                key=lambda post: int(post.id),
            )
            if not ready:
                raise _Failure(FetchFailure.PARTIAL)
            for post in ready:
                ordered.append(post)
                visited.add(post.id)
                del remaining[post.id]
        # Source URLs aid citations but must not make short posts pass the minimum.
        readable_text = "\n\n".join(post.content() for post in ordered)
        if evaluate_content(readable_text, fetched=False).readiness is not ContentReadiness.READY:
            raise _Failure(FetchFailure.TOO_SHORT)
        text = "\n\n".join(
            f"https://x.com/i/web/status/{post.id}\n{post.content()}" for post in ordered
        )
        if len(text.encode("utf-8")) > _MAX_TEXT_BYTES:
            raise _Failure(FetchFailure.TOO_LARGE)
        return FetchResult(text=text)

    @staticmethod
    def _identity(post: _Post) -> tuple[str, str, str | None, str]:
        return post.author_id, post.conversation_id, post.parent(), post.content()
