"""Typed boundaries for progress, exact USD accounting and source-grounded results."""

from contextlib import AbstractContextManager
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from linksifty.application.item_contracts import ItemRecord
from linksifty.domain.models import CriterionName


class UsageSummary(BaseModel):
    month: date
    spent_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    reserved_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    limit_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    remaining_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    resets_at: datetime


class UserSettings(BaseModel):
    valuable_threshold: Decimal = Field(ge=40, le=100, allow_inf_nan=False)


class EvidenceSource(BaseModel):
    id: str
    url: str
    text: str


class ResearchContext(BaseModel):
    status: str = "not_requested"
    sources: list[EvidenceSource] = Field(default_factory=list, max_length=5)


class ResearchSourceView(BaseModel):
    id: str
    url: str


class Telemetry(Protocol):
    def scope(self, name: str, identifier: str) -> AbstractContextManager[None]: ...


class SourceCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = "primary"
    name: CriterionName
    score: int = Field(ge=1, le=5, strict=True)
    rationale: str = Field(min_length=1, max_length=3000)
    excerpt: str = Field(min_length=10, max_length=2000)


class SourceAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str = Field(min_length=1, max_length=6000)
    criteria: list[SourceCriterion] = Field(min_length=8, max_length=8)


class ModelResult(BaseModel):
    failure_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    generation_id: str | None = None
    cost: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    assessment: SourceAssessment | None = None


class ProcessingJob(BaseModel):
    web_search: bool = False
    search_reservation_id: UUID | None = None
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
    research_status: str = "not_requested"
    research_sources: list[ResearchSourceView] = Field(default_factory=list)
    note: str
    criteria: list[dict[str, object]]
    score: float
    verdict: str
    threshold_snapshot: float
    citations: list[CitationView] = Field(default_factory=list)


class ProcessingStore(Protocol):
    async def submit_search(self, user_id: UUID, urls: list[str]) -> list[ItemRecord]: ...
    async def reserve_search(self, job: ProcessingJob, amount: Decimal) -> Reservation | None: ...
    async def save_research(self, job: ProcessingJob, context: ResearchContext) -> bool: ...
    async def heartbeat(self, job: ProcessingJob) -> bool: ...
    async def orphaned_reservations(self, user_id: UUID) -> list[PendingReservation]: ...
    async def usage(self, user_id: UUID) -> UsageSummary: ...
    async def update_threshold(self, user_id: UUID, threshold: Decimal) -> UserSettings: ...
    async def update_budget(self, user_id: UUID, limit: Decimal) -> UsageSummary: ...
    async def inbox(self, user_id: UUID) -> list[ItemRecord]: ...
    async def paste(
        self, user_id: UUID, text: str, item_id: UUID | None = None
    ) -> ItemRecord | None: ...
    async def resume(self, user_id: UUID, item_id: UUID) -> ItemRecord | None: ...
    async def assessment(self, user_id: UUID, item_id: UUID) -> AssessmentView | None: ...
    async def claim(self, user_id: UUID) -> ProcessingJob | None: ...
    async def stage(self, job: ProcessingJob, stage: str, status: str = "processing") -> bool: ...
    async def save_source(self, job: ProcessingJob, text: str) -> bool: ...
    async def reserve(self, job: ProcessingJob, amount: Decimal) -> Reservation | None: ...
    async def settings(self, user_id: UUID) -> UserSettings: ...
    async def record_result(self, job: ProcessingJob, result: ModelResult) -> bool: ...
    async def settle(self, user_id: UUID, reservation_id: UUID, cost: Decimal) -> None: ...
    async def complete(self, job: ProcessingJob, assessment: AssessmentView) -> bool: ...
    async def cleanup(self, user_id: UUID) -> None: ...


class AssessmentProvider(Protocol):
    def estimate(self, text: str) -> Decimal: ...
    async def assess(
        self, text: str, *, sources: list[EvidenceSource] | None = None
    ) -> ModelResult: ...
    async def reconcile(self, generation_id: str) -> Decimal | None: ...
