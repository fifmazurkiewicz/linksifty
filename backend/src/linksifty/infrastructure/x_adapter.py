"""Bounded official X post/thread reads. Never scrape or retry a rejected read."""

import asyncio
import json
import logging
import re
from typing import Annotated

import httpx
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

from linksifty.domain.acquisition import FetchFailure, FetchResult
from linksifty.domain.content_policy import ContentReadiness, evaluate_content
from linksifty.domain.x_urls import x_post_id

_logger = logging.getLogger(__name__)
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
        if self.attachments:
            raise _Failure(FetchFailure.PARTIAL, "attachments_present")
        if self.article is not None:
            raise _Failure(FetchFailure.PARTIAL, "article_present")
        if self.withheld:
            raise _Failure(FetchFailure.PARTIAL, "withheld_content")
        # Repost text is an RT preview; only the referenced original is source text.
        if len(self.references) == 1 and self.references[0].type == "retweeted":
            return ""
        if "note" in self.model_fields_set:
            if self.note is None or not self.note.text.strip():
                raise _Failure(FetchFailure.PARTIAL, "missing_long_text")
            return self.note.text
        if not self.text.strip() or _TRUNCATED.search(self.text):
            raise _Failure(FetchFailure.PARTIAL, "empty_or_truncated_text")
        return self.text

    def parent(self) -> str | None:
        kinds = [ref.type for ref in self.references]
        if (
            len(kinds) != len(set(kinds))
            or any(kind not in {"replied_to", "quoted", "retweeted"} for kind in kinds)
            or ("retweeted" in kinds and len(kinds) != 1)
        ):
            raise _Failure(FetchFailure.PARTIAL, "unsupported_references")
        return next((ref.id for ref in self.references if ref.type == "replied_to"), None)


class _Includes(BaseModel):
    posts: list[_Post] = Field(
        default_factory=list,
        validation_alias=AliasChoices("posts", "tweets"),
        max_length=_MAX_POSTS,
    )


class _Lookup(BaseModel):
    data: _Post
    includes: _Includes = Field(default_factory=_Includes)


class _Meta(BaseModel):
    model_config = ConfigDict(strict=True)
    result_count: int = Field(ge=0, le=100)
    next_token: str | None = Field(default=None, min_length=1, max_length=1024)


class _Search(BaseModel):
    data: list[_Post] = Field(default_factory=list, max_length=100)
    meta: _Meta
    includes: _Includes = Field(default_factory=_Includes)


