"""Strict rich X content parsing; previews never stand in for Article bodies."""

import re
from dataclasses import dataclass

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

from linksifty.domain.acquisition import FetchFailure


class XContentFailure(Exception):
    def __init__(self, reason: FetchFailure, check: str) -> None:
        self.reason = reason
        self.check = check


class XMedia(BaseModel):
    model_config = ConfigDict(strict=True)
    media_key: str = Field(
        default="", validation_alias=AliasChoices("media_key", "id", "media_id"), max_length=2000
    )
    type: str = "photo"
    url: str | None = Field(default=None, max_length=2000)


@dataclass(frozen=True, slots=True)
class ArticleContent:
    text: str
    media: tuple[XMedia, ...]
    post_ids: tuple[str, ...]


def _invalid(check: str) -> XContentFailure:
    return XContentFailure(FetchFailure.X_ARTICLE_INCOMPLETE, check)


def _post_id(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{1,19}", value) is None:
        raise _invalid("article_post_id_invalid")
    return value


def parse_article(article: dict[str, object]) -> ArticleContent:
    """Accept full text or complete DraftJS blocks; validate embedded dependencies."""
    title = article.get("title")
    body = article.get("text", article.get("plain_text"))
    media: list[XMedia] = []
    posts: list[str] = []
    links: list[str] = []
    code_blocks: list[tuple[str, str]] = []

    def add_media(value: object) -> None:
        if isinstance(value, str):
            value = {"media_key": value}
        if not isinstance(value, dict):
            raise _invalid("article_media_invalid")
        try:
            item = XMedia.model_validate(value)
        except ValidationError as error:
            raise _invalid("article_media_invalid") from error
        if not (item.media_key or item.url):
            raise _invalid("article_media_invalid")
        media.append(item)

    def add_entities(value: object) -> None:
        if not isinstance(value, dict) or set(value) - {
            "urls",
            "mentions",
            "hashtags",
            "symbols",
            "media",
            "posts",
            "code",
        }:
            raise _invalid("article_entities_invalid")
        for key in ("media", "posts"):
            values = value.get(key, [])
            if not isinstance(values, list):
                raise _invalid("article_entity_list_invalid")
            for entity in values:
                if key == "media":
                    add_media(entity)
                else:
                    posts.append(_post_id(entity.get("id") if isinstance(entity, dict) else entity))
        snippets = value.get("code", [])
        if not isinstance(snippets, list):
            raise _invalid("article_code_invalid")
        for snippet in snippets:
            if not isinstance(snippet, dict):
                raise _invalid("article_code_invalid")
            code = snippet.get("code")
            language = snippet.get("language", "")
            content = snippet.get("content", code)
            if (
                not isinstance(code, str)
                or not code.strip()
                or "\x00" in code
                or not isinstance(language, str)
                or re.fullmatch(r"[A-Za-z0-9_+.#-]{0,40}", language) is None
                or not isinstance(content, str)
                or "\x00" in content
                or code not in content
            ):
                raise _invalid("article_code_invalid")
            code_blocks.append(
                (
                    code,
                    f"Article code block ({language or 'unspecified language'}; "
                    f"position unspecified):\n{content}",
                )
            )

    if article.get("cover_media") is not None:
        add_media(article["cover_media"])
    media_values = article.get("media_entities", [])
    if not isinstance(media_values, list):
        raise _invalid("article_media_list_invalid")
    for value in media_values:
        add_media(value)
    if "entities" in article:
        add_entities(article["entities"])
    state = article.get("content_state")
    if state is not None:
        if not isinstance(state, dict) or not isinstance(state.get("blocks"), list):
            raise _invalid("article_content_state_invalid")
        entities = state.get("entity_map", state.get("entityMap", {}))
        entity_map: dict[str, object] = {}
        if isinstance(entities, dict):
            entity_map = {str(key): value for key, value in entities.items()}
        elif isinstance(entities, list):
            for entity in entities:
                if not isinstance(entity, dict) or "key" not in entity:
                    raise _invalid("article_entity_map_invalid")
                key = str(entity["key"])
                if key in entity_map:
                    raise _invalid("article_entity_map_invalid")
                entity_map[key] = entity.get("value", entity)
        else:
            raise _invalid("article_entity_map_invalid")
        parts: list[str] = []
        for block in state["blocks"]:
            if not isinstance(block, dict) or not isinstance(block.get("text"), str):
                raise _invalid("article_block_invalid")
            kind = block.get("type")
            if kind not in {
                "unstyled",
                "header-one",
                "header-two",
                "header-three",
                "blockquote",
                "unordered-list-item",
                "ordered-list-item",
                "code-block",
                "atomic",
            }:
                raise _invalid("article_block_type_unsupported")
            parts.append(block["text"])
            ranges = block.get("entity_ranges", block.get("entityRanges", []))
            if not isinstance(ranges, list) or (kind == "atomic" and not ranges):
                raise _invalid("article_entity_ranges_invalid")
            for span in ranges:
                entity = entity_map.get(str(span.get("key"))) if isinstance(span, dict) else None
                if not isinstance(entity, dict) or not isinstance(entity.get("data"), dict):
                    raise _invalid("article_entity_invalid")
                data = entity["data"]
                entity_type = entity.get("type")
                if entity_type in {"IMAGE", "MEDIA"}:
                    add_media(data)
                elif entity_type in {"TWEET", "POST"}:
                    posts.append(
                        _post_id(data.get("post_id", data.get("tweet_id", data.get("id"))))
                    )
                elif entity_type == "LINK":
                    url = data.get("url")
                    if not isinstance(url, str):
                        raise _invalid("article_link_invalid")
                    links.append(url)
                elif entity_type == "MARKDOWN" and isinstance(data.get("markdown"), str):
                    # Embedded HTML/images cannot be silently discarded as plain code.
                    markdown = data["markdown"]
                    if "![" in markdown or "<" in markdown:
                        raise _invalid("article_markdown_unsupported")
                    parts.append(markdown)
                elif entity_type != "DIVIDER":
                    raise _invalid("article_entity_type_unsupported")
        block_text = "\n\n".join(parts).strip()
        if body is None:
            body = block_text
        elif not isinstance(body, str) or " ".join(block_text.split()) != " ".join(body.split()):
            raise _invalid("article_body_disagrees_with_blocks")
    if not isinstance(title, str) or not title.strip():
        raise _invalid("article_title_missing")
    if body is None:
        raise _invalid("article_body_missing")
    if not isinstance(body, str) or "\x00" in body:
        raise _invalid("article_body_invalid")
    if not body.strip():
        raise _invalid("article_body_empty")
    if body.rstrip().endswith(("…", "...")):
        raise _invalid("article_body_truncated")
    if body == article.get("preview_text"):
        raise _invalid("article_body_preview")
    # X supplies no insertion offsets for these snippets; never invent their location.
    extra_code = [content for code, content in code_blocks if code not in body]
    return ArticleContent(
        "\n\n".join([title.strip(), body, *extra_code, *links]), tuple(media), tuple(posts)
    )
