import asyncio
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

from linksifty.config import Settings
from linksifty.infrastructure.supabase_auth import (
    AuthenticationUnavailable,
    InvalidToken,
    SupabaseAuthenticator,
)
from linksifty.main import create_app

USER_ID = "11111111-1111-4111-8111-111111111111"


def test_authenticator_uses_server_verified_identity() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/auth/v1/user"
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["apikey"] == "test-key"
        return httpx.Response(200, json={"id": USER_ID})

    async def run() -> UUID:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            auth = SupabaseAuthenticator("https://supabase.example", "test-key", client)
            return await auth.verify("test-token")

    assert asyncio.run(run()) == UUID(USER_ID)


@pytest.mark.parametrize("status", [401, 403])
def test_invalid_tokens_are_rejected(status: int) -> None:
    async def run() -> None:
        transport = httpx.MockTransport(lambda _: httpx.Response(status))
        async with httpx.AsyncClient(transport=transport) as client:
            await SupabaseAuthenticator("https://supabase.example", "test-key", client).verify(
                "bad"
            )

    with pytest.raises(InvalidToken):
        asyncio.run(run())


@pytest.mark.parametrize("payload", [{}, {"id": "not-a-uuid"}])
def test_malformed_provider_identity_fails_closed(payload: dict[str, str]) -> None:
    async def run() -> None:
        transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
        async with httpx.AsyncClient(transport=transport) as client:
            await SupabaseAuthenticator("https://supabase.example", "test-key", client).verify(
                "bad"
            )

    with pytest.raises(AuthenticationUnavailable):
        asyncio.run(run())


def test_production_routes_require_authentication() -> None:
    with TestClient(create_app(Settings())) as client:
        assert client.get("/health").status_code == 200
        for path in ("/v1/items", "/v1/items/demo-completed"):
            response = client.get(path)
            assert response.status_code == 401
            assert response.headers["WWW-Authenticate"] == "Bearer"
        assert (
            client.post("/v1/items", json={"sources": [{"url": "https://example.com"}]}).status_code
            == 401
        )


def test_missing_supabase_configuration_cannot_enable_demo() -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.get("/v1/items", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 503


def test_authenticator_timeout_does_not_admit_user() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("test timeout", request=request)

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            await SupabaseAuthenticator("https://supabase.example", "test-key", client).verify(
                "bad"
            )

    with pytest.raises(AuthenticationUnavailable):
        asyncio.run(run())


def test_verified_production_identity_never_receives_demo_data() -> None:
    settings = Settings(supabase_url="https://supabase.example", supabase_anon_key="test-key")
    with TestClient(create_app(settings)) as client:
        transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"id": USER_ID}))
        async_client = httpx.AsyncClient(transport=transport)
        client.app.state.authenticator = SupabaseAuthenticator(
            settings.supabase_url or "", "test-key", async_client
        )
        try:
            response = client.get("/v1/items", headers={"Authorization": "Bearer test-token"})
            assert response.status_code == 503
            assert "demo-completed" not in response.text
        finally:
            asyncio.run(async_client.aclose())
