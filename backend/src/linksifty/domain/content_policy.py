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


_FETCH_MARKERS: tuple[tuple[IncompleteReason, tuple[str, ...]], ...] = (
    (IncompleteReason.LOGIN_REQUIRED, ("log in", "sign in", "login required")),
    (IncompleteReason.PAYWALLED, ("subscribe to continue", "paywall", "subscription required")),
    (IncompleteReason.SCRIPT_ONLY, ("enable javascript", "javascript is required")),
    (IncompleteReason.BLOCKED, ("access denied", "request blocked", "forbidden")),
)
_MINIMUM_CHARACTERS = 200


def evaluate_content(text: str, *, fetched: bool) -> ContentEvaluation:
    """Return readiness without permitting an assessment of incomplete fetched text."""
    normalized = " ".join(text.split())
    if fetched:
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
