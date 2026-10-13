from linksifty.domain.models import AssessmentDraft, Criterion, CriterionName, Verdict
from linksifty.domain.scoring import complete_assessment, derive_verdict


def _criterion(name: CriterionName, score: int) -> Criterion:
    return Criterion(
        name=name,
        score=score,
        rationale="Evidence supports this.",
        citation_ids=("cite-1",),
    )


def _draft(score: int) -> AssessmentDraft:
    return AssessmentDraft(
        note="A concise note.",
        criteria=tuple(_criterion(name, score) for name in CriterionName),
    )


def test_threshold_snapshot_is_used_for_historic_verdict() -> None:
    assessment = complete_assessment(_draft(4), threshold=60)

    assert assessment.score == 80
    assert assessment.verdict is Verdict.VALUABLE
    assert assessment.threshold_snapshot == 60


def test_low_score_is_hype() -> None:
    assert derive_verdict(score=39.99, threshold=60) is Verdict.HYPE


def test_score_between_hype_and_valuable_threshold_is_to_review() -> None:
    assert derive_verdict(score=60, threshold=70) is Verdict.TO_REVIEW


def test_score_equal_to_threshold_is_valuable() -> None:
    assert derive_verdict(score=60, threshold=60) is Verdict.VALUABLE
