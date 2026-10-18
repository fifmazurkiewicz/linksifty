"""Budgeted image acquisition boundaries; extracted text is not an assessment."""

from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, Field

from linksifty.domain.acquisition import SourceImage


class MediaResult(BaseModel):
    text: str | None = None
    readable_text: str | None = None
    failure_reason: str | None = None
    generation_id: str | None = None
    cost: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)


class ImageReader(Protocol):
    def estimate(self) -> Decimal: ...
    async def extract(self, images: tuple[SourceImage, ...]) -> MediaResult: ...
