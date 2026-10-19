"""Provider-independent outcomes of source acquisition."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

MAX_SOURCE_IMAGES = 12
MediaType = Literal["image", "video", "gif", "audio", "attachment"]


def media_type(value: str) -> MediaType:
    kinds: dict[str, MediaType] = {
        "photo": "image",
        "image": "image",
        "video": "video",
        "animated_gif": "gif",
        "gif": "gif",
        "audio": "audio",
    }
    return kinds.get(value.lower(), "attachment")


class FetchFailure(StrEnum):
    UNSAFE_URL = "unsafe_url"
    LOGIN_REQUIRED = "login_required"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    PARTIAL = "partial_content"
    TOO_LARGE = "too_large"
    TOO_SHORT = "too_short"
    X_NOT_CONFIGURED = "x_not_configured"
    X_ACCESS_DENIED = "x_access_denied"
    X_NOT_FOUND = "x_not_found"
    X_RATE_LIMITED = "x_rate_limited"
    X_ATTEMPT_UNCERTAIN = "x_attempt_uncertain"
    X_ARTICLE_INCOMPLETE = "x_article_incomplete"
    X_MEDIA_UNSUPPORTED = "x_media_unsupported"
    X_MEDIA_UNAVAILABLE = "x_media_unavailable"
    IMAGE_READING_FAILED = "image_reading_failed"
    IMAGE_READING_UNCERTAIN = "image_reading_uncertain"
    IMAGE_READING_NOT_CONFIGURED = "image_reading_not_configured"


@dataclass(frozen=True, slots=True)
class SourceImage:
    url: str
    source_url: str
    mime_type: str
    data: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class FetchResult:
    text: str | None = None
    failure: FetchFailure | None = None
    images: tuple[SourceImage, ...] = ()
    readable_text: str | None = None
    omitted_media: tuple[MediaType, ...] = ()
