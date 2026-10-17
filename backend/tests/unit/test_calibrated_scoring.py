from dataclasses import replace

import pytest

from linksifty.domain.models import AssessmentDraft, Criterion, CriterionName, Verdict
from linksifty.domain.rubric import default_rubric
from linksifty.domain.scoring import complete_assessment


def draft(points: int = 5) -> AssessmentDraft:
    return AssessmentDraft(
        "Informative explanation",
        tuple(
            Criterion(n, points, "Specific supporting details.", ("passage",))
            for n in CriterionName
        ),
    )


def test_informative_explainer_is_valuable_without_replicability() -> None:
    original = draft()
    criteria = tuple(
        replace(c, score=None, status="not_applicable")
        if c.name is CriterionName.REPLICABILITY
        else c
        for c in original.criteria
    )
    result = complete_assessment(replace(original, criteria=criteria), 60)
    assert result.score == 100
    assert result.verdict is Verdict.VALUABLE


def test_low_score_without_hype_evidence_is_to_review() -> None:
    assert complete_assessment(draft(1), 60).verdict is Verdict.TO_REVIEW


def test_legacy_low_score_keeps_hype() -> None:
    assert (
        complete_assessment(draft(1), 60, rubric=default_rubric(version=1)).verdict is Verdict.HYPE
    )


def test_unknown_critical_evidence_cannot_become_valuable() -> None:
    original = draft()
    criteria = tuple(
        replace(c, score=None, status="not_verified") if c.name is CriterionName.EVIDENCE else c
        for c in original.criteria
    )
    result = complete_assessment(replace(original, criteria=criteria), 60)
    assert result.verdict is Verdict.TO_REVIEW
    assert result.score == 100


def test_all_unknown_has_no_percentage() -> None:
    original = draft()
    criteria = tuple(replace(c, score=None, status="not_verified") for c in original.criteria)
    result = complete_assessment(replace(original, criteria=criteria), 60)
    assert result.score is None
    assert result.verdict is Verdict.TO_REVIEW


def test_missing_corroboration_alone_does_not_penalize_useful_source() -> None:
    original = draft()
    criteria = tuple(
        replace(c, score=None, status="not_verified")
        if c.name is CriterionName.INDEPENDENT_CORROBORATION
        else c
        for c in original.criteria
    )
    assert complete_assessment(replace(original, criteria=criteria), 60).verdict is Verdict.VALUABLE


def test_hype_requires_explicit_cited_signal() -> None:
    from linksifty.domain.models import HypeSignal

    signal = HypeSignal("Promises guaranteed results unsupported by the text.", ("passage",))
    assert complete_assessment(replace(draft(), hype_signals=(signal,)), 60).verdict is Verdict.HYPE
    with pytest.raises(ValueError):
        HypeSignal("Uncited allegation", ())


@pytest.mark.parametrize(
    "name,score,status",
    [
        (CriterionName.EVIDENCE, None, "assessed"),
        (CriterionName.REPLICABILITY, 1, "not_applicable"),
        (CriterionName.EVIDENCE, None, "not_applicable"),
        (CriterionName.EVIDENCE, 3, "not_verified"),
    ],
)
def test_status_and_points_must_agree(name: CriterionName, score: int | None, status: str) -> None:
    with pytest.raises(ValueError):
        Criterion(name, score, "Reason", ("passage",), status=status)


def test_low_total_without_weak_key_criteria_still_does_not_imply_hype() -> None:
    from linksifty.domain.rubric import AssessmentRubric

    original = draft(1)
    critical = {
        CriterionName.EVIDENCE,
        CriterionName.SOURCE_CREDIBILITY,
        CriterionName.PRACTICALITY,
        CriterionName.CONCRETENESS,
    }
    criteria = tuple(replace(c, score=3) if c.name in critical else c for c in original.criteria)
    rules = AssessmentRubric(
        tuple(
            replace(c, weight=2) if c.name is CriterionName.NOVELTY else c
            for c in default_rubric().criteria
        )
    )
    result = complete_assessment(replace(original, criteria=criteria), 60, rubric=rules)
    assert result.score == 38.46
    assert result.verdict is Verdict.TO_REVIEW
