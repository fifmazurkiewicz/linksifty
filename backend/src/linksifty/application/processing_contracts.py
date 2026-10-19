"""Typed boundaries for progress, exact USD accounting and source-grounded results."""

from contextlib import AbstractContextManager
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from linksifty.application.item_contracts import ItemRecord
from linksifty.domain.acquisition import MediaType
from linksifty.domain.models import Criterion, CriterionName
from linksifty.domain.rubric import AssessmentRubric, RubricCriterion, default_rubric


class UsageSummary(BaseModel):
    month: date
    spent_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    reserved_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    limit_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    remaining_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    resets_at: datetime


class RubricEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: CriterionName
    description: str = Field(min_length=1, max_length=1000)
    weight: int = Field(ge=1, le=10, strict=True)

    @field_validator("description")
    @classmethod
    def readable_description(cls, value: str) -> str:
        if not value.strip() or "\x00" in value:
            raise ValueError("Description must contain readable text without NUL")
        return value.strip()


class RubricConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal[1, 2] = 1
    criteria: tuple[RubricEntry, ...] = Field(min_length=8, max_length=8)

    @model_validator(mode="after")
    def complete_rubric(self) -> "RubricConfig":
        self.to_domain()
        by_name = {entry.name: entry for entry in self.criteria}
        object.__setattr__(self, "criteria", tuple(by_name[name] for name in CriterionName))
        return self

    def to_domain(self) -> AssessmentRubric:
        return AssessmentRubric(
            tuple(RubricCriterion(c.name, c.description, c.weight) for c in self.criteria),
            version=self.version,
        )

    @classmethod
    def default(cls, *, version: Literal[1, 2] = 2) -> "RubricConfig":
        return cls(
            version=version,
            criteria=tuple(
                RubricEntry(name=c.name, description=c.description, weight=c.weight)
                for c in default_rubric(version=version).criteria
            ),
        )


class UserSettings(BaseModel):
    rubric: RubricConfig = Field(default_factory=RubricConfig.default)
    valuable_threshold: Decimal = Field(ge=40, le=100, allow_inf_nan=False)


class EvidenceSource(BaseModel):
    id: str
    url: str
    text: str
    omitted_media: list[MediaType] | None = Field(default=None, max_length=5)


class ResearchSourceView(BaseModel):
    id: str
    url: str
    omitted_media: list[MediaType] | None = Field(default=None, max_length=5)


class ResearchContext(BaseModel):
    status: str = "not_requested"
    sources: list[EvidenceSource] = Field(default_factory=list, max_length=20)
    discussion_sources: list[ResearchSourceView] = Field(default_factory=list, max_length=20)


class Telemetry(Protocol):
    def scope(self, name: str, identifier: str) -> AbstractContextManager[None]: ...
    def event(self, name: str, details: dict[str, object]) -> None: ...


class SourceCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = "primary"
    name: CriterionName
    score: int | None = Field(ge=1, le=5, strict=True)
    status: Literal["assessed", "not_applicable", "not_verified"] = "assessed"
    rationale: str = Field(min_length=1, max_length=3000)
    excerpt: str = Field(min_length=10, max_length=2000)

    @model_validator(mode="after")
    def valid_points(self) -> "SourceCriterion":
        Criterion(self.name, self.score, self.rationale, ("source",), self.status)
        return self


class SourceHypeSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rationale: str = Field(min_length=1, max_length=1000)
    source_id: Literal["primary"] = "primary"
    excerpt: str = Field(min_length=10, max_length=2000)


class SourceAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str = Field(min_length=1, max_length=6000)
    criteria: list[SourceCriterion] = Field(min_length=8, max_length=8)
    hype_signals: list[SourceHypeSignal] = Field(default_factory=list, max_length=3)


class ModelResult(BaseModel):
    failure_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    generation_id: str | None = None
    cost: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    assessment: SourceAssessment | None = None


class ProcessingJob(BaseModel):
    rubric_snapshot: RubricConfig | None = None
    web_search: bool = False
    search_reservation_id: UUID | None = None
    selection_reservation_id: UUID | None = None
    search_context: ResearchContext | None = None
    id: UUID
    item_id: UUID
    user_id: UUID
    lease_token: UUID
    original_url: str | None = None
    source_text: str | None = None
    threshold_snapshot: Decimal | None = None
    reservation_id: UUID | None = None
    generation_id: str | None = None
    actual_usd: Decimal | None = None
    reservation_state: str | None = None
    model_result: ModelResult | None = None


