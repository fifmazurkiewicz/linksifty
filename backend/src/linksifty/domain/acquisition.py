"""Provider-independent outcomes of source acquisition."""

from dataclasses import dataclass
from enum import StrEnum


class FetchFailure(StrEnum):
    UNSAFE_URL = "unsafe_url"
    LOGIN_REQUIRED = "login_required"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    PARTIAL = "partial_content"
    TOO_LARGE = "too_large"


@dataclass(frozen=True, slots=True)
class FetchResult:
    text: str | None = None
    failure: FetchFailure | None = None
