"""Typed, framework-free assessment entities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CriterionName(StrEnum):
    """The fixed rubric used for every assessment."""

    NOVELTY = "novelty"
    EVIDENCE = "evidence"
    PRACTICALITY = "practicality"
    SOURCE_CREDIBILITY = "source_credibility"
    REPLICABILITY = "replicability"
    INDEPENDENT_CORROBORATION = "independent_corroboration"
    ABSENCE_OF_CONFLICT_OF_INTEREST = "absence_of_conflict_of_interest"
    CONCRETENESS = "concreteness"

    @property
    def weight(self) -> int:
        """Return this criterion's fixed contribution weight."""
        if self in {
            CriterionName.EVIDENCE,
            CriterionName.SOURCE_CREDIBILITY,
            CriterionName.REPLICABILITY,
            CriterionName.ABSENCE_OF_CONFLICT_OF_INTEREST,
        }:
            return 2
        return 1


class Verdict(StrEnum):
    """User-visible deterministic assessment outcomes."""

    VALUABLE = "valuable"
    TO_REVIEW = "to_review"
    HYPE = "hype"


@dataclass(frozen=True, slots=True)
class Criterion:
    """One assessed rubric criterion and its supporting citations."""

    name: CriterionName
    score: int | None
    rationale: str
    citation_ids: tuple[str, ...]
    status: str = "assessed"

    def __post_init__(self) -> None:
        """Reject invalid or unsupported assessment evidence."""
        if self.status not in {"assessed", "not_applicable", "not_verified"}:
            raise ValueError("Unknown criterion status")
        if self.status == "assessed":
            if type(self.score) is not int or not 1 <= self.score <= 5:
                raise ValueError("Assessed criteria require an integer score from 1 to 5")
        elif self.score is not None:
            raise ValueError("Unscored criteria require a null score")
        if self.status == "not_applicable" and self.name is not CriterionName.REPLICABILITY:
            raise ValueError("Only replicability can be not applicable")
        if not self.rationale.strip():
            raise ValueError("criterion rationale must not be empty")
        if not self.citation_ids:
            raise ValueError("criterion must cite supporting evidence")


@dataclass(frozen=True, slots=True)
class HypeSignal:
    rationale: str
    citation_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.rationale.strip() or not self.citation_ids:
            raise ValueError("Hype requires an explanation and primary-source evidence")


@dataclass(frozen=True, slots=True)
class AssessmentDraft:
    """Provider-derived explanation before deterministic verdict calculation."""

    note: str
    criteria: tuple[Criterion, ...]
    hype_signals: tuple[HypeSignal, ...] = ()

    def __post_init__(self) -> None:
        """Require one evidence-backed criterion for every rubric dimension."""
        if not self.note.strip():
            raise ValueError("assessment note must not be empty")
        if {criterion.name for criterion in self.criteria} != set(CriterionName):
            raise ValueError("assessment must contain every criterion exactly once")
        if len(self.criteria) != len(CriterionName):
            raise ValueError("assessment must contain eight criteria")


@dataclass(frozen=True, slots=True)
class CompletedAssessment:
    """Persistable assessment with immutable score and threshold snapshot."""

    note: str
    criteria: tuple[Criterion, ...]
    score: float | None
    verdict: Verdict
    threshold_snapshot: float
    hype_signals: tuple[HypeSignal, ...] = ()
    verdict_reason: str = ""
