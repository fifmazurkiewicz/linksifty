"""Immutable, owner-selectable scoring rubric; no transport or provider dependencies."""

from dataclasses import dataclass

from linksifty.domain.models import CriterionName

_DESCRIPTIONS = {
    CriterionName.NOVELTY: "Does the material offer new information or a useful new perspective?",
    CriterionName.EVIDENCE: (
        "Are its claims supported by concrete data, examples and cited evidence?"
    ),
    CriterionName.PRACTICALITY: "Can the reader apply the information to a real task or decision?",
    CriterionName.SOURCE_CREDIBILITY: (
        "Is the author or publisher qualified, transparent and trustworthy?"
    ),
    CriterionName.REPLICABILITY: (
        "Are there enough methods and details to reproduce the actions or results?"
    ),
    CriterionName.INDEPENDENT_CORROBORATION: (
        "Do independent supplied sources corroborate the claims?"
    ),
    CriterionName.ABSENCE_OF_CONFLICT_OF_INTEREST: (
        "Are interests disclosed and promotional incentives unlikely to distort the claims?"
    ),
    CriterionName.CONCRETENESS: (
        "Does the material provide specific details rather than slogans or superlatives?"
    ),
}


@dataclass(frozen=True, slots=True)
class RubricCriterion:
    name: CriterionName
    description: str
    weight: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, CriterionName):
            raise ValueError("Unknown criterion")
        if type(self.weight) is not int or not 1 <= self.weight <= 10:
            raise ValueError("Weights must be integers from 1 to 10")
        if (
            not 1 <= len(self.description) <= 1000
            or not self.description.strip()
            or "\x00" in self.description
        ):
            raise ValueError("Descriptions require 1–1000 readable characters without NUL")
        object.__setattr__(self, "description", self.description.strip())


@dataclass(frozen=True, slots=True)
class AssessmentRubric:
    criteria: tuple[RubricCriterion, ...]

    def __post_init__(self) -> None:
        if len(self.criteria) != len(CriterionName) or {c.name for c in self.criteria} != set(
            CriterionName
        ):
            raise ValueError("Require exactly one entry for each of the eight criteria")
        by_name = {c.name: c for c in self.criteria}
        object.__setattr__(self, "criteria", tuple(by_name[name] for name in CriterionName))


def default_rubric() -> AssessmentRubric:
    return AssessmentRubric(
        tuple(RubricCriterion(n, _DESCRIPTIONS[n], n.weight) for n in CriterionName)
    )
