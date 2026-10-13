from linksifty.application.assessment_service import AssessmentService
from linksifty.domain.models import AssessmentDraft, Criterion, CriterionName


def test_assessment_service_uses_deterministic_threshold() -> None:
    draft = AssessmentDraft(
        note="Useful evidence.",
        criteria=tuple(
            Criterion(name, 4, "Supported by source.", ("citation-1",)) for name in CriterionName
        ),
    )
    result = AssessmentService(lambda _: draft).assess("source text", threshold=70)

    assert result.score == 80
    assert result.threshold_snapshot == 70
    assert result.verdict.value == "valuable"
