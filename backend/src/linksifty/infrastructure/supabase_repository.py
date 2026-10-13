"""User-scoped Supabase REST persistence with validated responses."""

from uuid import UUID

import httpx
from pydantic import TypeAdapter, ValidationError

from linksifty.application.item_contracts import ItemRecord


class RepositoryUnavailable(Exception):
    """Persistence failed; provider details remain server-side."""


_items = TypeAdapter(list[ItemRecord])


class SupabaseRepository:
    """Service-role adapter; every operation also enforces the verified owner."""

    def __init__(self, url: str, service_key: str, client: httpx.AsyncClient) -> None:
        self._url = f"{url.rstrip('/')}/rest/v1"
        self._headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
        self._client = client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, object] | None = None,
    ) -> list[ItemRecord]:
        try:
            response = await self._client.request(
                method,
                f"{self._url}/{path}",
                headers={**self._headers, "Prefer": "return=representation"},
                params=params,
                json=payload,
                timeout=10,
                follow_redirects=False,
            )
            if not response.is_success:
                raise RepositoryUnavailable("Persistence temporarily unavailable")
            return _items.validate_json(response.content)
        except (httpx.HTTPError, ValidationError) as error:
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def list_items(self, user_id: UUID, *, offset: int = 0) -> list[ItemRecord]:
        if offset < 0:
            raise ValueError("offset must not be negative")
        return await self._request(
            "GET",
            "items",
            params={
                "user_id": f"eq.{user_id}",
                "order": "unread.desc,created_at.desc",
                "limit": "50",
                "offset": str(offset),
            },
        )

    async def get_item(self, user_id: UUID, item_id: UUID) -> ItemRecord | None:
        records = await self._request(
            "GET", "items", params={"user_id": f"eq.{user_id}", "id": f"eq.{item_id}", "limit": "1"}
        )
        return records[0] if records else None

    async def create_items(self, user_id: UUID, urls: list[str]) -> list[ItemRecord]:
        if not 1 <= len(urls) <= 5:
            raise ValueError("submit between one and five links")
        return await self._request(
            "POST", "rpc/submit_fetch_items", payload={"p_user_id": str(user_id), "p_urls": urls}
        )

    async def delete_item(self, user_id: UUID, item_id: UUID) -> bool:
        records = await self._request(
            "DELETE", "items", params={"user_id": f"eq.{user_id}", "id": f"eq.{item_id}"}
        )
        return bool(records)

    async def mark_read(self, user_id: UUID, item_id: UUID, *, unread: bool) -> ItemRecord | None:
        records = await self._request(
            "PATCH",
            "items",
            params={"user_id": f"eq.{user_id}", "id": f"eq.{item_id}"},
            payload={"unread": unread},
        )
        return records[0] if records else None
