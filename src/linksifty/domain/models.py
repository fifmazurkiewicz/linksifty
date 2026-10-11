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
    score: int
    rationale: str
    citation_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject invalid or unsupported assessment evidence."""
        if not 1 <= self.score <= 5:
            raise ValueError("criterion score must be between 1 and 5")
        if not self.rationale.strip():
            raise ValueError("criterion rationale must not be empty")
        if not self.citation_ids:
            raise ValueError("criterion must cite supporting evidence")


@dataclass(frozen=True, slots=True)
class AssessmentDraft:
    """Provider-derived explanation before deterministic verdict calculation."""

    note: str
    criteria: tuple[Criterion, ...]

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
    score: float
    verdict: Verdict
    threshold_snapshot: float
