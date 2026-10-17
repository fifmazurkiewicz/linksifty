"""Immutable, owner-selectable scoring rubric; no transport or provider dependencies."""

from dataclasses import dataclass

from linksifty.domain.models import CriterionName

_LEGACY_DESCRIPTIONS = {
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


_DESCRIPTIONS = {
    CriterionName.NOVELTY: (
        "Learning value: does the material build useful understanding within its purpose? "
        "1: little substantive explanation; 3: some useful knowledge with gaps; "
        "5: clear, substantial learning even about established facts. Do not assume the reader's "
        "prior knowledge or require global novelty; state that personalization is unavailable."
    ),
    CriterionName.EVIDENCE: (
        "Support for claims: do the key claims have relevant, traceable legislation, data, "
        "documents or examples? 1: identifiable unsupported or contradicted key claims; "
        "3: partial support with named gaps; 5: strong support for the central claims. "
        "Check dates and scope for time-sensitive claims. Numbers alone are not evidence. "
        "Use not_verified when the supplied material cannot establish support."
    ),
    CriterionName.PRACTICALITY: (
        "Usefulness: can the reader use this to understand a topic, make a decision or act? "
        "1: little usable information; 3: useful but missing important decision details; "
        "5: clearly supports its intended task or decision. An explainer need not provide "
        "a click-by-click tutorial or investment strategy."
    ),
    CriterionName.SOURCE_CREDIBILITY: (
        "Topic-specific credibility: is the identified author or institution competent and "
        "accountable in this topic? 1: concrete credibility problems; 3: relevant but limited "
        "authority; 5: a competent, accountable primary authority in its remit. Official "
        "guidance can merit 5; a government URL is not an automatic guarantee of correctness "
        "or currency. Use not_verified when identity or competence cannot be established."
    ),
    CriterionName.REPLICABILITY: (
        "Replicability: only for a claimed experiment, method or reproducible result. "
        "1: crucial steps missing; 3: enough for partial reproduction with named gaps; "
        "5: sufficient methods, inputs and conditions to reproduce it. Use not_applicable "
        "for informational explainers that do not claim such a method or result."
    ),
    CriterionName.INDEPENDENT_CORROBORATION: (
        "Cross-source confirmation: compare specific central claims with supplied independent "
        "sources. 1: concrete contradiction; 3: limited or mixed confirmation; "
        "5: central claims clearly corroborated. Identify the matching claim and sources. "
        "Different levels of detail are not a contradiction. Use not_verified if no independent "
        "comparison can be established; the presence of another page alone is insufficient."
    ),
    CriterionName.ABSENCE_OF_CONFLICT_OF_INTEREST: (
        "Fair presentation and interests: does the source disclose relevant interests and "
        "present claims without sales-driven distortion? 1: concrete hidden interests or "
        "material distortion; 3: identifiable incentives with limitations; 5: fair presentation "
        "with adequately understood interests and no material distortion observed. Missing a "
        "disclosure is not proof of conflict. Use not_verified when context is insufficient."
    ),
    CriterionName.CONCRETENESS: (
        "Specificity and completeness for the stated purpose: does the material give relevant "
        "details, conditions and limitations? 1: slogans or critical omissions; "
        "3: useful specifics but named gaps; 5: concrete details sufficient for its purpose. "
        "Consider currency where it matters; do not demand an entire investing guide from "
        "an explanation of account rules."
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
    version: int = 2

    def __post_init__(self) -> None:
        if type(self.version) is not int or self.version not in {1, 2}:
            raise ValueError("Unsupported rubric version")
        if len(self.criteria) != len(CriterionName) or {c.name for c in self.criteria} != set(
            CriterionName
        ):
            raise ValueError("Require exactly one entry for each of the eight criteria")
        by_name = {c.name: c for c in self.criteria}
        object.__setattr__(self, "criteria", tuple(by_name[name] for name in CriterionName))


def default_rubric(*, version: int = 2) -> AssessmentRubric:
    return AssessmentRubric(
        tuple(
            RubricCriterion(
                n, (_LEGACY_DESCRIPTIONS if version == 1 else _DESCRIPTIONS)[n], n.weight
            )
            for n in CriterionName
        ),
        version=version,
    )
