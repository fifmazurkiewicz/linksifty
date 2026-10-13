"""Item DTOs and persistence boundary used by application services."""

from typing import Protocol
from uuid import UUID

from pydantic import BaseModel

from linksifty.domain.jobs import JobStatus


class ItemRecord(BaseModel):
    id: UUID
    user_id: UUID
    original_url: str | None = None
    title: str | None = None
    status: JobStatus
    unread: bool


class ItemRepository(Protocol):
    async def list_items(self, user_id: UUID, *, offset: int = 0) -> list[ItemRecord]: ...

    async def get_item(self, user_id: UUID, item_id: UUID) -> ItemRecord | None: ...

    async def create_items(self, user_id: UUID, urls: list[str]) -> list[ItemRecord]: ...
