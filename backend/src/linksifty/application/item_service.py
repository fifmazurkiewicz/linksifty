"""Item use cases operating on verified user identities."""

from uuid import UUID

from linksifty.application.item_contracts import ItemRecord, ItemRepository


class ItemService:
    """Orchestrate item storage separately from HTTP route definitions."""

    def __init__(self, repository: ItemRepository) -> None:
        self._repository = repository

    async def inbox(self, user_id: UUID) -> list[ItemRecord]:
        return await self._repository.list_items(user_id)

    async def detail(self, user_id: UUID, item_id: UUID) -> ItemRecord | None:
        return await self._repository.get_item(user_id, item_id)

    async def submit(self, user_id: UUID, urls: list[str]) -> list[ItemRecord]:
        return await self._repository.create_items(user_id, urls)

    async def delete(self, user_id: UUID, item_ids: list[UUID]) -> list[UUID]:
        return await self._repository.delete_items(user_id, item_ids)
