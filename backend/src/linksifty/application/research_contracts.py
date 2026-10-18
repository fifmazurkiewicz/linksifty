"""Search discovery boundary; results alone are not evidence."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class SearchCandidate:
    url: str
    title: str = ""
    snippet: str = ""


@dataclass(frozen=True)
class SearchResponse:
    confirmed: bool = False
    urls: tuple[str, ...] = ()
    candidates: tuple[SearchCandidate, ...] = ()


class SearchProvider(Protocol):
    async def search(self, query: str) -> SearchResponse: ...


class SourceDecision(BaseModel):
    candidate_id: int = Field(ge=0, lt=20, strict=True)
    relevant: bool = Field(strict=True)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)


class SourceSelection(BaseModel):
    decisions: list[SourceDecision] = Field(default_factory=list, max_length=20)
    generation_id: str | None = None
    cost: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    failure_reason: str | None = None


class SourceSelector(Protocol):
    def estimate(self, candidate_count: int) -> Decimal: ...
    async def select(
        self, text: str, query: str, candidates: tuple[SearchCandidate, ...]
    ) -> SourceSelection: ...
