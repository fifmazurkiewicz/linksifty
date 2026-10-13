"""Deterministic local repository used until Supabase is configured."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class StoredItem:
    id: str
    user_id: str
    url: str
    status: str = "queued"
    unread: bool = True


class MemoryRepository:
    """User-scoped in-process storage with the same ownership rule as Supabase."""

    def __init__(self) -> None:
        self._items: list[StoredItem] = []

    def create_item(self, user_id: str, url: str, *, unread: bool = True) -> StoredItem:
        item = StoredItem(id=str(uuid4()), user_id=user_id, url=url, unread=unread)
        self._items.append(item)
        return item

    def get_item(self, user_id: str, item_id: str) -> StoredItem | None:
        return next(
            (item for item in self._items if item.id == item_id and item.user_id == user_id),
            None,
        )

    def list_items(self, user_id: str) -> list[StoredItem]:
        return sorted(
            (item for item in self._items if item.user_id == user_id),
            key=lambda item: not item.unread,
        )
