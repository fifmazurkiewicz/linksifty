from unittest.mock import create_autospec
from uuid import uuid4

from fastapi.testclient import TestClient

from linksifty.api.auth import current_user
from linksifty.application.chat_contracts import ChatError, ChatHistory, ChatTurn
from linksifty.application.chat_service import ChatService
from linksifty.config import Settings
from linksifty.main import create_app


def test_chat_routes_authenticate_validate_and_use_only_verified_owner() -> None:
    user, item, request_id = uuid4(), uuid4(), uuid4()
    service = create_autospec(ChatService, instance=True)
    service.history.return_value = ChatHistory(turns=[], available=True, search_available=True)
    service.ask.return_value = ChatTurn(
        id=request_id, item_id=item, question="Why?", status="pending"
    )
    app = create_app(Settings(demo_mode=True))
    app.state.chat = service
    app.dependency_overrides[current_user] = lambda: user
    client = TestClient(app)
    loaded = client.get(f"/v1/items/{item}/chat")
    assert loaded.status_code == 200
    assert loaded.headers["Cache-Control"] == "no-store"
    service.history.assert_awaited_once_with(user, item)
    for question in ["", "  ", "\x00", "a" * 4001]:
        assert (
            client.post(
                f"/v1/items/{item}/chat", json={"question": question, "request_id": str(request_id)}
            ).status_code
            == 422
        )
    assert (
        client.post(
            f"/v1/items/{item}/chat",
            json={"question": "Why?", "request_id": str(request_id), "user_id": str(uuid4())},
        ).status_code
        == 422
    )
    response = client.post(
        f"/v1/items/{item}/chat", json={"question": " Why? ", "request_id": str(request_id)}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert "sources" not in response.json()
    service.ask.assert_awaited_once_with(user, item, request_id, "Why?")


def test_missing_content_and_duplicate_conflicts_have_safe_http_errors() -> None:
    service = create_autospec(ChatService, instance=True)
    app = create_app(Settings(demo_mode=True))
    app.state.chat = service
    client = TestClient(app)
    item = uuid4()
    service.history.side_effect = ChatError("not_found")
    assert client.get(f"/v1/items/{item}/chat").status_code == 404
    service.ask.side_effect = ChatError("request_conflict")
    assert (
        client.post(
            f"/v1/items/{item}/chat", json={"question": "Why?", "request_id": str(uuid4())}
        ).status_code
        == 409
    )


def test_anonymous_chat_fails_before_content_or_provider_access() -> None:
    app = create_app(Settings())
    client = TestClient(app)
    item = uuid4()
    assert client.get(f"/v1/items/{item}/chat").status_code == 401
    assert (
        client.post(
            f"/v1/items/{item}/chat", json={"question": "Why?", "request_id": str(uuid4())}
        ).status_code
        == 401
    )
