import asyncio
import json
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

from linksifty.api.auth import current_user
from linksifty.application.item_contracts import ItemRepository
from linksifty.application.item_service import ItemService
from linksifty.config import Settings
from linksifty.infrastructure.supabase_repository import SupabaseRepository
from linksifty.main import create_app

USER = UUID("11111111-1111-4111-8111-111111111111")
ITEM = UUID("22222222-2222-4222-8222-222222222222")
OTHER = UUID("33333333-3333-4333-8333-333333333333")


@pytest.mark.parametrize("identifiers", [[ITEM], [ITEM, OTHER]])
def test_confirmed_delete_uses_verified_owner_and_returns_deleted_ids(
    identifiers: list[UUID],
) -> None:
    repository = Mock(spec=ItemRepository)
    repository.delete_items = AsyncMock(return_value=identifiers)
    app = create_app(Settings(demo_mode=True))
    app.state.items = ItemService(repository)
    app.dependency_overrides[current_user] = lambda: USER
    response = TestClient(app).post(
        "/v1/items/delete",
        json={"item_ids": [str(value) for value in identifiers], "confirmed": True},
    )
    assert response.status_code == 200
    assert response.json() == {"deleted_ids": [str(value) for value in identifiers]}
    repository.delete_items.assert_awaited_once_with(USER, identifiers)


@pytest.mark.parametrize(
    "payload",
    [
        {"item_ids": [str(ITEM)]},
        {"item_ids": [str(ITEM)], "confirmed": False},
        {"item_ids": [str(ITEM)], "confirmed": "true"},
        {"item_ids": [str(ITEM)], "confirmed": 1},
        {"item_ids": [], "confirmed": True},
        {"item_ids": [str(ITEM)] * 51, "confirmed": True},
        {"item_ids": [str(ITEM), str(ITEM)], "confirmed": True},
        {"item_ids": ["invalid"], "confirmed": True},
        {"item_ids": [str(ITEM)], "confirmed": True, "user_id": str(OTHER)},
    ],
)
def test_invalid_or_unconfirmed_delete_never_reaches_database(payload: dict[str, object]) -> None:
    repository = Mock(spec=ItemRepository)
    repository.delete_items = AsyncMock()
    app = create_app(Settings(demo_mode=True))
    app.state.items = ItemService(repository)
    app.dependency_overrides[current_user] = lambda: USER
    assert TestClient(app).post("/v1/items/delete", json=payload).status_code == 422
    repository.delete_items.assert_not_awaited()


def test_foreign_or_missing_batch_has_generic_not_found_response() -> None:
    repository = Mock(spec=ItemRepository)
    repository.delete_items = AsyncMock(return_value=[])
    app = create_app(Settings(demo_mode=True))
    app.state.items = ItemService(repository)
    app.dependency_overrides[current_user] = lambda: USER
    response = TestClient(app).post(
        "/v1/items/delete", json={"item_ids": [str(ITEM), str(OTHER)], "confirmed": True}
    )
    assert response.status_code == 404
    assert str(OTHER) not in response.text


def test_anonymous_delete_cannot_access_service() -> None:
    app = create_app(Settings())
    response = TestClient(app).post(
        "/v1/items/delete", json={"item_ids": [str(ITEM)], "confirmed": True}
    )
    assert response.status_code == 401


def test_repository_uses_one_confirmed_owner_scoped_transaction() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/rpc/delete_items")
        assert request.method == "POST"
        assert json.loads(request.content) == {
            "p_user_id": str(USER),
            "p_item_ids": [str(ITEM), str(OTHER)],
            "p_confirmed": True,
        }
        return httpx.Response(200, json=[{"id": str(ITEM)}, {"id": str(OTHER)}])

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repository = SupabaseRepository("https://supabase.example", "test-key", client)
            assert await repository.delete_items(USER, [ITEM, OTHER]) == [ITEM, OTHER]

    asyncio.run(run())
