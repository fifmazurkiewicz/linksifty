"""Bounded official X post/thread reads. Never scrape or retry a rejected read."""

import asyncio
import json
import logging
import re
from typing import Annotated
from uuid import uuid4

import httpx
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

from linksifty.application.discussions import DiscussionReply, DiscussionResult
from linksifty.domain.acquisition import FetchFailure, FetchResult
from linksifty.domain.content_policy import ContentReadiness, evaluate_content
from linksifty.domain.x_urls import x_post_id
from linksifty.infrastructure.redaction import redact
from linksifty.infrastructure.x_content import XContentFailure as _Failure
from linksifty.infrastructure.x_content import XMedia, parse_article
from linksifty.infrastructure.x_images import fetch_images, validate_media

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
            if self.attachments.get("poll_ids") or set(self.attachments) - {
                "media_keys",
                "poll_ids",
                "media_source_tweet_id",
            }:
                raise _Failure(FetchFailure.X_MEDIA_UNSUPPORTED, "unsupported_attachment")
            keys = self.attachments.get("media_keys")
            if (
                not isinstance(keys, list)
                or not keys
                or any(not isinstance(key, str) for key in keys)
            ):
                raise _Failure(FetchFailure.X_MEDIA_UNAVAILABLE, "missing_media_keys")
        if self.withheld:
            raise _Failure(FetchFailure.PARTIAL, "withheld_content")
        if self.article is not None:
            return parse_article(self.article).text
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

    def context_references(self) -> list[_Reference]:
        embedded = parse_article(self.article).post_ids if self.article is not None else ()
        return [
            *self.references,
            *(_Reference(id=identifier, type="embedded") for identifier in embedded),
        ]

    def media(self, available: dict[str, XMedia]) -> list[XMedia]:
        result: list[XMedia] = []
        keys = (self.attachments or {}).get("media_keys", [])
        if not isinstance(keys, list):
            raise _Failure(FetchFailure.X_MEDIA_UNAVAILABLE, "missing_media_keys")
        for key in keys:
            if not isinstance(key, str) or key not in available:
                raise _Failure(FetchFailure.X_MEDIA_UNAVAILABLE, "missing_expanded_media")
            result.append(available[key])
        if self.article is not None:
            for media in parse_article(self.article).media:
                resolved = available.get(media.media_key, media)
                if media.url and resolved.url != media.url:
                    raise _Failure(FetchFailure.X_MEDIA_UNAVAILABLE, "conflicting_media_versions")
                result.append(resolved)
        missing = False
        for media in result:
            if media.type != "photo":
                raise _Failure(FetchFailure.X_MEDIA_UNSUPPORTED, "non_static_image")
            if not media.url and media.media_key:
                missing = True
            else:
                validate_media(media)
        if missing:
            raise _Failure(FetchFailure.X_MEDIA_UNAVAILABLE, "missing_article_media_expansion")
        return result


class _Includes(BaseModel):
    media: list[XMedia] = Field(default_factory=list, max_length=100)
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