class Reservation(BaseModel):
    rubric_snapshot: RubricConfig = Field(default_factory=RubricConfig.default)
    id: UUID
    state: Literal["reserved", "settled"]
    actual_usd: Decimal | None = None
    threshold_snapshot: Decimal = Field(ge=40, le=100)


class PendingReservation(BaseModel):
    id: UUID
    generation_id: str


class CitationView(BaseModel):
    source_id: str = "primary"
    id: UUID
    excerpt: str
    start_position: int
    end_position: int
    source_url: str | None = None


class AssessmentView(BaseModel):
    omitted_media: list[MediaType] | None = Field(default=None, max_length=5)
    rubric_snapshot: RubricConfig = Field(default_factory=lambda: RubricConfig.default(version=1))
    research_status: str = "not_requested"
    research_sources: list[ResearchSourceView] = Field(default_factory=list)
    note: str
    criteria: list[dict[str, object]]
    score: float | None
    verdict: str
    threshold_snapshot: float
    hype_signals: list[dict[str, object]] = Field(default_factory=list)
    verdict_reason: str = ""
    citations: list[CitationView] = Field(default_factory=list)


class ProcessingStore(Protocol):
    async def reserve_selection(self, job: ProcessingJob, amount: Decimal) -> UUID | None: ...
    async def record_selection_generation(
        self, job: ProcessingJob, reservation_id: UUID, generation_id: str | None
    ) -> None: ...
    async def reserve_images(self, job: ProcessingJob, amount: Decimal) -> UUID | None: ...
    async def record_image_generation(
        self, job: ProcessingJob, reservation_id: UUID, generation_id: str | None
    ) -> None: ...
    async def begin_x_fetch(self, job: ProcessingJob) -> bool: ...
    async def submit_search(self, user_id: UUID, urls: list[str]) -> list[ItemRecord]: ...
    async def reserve_search(self, job: ProcessingJob, amount: Decimal) -> Reservation | None: ...
    async def save_research(self, job: ProcessingJob, context: ResearchContext) -> bool: ...
    async def heartbeat(self, job: ProcessingJob) -> bool: ...
    async def orphaned_reservations(self, user_id: UUID) -> list[PendingReservation]: ...
    async def usage(self, user_id: UUID) -> UsageSummary: ...
    async def update_settings(
        self, user_id: UUID, threshold: Decimal, rubric: RubricConfig | None
    ) -> UserSettings: ...
    async def update_budget(self, user_id: UUID, limit: Decimal) -> UsageSummary: ...
    async def inbox(self, user_id: UUID) -> list[ItemRecord]: ...
    async def paste(
        self, user_id: UUID, text: str, item_id: UUID | None = None
    ) -> ItemRecord | None: ...
    async def resume(self, user_id: UUID, item_id: UUID) -> ItemRecord | None: ...
    async def assessment(self, user_id: UUID, item_id: UUID) -> AssessmentView | None: ...
    async def claim(self, user_id: UUID) -> ProcessingJob | None: ...
    async def stage(self, job: ProcessingJob, stage: str, status: str = "processing") -> bool: ...
    async def save_source(
        self, job: ProcessingJob, text: str, *, omitted_media: tuple[MediaType, ...] = ()
    ) -> bool: ...
    async def reserve(self, job: ProcessingJob, amount: Decimal) -> Reservation | None: ...
    async def settings(self, user_id: UUID) -> UserSettings: ...
    async def record_result(self, job: ProcessingJob, result: ModelResult) -> bool: ...
    async def settle(self, user_id: UUID, reservation_id: UUID, cost: Decimal) -> None: ...
    async def complete(self, job: ProcessingJob, assessment: AssessmentView) -> bool: ...
    async def cleanup(self, user_id: UUID) -> None: ...


class AssessmentProvider(Protocol):
    def estimate(self, text: str) -> Decimal: ...
    async def assess(
        self,
        text: str,
        *,
        sources: list[EvidenceSource] | None = None,
        rubric: RubricConfig | None = None,
        primary_url: str | None = None,
    ) -> ModelResult: ...
    async def reconcile(self, generation_id: str) -> Decimal | None: ...
