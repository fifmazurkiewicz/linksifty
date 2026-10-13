import asyncio
from uuid import UUID

import httpx
import pytest

from linksifty.infrastructure.supabase_repository import RepositoryUnavailable, SupabaseRepository

USER = UUID("11111111-1111-4111-8111-111111111111")
ITEM = UUID("22222222-2222-4222-8222-222222222222")


def test_list_always_filters_by_authenticated_owner() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.params["user_id"] == f"eq.{USER}"
        assert request.url.params["limit"] == "50"
        return httpx.Response(200, json=[])

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repository = SupabaseRepository("https://supabase.example", "test-key", client)
            assert await repository.list_items(USER) == []

    asyncio.run(run())


def test_get_always_filters_owner_and_item() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.params["user_id"] == f"eq.{USER}"
        assert request.url.params["id"] == f"eq.{ITEM}"
        return httpx.Response(200, json=[])

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repository = SupabaseRepository("https://supabase.example", "test-key", client)
            assert await repository.get_item(USER, ITEM) is None

    asyncio.run(run())


def test_provider_errors_do_not_leak_response_body() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda _: httpx.Response(500, text="sensitive provider data")
        )
        async with httpx.AsyncClient(transport=transport) as client:
            await SupabaseRepository("https://supabase.example", "test-key", client).list_items(
                USER
            )

    with pytest.raises(RepositoryUnavailable) as captured:
        asyncio.run(run())
    assert "sensitive" not in str(captured.value)


def test_delete_always_filters_owner_and_item() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.params["user_id"] == f"eq.{USER}"
        assert request.url.params["id"] == f"eq.{ITEM}"
        return httpx.Response(200, json=[])

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repository = SupabaseRepository("https://supabase.example", "test-key", client)
            assert not await repository.delete_item(USER, ITEM)

    asyncio.run(run())
