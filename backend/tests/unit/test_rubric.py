from dataclasses import replace

import pytest

from linksifty.domain.models import AssessmentDraft, Criterion, CriterionName
from linksifty.domain.rubric import AssessmentRubric, RubricCriterion, default_rubric
from linksifty.domain.scoring import complete_assessment


def test_custom_weights_change_score_without_changing_historical_result() -> None:
    draft = AssessmentDraft(
        "Note",
        tuple(
            Criterion(n, 5 if n is CriterionName.NOVELTY else 1, "Evidence", ("citation",))
            for n in CriterionName
        ),
    )
    original = complete_assessment(draft, 60)
    custom = AssessmentRubric(
        tuple(
            replace(c, weight=10) if c.name is CriterionName.NOVELTY else c
            for c in default_rubric().criteria
        )
    )
    assert complete_assessment(draft, 60, rubric=custom).score == 58.10
    assert original.score == 26.67


@pytest.mark.parametrize("weight", [0, 11, 1.5, True, "2"])
def test_invalid_weights_fail(weight: object) -> None:
    with pytest.raises(ValueError):
        RubricCriterion(CriterionName.NOVELTY, "Description", weight)  # type: ignore[arg-type]


@pytest.mark.parametrize("description", ["", " \n\t", "a" * 1001, "a\x00b"])
def test_invalid_descriptions_fail(description: str) -> None:
    with pytest.raises(ValueError):
        RubricCriterion(CriterionName.NOVELTY, description, 1)


def test_exactly_eight_unique_criteria_are_required() -> None:
    rules = default_rubric().criteria
    with pytest.raises(ValueError):
        AssessmentRubric(rules[:-1])
    with pytest.raises(ValueError):
        AssessmentRubric((*rules[:-1], rules[0]))
    assert [c.name for c in default_rubric().criteria] == list(CriterionName)


def test_migration_defaults_match_the_domain_catalog() -> None:
    import json
    from pathlib import Path

    from linksifty.application.processing_contracts import RubricConfig

    migration = Path("supabase/migrations/20261016_000009_assessment_rubric.sql").read_text()
    literal = migration.split("select '", 1)[1].split("'::jsonb;", 1)[0].replace("''", "'")
    assert json.loads(literal) == RubricConfig.default(version=1).model_dump(
        mode="json", exclude={"version"}
    )


def test_calibrated_migration_defaults_match_domain() -> None:
    import json
    from pathlib import Path

    from linksifty.application.processing_contracts import RubricConfig

    migration = Path("supabase/migrations/20261017_000010_assessment_calibration.sql").read_text()
    new_function = migration.split(
        "create or replace function public.default_assessment_rubric()", 1
    )[1]
    literal = new_function.split("select '", 1)[1].split("'::jsonb;", 1)[0].replace("''", "'")
    assert json.loads(literal) == RubricConfig.default().model_dump(mode="json")