class _Failure(Exception):
    def __init__(self, reason: FetchFailure, check: str) -> None:
        self.reason = reason
        self.check = check


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
            _logger.warning("x_fetch_failed reason=%s check=%s", failure.reason, failure.check)
            return FetchResult(failure=failure.reason)
        except (ValidationError, ValueError, UnicodeError) as error:
            _logger.warning(
                "x_fetch_failed reason=partial_content error_type=%s", type(error).__name__
            )
            return FetchResult(failure=FetchFailure.PARTIAL)
        except (httpx.HTTPError, TimeoutError) as error:
            _logger.warning("x_fetch_failed reason=unavailable error_type=%s", type(error).__name__)
            return FetchResult(failure=FetchFailure.UNAVAILABLE)

    async def _get(self, client: httpx.AsyncClient, path: str, **params: str) -> dict[str, object]:
        async with client.stream(
            "GET",
            f"https://api.x.com/2/tweets/{path}",
            params={"tweet.fields": _FIELDS, "expansions": "referenced_tweets.id", **params},
            headers={"Authorization": f"Bearer {self._token}", "Accept": "application/json"},
        ) as response:
            if response.status_code != 200:
                # Fixed endpoint labels only: no post IDs, queries, headers or provider bodies.
                _logger.warning(
                    "x_api_request_failed endpoint=%s status=%s",
                    "full_archive_search" if path == "search/all" else "post_lookup",
                    response.status_code,
                )
            failure = {
                401: FetchFailure.X_ACCESS_DENIED,
                402: FetchFailure.X_ACCESS_DENIED,
                403: FetchFailure.X_ACCESS_DENIED,
                404: FetchFailure.X_NOT_FOUND,
                429: FetchFailure.X_RATE_LIMITED,
            }.get(response.status_code)
            if failure is not None:
                raise _Failure(failure, "http_status")
            if response.status_code != 200:
                raise _Failure(FetchFailure.UNAVAILABLE, "http_status")
            if response.headers.get("content-type", "").split(";", 1)[0] != "application/json":
                raise _Failure(FetchFailure.PARTIAL, "unexpected_content_type")
            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > _MAX_BODY_BYTES:
                    raise _Failure(FetchFailure.TOO_LARGE, "response_size_limit")
            payload: object = json.loads(body)
            if not isinstance(payload, dict):
                raise _Failure(FetchFailure.PARTIAL, "invalid_response_shape")
            if payload.get("errors"):
                raise _Failure(FetchFailure.PARTIAL, "provider_partial_errors")
            return payload

    async def _lookup(
        self, client: httpx.AsyncClient, identifier: str, available: dict[str, _Post]
    ) -> _Post:
        payload = await self._get(client, identifier)
        try:
            lookup = _Lookup.model_validate(payload)
        except ValidationError as error:
            raise _Failure(FetchFailure.PARTIAL, "invalid_post_payload") from error
        if lookup.data.id != identifier:
            raise _Failure(FetchFailure.PARTIAL, "lookup_id_mismatch")
        self._remember(available, [lookup.data, *lookup.includes.posts])
        return lookup.data

    async def _thread(self, client: httpx.AsyncClient, identifier: str) -> FetchResult:
        submitted_id = identifier
        available: dict[str, _Post] = {}
        selected = await self._lookup(client, identifier, available)
        reposts: set[str] = set()
        while True:
            selected.parent()
            original_id = next(
                (ref.id for ref in selected.references if ref.type == "retweeted"), None
            )
            if original_id is None:
                break
            selected.content()
            if selected.id in reposts:
                raise _Failure(FetchFailure.PARTIAL, "reference_cycle")
            reposts.add(selected.id)
            original = available.get(original_id)
            if original is None:
                raise _Failure(FetchFailure.PARTIAL, "missing_referenced_post")
            selected = original
        identifier = selected.id
        root = (
            selected
            if selected.conversation_id == identifier
            else await self._lookup(client, selected.conversation_id, available)
        )
        if (
            root.conversation_id != root.id
            or root.author_id != selected.author_id
            or root.parent() is not None
        ):
            raise _Failure(FetchFailure.PARTIAL, "invalid_conversation_root")
        posts = {root.id: root}
        # Validate before requesting more potentially billed resources.
        self._source_posts([root, selected], available)
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
            payload = await self._get(client, "search/all", **query)
            try:
                page = _Search.model_validate(payload)
            except ValidationError as error:
                raise _Failure(FetchFailure.PARTIAL, "invalid_search_payload") from error
            if page.meta.result_count != len(page.data):
                raise _Failure(FetchFailure.PARTIAL, "search_count_mismatch")
            self._remember(available, [*page.data, *page.includes.posts])
            for post in page.data:
                if post.author_id != root.author_id or post.conversation_id != root.id:
                    raise _Failure(FetchFailure.PARTIAL, "search_identity_mismatch")
                posts[post.id] = post
            token = page.meta.next_token
            if token is None:
                break
            if token in seen_tokens:
                raise _Failure(FetchFailure.PARTIAL, "repeated_pagination_token")
            seen_tokens.add(token)
        else:
            raise _Failure(FetchFailure.PARTIAL, "page_limit")
        if identifier not in posts:
            raise _Failure(FetchFailure.PARTIAL, "selected_post_missing_or_changed")
        ordered = [root]
        remaining = {key: value for key, value in posts.items() if key != root.id}
        visited = {root.id}
        while remaining:
            ready = sorted(
                (post for post in remaining.values() if post.parent() in visited),
                key=lambda post: int(post.id),
            )
            if not ready:
                raise _Failure(FetchFailure.PARTIAL, "disconnected_thread")
            for post in ready:
                ordered.append(post)
                visited.add(post.id)
                del remaining[post.id]
        sources = self._source_posts(ordered, available)
        # Labels, URLs and RT previews must not make short sources pass the minimum.
        readable_text = "\n\n".join(post.content() for post in sources)
        if evaluate_content(readable_text, fetched=False).readiness is not ContentReadiness.READY:
            raise _Failure(FetchFailure.TOO_SHORT, "minimum_text_length")
        text = "\n\n".join(
            f"https://x.com/i/web/status/{post.id}\nauthor_id={post.author_id}\n{post.content()}"
            + "".join(
                f"\n{ref.type}: https://x.com/i/web/status/{ref.id}" for ref in post.references
            )
            for post in sources
        )
        if reposts:
            text = f"Submitted repost: https://x.com/i/web/status/{submitted_id}\n\n{text}"
        if len(text.encode("utf-8")) > _MAX_TEXT_BYTES:
            raise _Failure(FetchFailure.TOO_LARGE, "text_size_limit")
        return FetchResult(text=text)

    @staticmethod
    def _remember(available: dict[str, _Post], posts: list[_Post]) -> None:
        for post in posts:
            previous = available.get(post.id)
            if previous is not None and (
                previous != post
                or ("note" in previous.model_fields_set) != ("note" in post.model_fields_set)
            ):
                raise _Failure(FetchFailure.PARTIAL, "conflicting_post_versions")
            available[post.id] = post
            if len(available) > _MAX_POSTS:
                raise _Failure(FetchFailure.TOO_LARGE, "post_count_limit")

    @staticmethod
    def _source_posts(ordered: list[_Post], available: dict[str, _Post]) -> list[_Post]:
        thread_ids = {post.id for post in ordered}
        visited: set[str] = set()
        active: set[str] = set()
        sources: list[_Post] = []

        def visit(post: _Post) -> None:
            if post.id in active:
                raise _Failure(FetchFailure.PARTIAL, "reference_cycle")
            if post.id in visited:
                return
            post.parent()
            post.content()
            active.add(post.id)
            for ref in post.references:
                if ref.type == "replied_to" and post.id in thread_ids:
                    continue  # The author's thread parents are validated by _thread.
                target = available.get(ref.id)
                if target is None:
                    raise _Failure(FetchFailure.PARTIAL, "missing_referenced_post")
                visit(target)
            active.remove(post.id)
            visited.add(post.id)
            sources.append(post)

        for post in ordered:
            visit(post)
        return sources
