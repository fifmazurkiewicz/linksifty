"""Deterministic score and verdict calculations."""

from __future__ import annotations

from linksifty.domain.models import AssessmentDraft, CompletedAssessment, Verdict
from linksifty.domain.rubric import AssessmentRubric, default_rubric

_HYPE_LIMIT = 40.0


def weighted_score(draft: AssessmentDraft, *, rubric: AssessmentRubric | None = None) -> float:
    """Convert weighted 1–5 criterion scores to a percentage."""
    weights = {c.name: c.weight for c in (rubric or default_rubric()).criteria}
    weighted_sum = sum(criterion.score * weights[criterion.name] for criterion in draft.criteria)
    total_weight = sum(weights.values())
    return round(weighted_sum / (total_weight * 5) * 100, 2)


def derive_verdict(score: float, threshold: float) -> Verdict:
    """Map a valid percentage and future-only valuable threshold to one verdict."""
    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")
    if not _HYPE_LIMIT <= threshold <= 100:
        raise ValueError("threshold must be between 40 and 100")
    if score >= threshold:
        return Verdict.VALUABLE
    if score < _HYPE_LIMIT:
        return Verdict.HYPE
    return Verdict.TO_REVIEW


def complete_assessment(
    draft: AssessmentDraft, threshold: float, *, rubric: AssessmentRubric | None = None
) -> CompletedAssessment:
    """Create an immutable result whose verdict cannot change with later settings."""
    score = weighted_score(draft, rubric=rubric)
    return CompletedAssessment(
        note=draft.note,
        criteria=draft.criteria,
        score=score,
        verdict=derive_verdict(score, threshold),
        threshold_snapshot=threshold,
    )