class XAdapter:
    def __init__(
        self,
        token: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        debug: bool = False,
        secrets: tuple[str, ...] = (),
    ) -> None:
        self._token = token
        self._transport = transport
        self._debug = debug
        self._secrets = tuple(value for value in (token, *secrets) if value)

    def _log_debug(self, event: str, request_id: str, details: dict[str, object]) -> None:
        if not self._debug:
            return
        # Redact before truncating/chunking so secrets cannot straddle a boundary.
        payload = json.dumps(redact(details, self._secrets), ensure_ascii=True)
        truncated = len(payload) > 32000
        payload = payload[:32000] + (" [TRUNCATED at 32000 characters]" if truncated else "")
        chunks = [payload[start : start + 4000] for start in range(0, len(payload), 4000)]
        for part, chunk in enumerate(chunks, 1):
            # Warning level deliberately works with the existing Render stderr configuration.
            _logger.warning(
                "x_api_debug event=%s request_id=%s part=%s/%s truncated=%s payload=%s",
                event,
                request_id,
                part,
                len(chunks),
                str(truncated).lower(),
                chunk,
            )

    def _log_response(self, request_id: str, response: httpx.Response, body: bytearray) -> None:
        if not self._debug:
            return
        try:
            payload: object = json.loads(body)
        except (ValueError, RecursionError):
            payload = body.decode("utf-8", errors="replace")
        try:
            self._log_debug(
                "response",
                request_id,
                {"status": response.status_code, "body": payload},
            )
        except RecursionError:
            self._log_debug(
                "response",
                request_id,
                {"status": response.status_code, "body": "[OMITTED: nesting limit]"},
            )

    async def comments(self, url: str) -> DiscussionResult:
        """One explicit, bounded reply sample; failure never repeats a paid read."""
        identifier = x_post_id(url)
        if identifier is None:
            return DiscussionResult(status="unavailable")
        params = {
            "tweet.fields": "author_id,conversation_id,note_tweet,referenced_tweets,attachments",
            "expansions": "author_id",
            "user.fields": "username",
        }
        try:
            async with asyncio.timeout(30):
                async with httpx.AsyncClient(
                    transport=self._transport, trust_env=False, follow_redirects=False, timeout=10
                ) as client:
                    lookup = _Lookup.model_validate(await self._get(client, identifier, **params))
                    if lookup.data.id != identifier:
                        raise _Failure(FetchFailure.PARTIAL, "lookup_id_mismatch")
                    conversation = lookup.data.conversation_id
                    payload = await self._get(
                        client,
                        "search/all",
                        **params,
                        query=f"conversation_id:{conversation} is:reply",
                        max_results="20",
                        start_time="2006-03-21T00:00:00Z",
                        sort_order="recency",
                    )
            page = _Search.model_validate(payload)
            if page.meta.result_count != len(page.data) or len(page.data) > 20:
                raise _Failure(FetchFailure.PARTIAL, "comment_count_mismatch")
            users: dict[str, str] = {}
            includes = payload.get("includes")
            if isinstance(includes, dict) and isinstance(includes.get("users"), list):
                for user in includes["users"]:
                    if (
                        isinstance(user, dict)
                        and isinstance(user.get("id"), str)
                        and isinstance(user.get("username"), str)
                        and re.fullmatch(r"[A-Za-z0-9_]{1,15}", user["username"])
                    ):
                        users[user["id"]] = user["username"]
            replies: list[DiscussionReply] = []
            seen: set[str] = set()
            for post in page.data:
                if post.conversation_id != conversation:
                    raise _Failure(FetchFailure.PARTIAL, "comment_conversation_mismatch")
                if post.withheld or post.id in seen or post.parent() is None:
                    continue
                seen.add(post.id)
                text = post.note.text if post.note is not None else post.text
                if not text.strip() or "\x00" in text:
                    continue
                replies.append(
                    DiscussionReply(
                        id=post.id,
                        author_id=post.author_id,
                        username=users.get(post.author_id),
                        text=text[:4000],
                        truncated=len(text) > 4000 or bool(_TRUNCATED.search(text)),
                        has_media=bool(post.attachments),
                    )
                )
            return DiscussionResult(status="ready", replies=replies)
        except (_Failure, ValidationError, ValueError, httpx.HTTPError, TimeoutError):
            _logger.warning("x_comments_unavailable; no automatic retry")
            return DiscussionResult(status="unavailable")

    async def fetch(self, url: str) -> FetchResult:
        identifier = x_post_id(url)
        if identifier is None:
            return FetchResult(failure=FetchFailure.UNSAFE_URL)
        request_count = 0

        async def count_request(request: httpx.Request) -> None:
            nonlocal request_count
            if request_count >= 12:
                raise _Failure(FetchFailure.PARTIAL, "request_limit")
            request_count += 1

        try:
            async with asyncio.timeout(60):
                async with httpx.AsyncClient(
                    transport=self._transport,
                    trust_env=False,
                    follow_redirects=False,
                    timeout=10,
                    event_hooks={"request": [count_request]},
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
        request_id = uuid4().hex if self._debug else ""
        url = f"https://api.x.com/2/tweets/{path}"
        parameters = {
            "tweet.fields": _FIELDS,
            "expansions": (
                "referenced_tweets.id,attachments.media_keys,"
                "referenced_tweets.id.attachments.media_keys,"
                "article.cover_media,article.media_entities"
            ),
            "media.fields": "media_key,type,url,width,height,alt_text",
            **params,
        }
        self._log_debug("request", request_id, {"method": "GET", "url": url, "params": parameters})
        try:
            async with client.stream(
                "GET",
                url,
                params=parameters,
                headers={"Authorization": f"Bearer {self._token}", "Accept": "application/json"},
            ) as response:
                if response.status_code != 200:
                    # Default logs retain fixed labels only; details require explicit debug opt-in.
                    _logger.warning(
                        "x_api_request_failed endpoint=%s status=%s",
                        "full_archive_search" if path == "search/all" else "post_lookup",
                        response.status_code,
                    )
                is_json = (
                    response.headers.get("content-type", "").split(";", 1)[0] == "application/json"
                )
                body = bytearray()
                if self._debug or (response.status_code == 200 and is_json):
                    try:
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk[: _MAX_BODY_BYTES + 1 - len(body)])
                            if len(body) > _MAX_BODY_BYTES:
                                break
                    except httpx.HTTPError as error:
                        if response.status_code == 200:
                            self._log_response(request_id, response, body)
                            raise
                        self._log_debug(
                            "transport_error", request_id, {"error_type": type(error).__name__}
                        )
                self._log_response(request_id, response, body)
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
                if not is_json:
                    raise _Failure(FetchFailure.PARTIAL, "unexpected_content_type")
                if len(body) > _MAX_BODY_BYTES:
                    raise _Failure(FetchFailure.TOO_LARGE, "response_size_limit")
                payload: object = json.loads(body)
                if not isinstance(payload, dict):
                    raise _Failure(FetchFailure.PARTIAL, "invalid_response_shape")
                if payload.get("errors"):
                    raise _Failure(FetchFailure.PARTIAL, "provider_partial_errors")
                return payload
        except (httpx.HTTPError, TimeoutError) as error:
            self._log_debug("transport_error", request_id, {"error_type": type(error).__name__})
            raise

    async def _lookup(
        self,
        client: httpx.AsyncClient,
        identifier: str,
        available: dict[str, _Post],
        media: dict[str, XMedia],
    ) -> _Post:
        payload = await self._get(client, identifier)
        try:
            lookup = _Lookup.model_validate(payload)
        except ValidationError as error:
            raise _Failure(FetchFailure.PARTIAL, "invalid_post_payload") from error
        if lookup.data.id != identifier:
            raise _Failure(FetchFailure.PARTIAL, "lookup_id_mismatch")
        self._remember(available, [lookup.data, *lookup.includes.posts])
        self._remember_media(media, lookup.includes.media)
        return lookup.data

    async def _thread(self, client: httpx.AsyncClient, identifier: str) -> FetchResult:
        submitted_id = identifier
        available: dict[str, _Post] = {}
        media: dict[str, XMedia] = {}
        selected = await self._lookup(client, identifier, available, media)
        looked_up = {identifier}
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
            else await self._lookup(client, selected.conversation_id, available, media)
        )
        if root is not selected:
            looked_up.add(root.id)
        if (
            root.conversation_id != root.id
            or root.author_id != selected.author_id
            or root.parent() is not None
        ):
            raise _Failure(FetchFailure.PARTIAL, "invalid_conversation_root")
        posts = {root.id: root}
        # Validate before requesting more potentially billed resources.
        await self._resolve_sources(client, [root, selected], available, media, looked_up)
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
            self._remember_media(media, page.includes.media)
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
        excluded: set[str] = set()
        while remaining:
            count = len(remaining)
            for post in sorted(remaining.values(), key=lambda post: int(post.id)):
                parent_id = post.parent()
                parent = available.get(parent_id or "")
                if parent_id in visited:
                    ordered.append(post)
                    visited.add(post.id)
                elif parent_id in excluded or (
                    parent is not None
                    and parent.author_id != root.author_id
                    and parent.conversation_id == root.id
                ):
                    # Search also returns the author's conversations with commenters.
                    excluded.add(post.id)
                else:
                    continue
                del remaining[post.id]
            if len(remaining) == count:
                raise _Failure(FetchFailure.PARTIAL, "disconnected_thread")
        if identifier not in visited:
            raise _Failure(FetchFailure.PARTIAL, "selected_post_outside_thread")
        sources = await self._resolve_sources(client, ordered, available, media, looked_up)
        # Labels, URLs and RT previews must not make short sources pass the minimum.
        readable_text = "\n\n".join(post.content() for post in sources)
        required_media = [
            (item, f"https://x.com/i/web/status/{post.id}")
            for post in sources
            for item in post.media(media)
        ]
        if (
            not required_media
            and evaluate_content(readable_text, fetched=False).readiness
            is not ContentReadiness.READY
        ):
            raise _Failure(FetchFailure.TOO_SHORT, "minimum_text_length")
        text = "\n\n".join(
            f"https://x.com/i/web/status/{post.id}\nauthor_id={post.author_id}\n{post.content()}"
            + "".join(
                f"\n{ref.type}: https://x.com/i/web/status/{ref.id}"
                for ref in post.context_references()
            )
            for post in sources
        )
        if reposts:
            text = f"Submitted repost: https://x.com/i/web/status/{submitted_id}\n\n{text}"
        if len(text.encode("utf-8")) > _MAX_TEXT_BYTES:
            raise _Failure(FetchFailure.TOO_LARGE, "text_size_limit")
        async with httpx.AsyncClient(transport=self._transport, trust_env=False) as media_client:
            images = await fetch_images(media_client, required_media)
        return FetchResult(text=text, images=images, readable_text=readable_text)

    async def _resolve_sources(
        self,
        client: httpx.AsyncClient,
        ordered: list[_Post],
        available: dict[str, _Post],
        media: dict[str, XMedia],
        looked_up: set[str],
    ) -> list[_Post]:
        while True:
            sources = self._source_posts(ordered, available)
            target = None
            for source in sources:
                try:
                    source.media(media)
                except _Failure as failure:
                    if failure.check != "missing_article_media_expansion" or source.id in looked_up:
                        raise
                    target = target or source
            if target is None:
                return sources
            # Complete a quoted Article's expansions once; never repeat an already-read post.
            looked_up.add(target.id)
            await self._lookup(client, target.id, available, media)

    @staticmethod
    def _remember_media(available: dict[str, XMedia], media: list[XMedia]) -> None:
        for item in media:
            key = item.media_key or item.url
            if not key or (key in available and available[key] != item):
                raise _Failure(FetchFailure.X_MEDIA_UNAVAILABLE, "conflicting_media_versions")
            available[key] = item
            if len(available) > 100:
                raise _Failure(FetchFailure.TOO_LARGE, "expanded_media_limit")

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
            for ref in post.context_references():
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
