import json

import httpx
from fastapi.testclient import TestClient

from linksifty.config import Settings
from linksifty.main import create_app

USER = "11111111-1111-4111-8111-111111111111"
ITEM = "22222222-2222-4222-8222-222222222222"
SETTINGS = Settings(
    supabase_url="https://supabase.example",
    supabase_anon_key="test-anon",
    supabase_service_role_key="test-service",
)
HEADERS = {"Authorization": "Bearer test-session"}


def test_authenticated_submission_persists_job_transaction_before_returning() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/v1/user":
            assert request.headers["Authorization"] == "Bearer test-session"
            return httpx.Response(
                200,
                json={
                    "id": USER,
                    "email": "user@example.com",
                    "email_confirmed_at": "2026-10-14T10:00:00Z",
                },
            )
        if request.url.path.endswith("/rpc/get_or_create_account_profile"):
            return httpx.Response(
                200,
                json=[
                    {
                        "user_id": USER,
                        "email": "user@example.com",
                        "status": "approved",
                        "trial_links_used": 0,
                        "created_at": "2026-10-14T10:00:00Z",
                        "updated_at": "2026-10-14T10:00:00Z",
                    }
                ],
            )
        assert request.url.path == "/rest/v1/rpc/submit_fetch_items"
        assert json.loads(request.content) == {
            "p_user_id": USER,
            "p_urls": ["https://example.com/"],
        }
        return httpx.Response(
            200,
            json=[
                {
                    "id": ITEM,
                    "user_id": USER,
                    "original_url": "https://example.com/",
                    "status": "queued",
                    "unread": True,
                }
            ],
        )

    with TestClient(create_app(SETTINGS, transport=httpx.MockTransport(respond))) as client:
        response = client.post(
            "/v1/items", json={"sources": [{"url": "https://example.com"}]}, headers=HEADERS
        )
        assert response.status_code == 202
        assert response.json()["demo"] is False
        assert response.json()["items"][0]["id"] == ITEM


def test_other_users_item_remains_not_found_after_authentication() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/v1/user":
            return httpx.Response(
                200,
                json={
                    "id": USER,
                    "email": "user@example.com",
                    "email_confirmed_at": "2026-10-14T10:00:00Z",
                },
            )
        if request.url.path.endswith("/rpc/get_or_create_account_profile"):
            return httpx.Response(
                200,
                json=[
                    {
                        "user_id": USER,
                        "email": "user@example.com",
                        "status": "approved",
                        "trial_links_used": 0,
                        "created_at": "2026-10-14T10:00:00Z",
                        "updated_at": "2026-10-14T10:00:00Z",
                    }
                ],
            )
        assert request.url.params["user_id"] == f"eq.{USER}"
        assert request.url.params["id"] == f"eq.{ITEM}"
        return httpx.Response(200, json=[])

    with TestClient(create_app(SETTINGS, transport=httpx.MockTransport(respond))) as client:
        assert client.get(f"/v1/items/{ITEM}", headers=HEADERS).status_code == 404


def test_failed_persistence_never_acknowledges_submission() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/v1/user":
            return httpx.Response(200, json={"id": USER})
        return httpx.Response(500, text="database credentials must not leak")

    with TestClient(create_app(SETTINGS, transport=httpx.MockTransport(respond))) as client:
        response = client.post(
            "/v1/items", json={"sources": [{"url": "https://example.com"}]}, headers=HEADERS
        )
        assert response.status_code == 503
        assert "credentials" not in response.text
