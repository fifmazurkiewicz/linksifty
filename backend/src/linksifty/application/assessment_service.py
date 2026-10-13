"""Provider-independent assessment orchestration."""

from __future__ import annotations

from collections.abc import Callable

from linksifty.domain.models import AssessmentDraft, CompletedAssessment
from linksifty.domain.scoring import complete_assessment


class AssessmentService:
    """Turn a validated provider draft into a deterministic completed assessment."""

    def __init__(self, create_draft: Callable[[str], AssessmentDraft]) -> None:
        self._create_draft = create_draft

    def assess(self, source_text: str, *, threshold: float) -> CompletedAssessment:
        """Assess only supplied complete source text and snapshot the current threshold."""
        return complete_assessment(self._create_draft(source_text), threshold)
