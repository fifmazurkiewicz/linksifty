import asyncio
from uuid import UUID

import httpx
import pytest

from linksifty.infrastructure.supabase_repository import (
    AccountPolicyViolation,
    RepositoryUnavailable,
    SupabaseRepository,
)

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


def test_trial_limit_is_a_policy_error_not_a_persistence_outage() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda _: httpx.Response(
                400,
                json={"code": "P0001", "message": "account_trial_limit_exceeded"},
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            await SupabaseRepository("https://supabase.example", "test-key", client).create_items(
                USER, ["https://example.com/1"]
            )

    with pytest.raises(AccountPolicyViolation, match="trial_limit_exceeded"):
        asyncio.run(run())


def test_profile_bootstrap_uses_verified_identity_and_server_admin_decision() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/rpc/get_or_create_account_profile")
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.read() == (
            b'{"p_user_id":"11111111-1111-4111-8111-111111111111",'
            b'"p_email":"admin@example.com","p_is_admin":true}'
        )
        return httpx.Response(
            200,
            json=[
                {
                    "user_id": str(USER),
                    "email": "admin@example.com",
                    "status": "approved",
                    "trial_links_used": 0,
                    "created_at": "2026-10-14T10:00:00Z",
                }
            ],
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            profile = await SupabaseRepository(
                "https://supabase.example", "test-key", client
            ).get_or_create_profile(USER, "admin@example.com", is_admin=True)
            assert profile.user_id == USER
            assert profile.status == "approved"

    asyncio.run(run())


def test_admin_account_listing_selects_only_account_metadata() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/rpc/list_admin_account_summaries")
        return httpx.Response(
            200,
            json=[
                {
                    "user_id": str(USER),
                    "email": "user@example.com",
                    "status": "pending",
                    "trial_links_used": 2,
                    "created_at": "2026-10-14T10:00:00Z",
                    "approval_email_status": "failed",
                    "approval_email_failure_code": "timeout",
                }
            ],
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            profiles = await SupabaseRepository(
                "https://supabase.example", "test-key", client
            ).list_admin_profiles()
            assert profiles[0].status == "pending"
            assert profiles[0].approval_email_status == "failed"

    asyncio.run(run())


def test_account_status_update_uses_locked_transition_rpc() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/rpc/set_account_profile_status")
        assert request.read() == (
            b'{"p_user_id":"11111111-1111-4111-8111-111111111111","p_status":"approved"}'
        )
        return httpx.Response(
            200,
            json=[
                {
                    "previous_status": "pending",
                    "user_id": str(USER),
                    "email": "user@example.com",
                    "status": "approved",
                    "trial_links_used": 2,
                    "created_at": "2026-10-14T10:00:00Z",
                    "approval_notification_id": "33333333-3333-4333-8333-333333333333",
                }
            ],
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            change = await SupabaseRepository(
                "https://supabase.example", "test-key", client
            ).set_profile_status(USER, "approved")
            assert change is not None
            previous, current, notification_id = change
            assert previous == "pending"
            assert current.status == "approved"
            assert notification_id == UUID("33333333-3333-4333-8333-333333333333")

    asyncio.run(run())


def test_notification_claim_and_delivery_update_use_private_rpcs() -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if request.url.path.endswith("/rpc/claim_account_notification"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "33333333-3333-4333-8333-333333333333",
                        "user_id": str(USER),
                        "email": "user@example.com",
                        "attempts": 1,
                    }
                ],
            )
        assert request.url.path.endswith("/rpc/finish_account_notification")
        return httpx.Response(200, json=[])

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repository = SupabaseRepository("https://supabase.example", "test-key", client)
            notification = await repository.claim_approval_notification(
                UUID("33333333-3333-4333-8333-333333333333")
            )
            assert notification is not None
            assert notification.email == "user@example.com"
            await repository.finish_approval_notification(
                notification.notification_id,
                status="sent",
                provider_message_id="message_1",
                failure_code=None,
            )

    asyncio.run(run())
    assert calls == 2


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
