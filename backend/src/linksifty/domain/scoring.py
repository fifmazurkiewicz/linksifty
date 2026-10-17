"""Deterministic, versioned scoring; missing knowledge is not a negative score."""

from __future__ import annotations

from linksifty.domain.models import AssessmentDraft, CompletedAssessment, CriterionName, Verdict
from linksifty.domain.rubric import AssessmentRubric, default_rubric

_CRITICAL = {
    CriterionName.EVIDENCE,
    CriterionName.SOURCE_CREDIBILITY,
    CriterionName.PRACTICALITY,
    CriterionName.CONCRETENESS,
}


def weighted_score(
    draft: AssessmentDraft, *, rubric: AssessmentRubric | None = None
) -> float | None:
    rules = rubric or default_rubric()
    weights = {c.name: c.weight for c in rules.criteria}
    if rules.version == 1 and any(c.status != "assessed" for c in draft.criteria):
        raise ValueError("Legacy assessments require eight scored criteria")
    scored = [c for c in draft.criteria if c.score is not None]
    total_weight = sum(weights[c.name] for c in scored)
    if total_weight == 0:
        return None
    weighted_sum = sum(c.score * weights[c.name] for c in scored if c.score is not None)
    return round(weighted_sum / (total_weight * 5) * 100, 2)


def derive_verdict(
    score: float | None,
    threshold: float,
    *,
    version: int = 2,
    has_hype: bool = False,
    needs_review: bool = False,
) -> Verdict:
    if score is not None and not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")
    if not 40 <= threshold <= 100:
        raise ValueError("threshold must be between 40 and 100")
    if version not in {1, 2}:
        raise ValueError("Unsupported rubric version")
    if version == 2 and has_hype:
        return Verdict.HYPE
    if score is None or needs_review:
        return Verdict.TO_REVIEW
    if score >= threshold:
        return Verdict.VALUABLE
    if version == 1 and score < 40:
        return Verdict.HYPE
    return Verdict.TO_REVIEW


def complete_assessment(
    draft: AssessmentDraft,
    threshold: float,
    *,
    rubric: AssessmentRubric | None = None,
) -> CompletedAssessment:
    rules = rubric or default_rubric()
    score = weighted_score(draft, rubric=rules)
    needs_review = rules.version == 2 and any(
        c.name in _CRITICAL and (c.score is None or c.score <= 2) for c in draft.criteria
    )
    verdict = derive_verdict(
        score,
        threshold,
        version=rules.version,
        has_hype=bool(draft.hype_signals),
        needs_review=needs_review,
    )
    if rules.version == 1:
        reason = "Historical verdict calculated using the original score thresholds."
    elif verdict is Verdict.HYPE:
        reason = (
            "Specific source passages show exaggerated promises or conclusions beyond the evidence."
        )
    elif score is None:
        reason = "No criteria could be scored; review the missing verification."
    elif needs_review:
        reason = "Key evidence, credibility, usefulness or completeness is unverified or weak."
    elif verdict is Verdict.VALUABLE:
        reason = (
            "The scored criteria meet the threshold "
            "and the key criteria are sufficiently supported."
        )
    else:
        reason = (
            "The score is below the valuable threshold; a low score alone does not establish hype."
        )
    return CompletedAssessment(
        note=draft.note,
        criteria=draft.criteria,
        score=score,
        verdict=verdict,
        threshold_snapshot=threshold,
        hype_signals=draft.hype_signals,
        verdict_reason=reason,
    )
