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
    TOO_SHORT = "too_short"
    X_NOT_CONFIGURED = "x_not_configured"
    X_ACCESS_DENIED = "x_access_denied"
    X_NOT_FOUND = "x_not_found"
    X_RATE_LIMITED = "x_rate_limited"
    X_ATTEMPT_UNCERTAIN = "x_attempt_uncertain"


@dataclass(frozen=True, slots=True)
class FetchResult:
    text: str | None = None
    failure: FetchFailure | None = None
