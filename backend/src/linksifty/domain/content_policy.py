"""Rules that prevent assessment from incomplete source material."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ContentReadiness(StrEnum):
    """Whether acquired or pasted text can enter assessment."""

    READY = "ready"
    AWAITING_MANUAL_CONTENT = "awaiting_manual_content"


class IncompleteReason(StrEnum):
    """User-visible explanation for an unavailable fetched source."""

    BLOCKED = "blocked"
    PAYWALLED = "paywalled"
    LOGIN_REQUIRED = "login_required"
    SCRIPT_ONLY = "script_only"
    UNSUPPORTED = "unsupported"
    TOO_SHORT = "too_short"


@dataclass(frozen=True, slots=True)
class ContentEvaluation:
    """Result of a pure content-completeness decision."""

    readiness: ContentReadiness
    reason: IncompleteReason | None = None


_LOGIN_PHRASES = (
    "please sign in",
    "please log in",
    "sign in to continue",
    "log in to continue",
    "login required",
)
_FETCH_MARKERS: tuple[tuple[IncompleteReason, tuple[str, ...]], ...] = (
    (IncompleteReason.PAYWALLED, ("subscribe to continue", "paywall", "subscription required")),
    (IncompleteReason.SCRIPT_ONLY, ("enable javascript", "javascript is required")),
    (IncompleteReason.BLOCKED, ("access denied", "request blocked", "forbidden")),
)
_MINIMUM_CHARACTERS = 200


def is_login_wall(text: str) -> bool:
    """A bare "Sign in" is page chrome; only explicit prompts or tiny pages are walls."""
    lower_text = " ".join(text.split()).lower()
    if any(phrase in lower_text for phrase in _LOGIN_PHRASES):
        return True
    short = len(lower_text) < _MINIMUM_CHARACTERS
    return short and ("sign in" in lower_text or "log in" in lower_text)


def evaluate_content(text: str, *, fetched: bool) -> ContentEvaluation:
    """Return readiness without permitting an assessment of incomplete fetched text."""
    normalized = " ".join(text.split())
    if fetched:
        if is_login_wall(normalized):
            return ContentEvaluation(
                ContentReadiness.AWAITING_MANUAL_CONTENT, IncompleteReason.LOGIN_REQUIRED
            )
        lower_text = normalized.lower()
        for reason, markers in _FETCH_MARKERS:
            if any(marker in lower_text for marker in markers):
                return ContentEvaluation(ContentReadiness.AWAITING_MANUAL_CONTENT, reason)
    if len(normalized) < _MINIMUM_CHARACTERS:
        return ContentEvaluation(
            ContentReadiness.AWAITING_MANUAL_CONTENT,
            IncompleteReason.TOO_SHORT,
        )
    return ContentEvaluation(ContentReadiness.READY)
