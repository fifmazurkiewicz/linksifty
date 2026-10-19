from unittest.mock import create_autospec
from uuid import uuid4

from fastapi.testclient import TestClient

from linksifty.api.auth import current_user
from linksifty.application.discussions import Discussion, DiscussionHistory, DiscussionService
from linksifty.config import Settings
from linksifty.main import create_app


def test_discussions_require_explicit_strict_consent_and_scope_to_the_verified_owner() -> None:
    user, item = uuid4(), uuid4()
    service = create_autospec(DiscussionService, instance=True)
    service.history.return_value = DiscussionHistory(available=True, sources=[])
    service.load.return_value = Discussion(source_id="primary", url="https://x.com/u/status/100")
    app = create_app(Settings(demo_mode=True))
    app.state.discussions = service
    app.dependency_overrides[current_user] = lambda: user
    client = TestClient(app)
    endpoint = f"/v1/items/{item}/discussions"
    result = client.get(endpoint)
    assert result.status_code == 200 and result.headers["cache-control"] == "no-store"
    service.history.assert_awaited_once_with(user, item)
    service.load.assert_not_awaited()
    for body in (
        {"source_id": "primary"},
        {"source_id": "primary", "consent": False},
        {"source_id": "primary", "consent": 1},
        {"source_id": "primary", "consent": True, "url": "https://evil.test"},
    ):
        assert client.post(endpoint, json=body).status_code == 422
    service.load.assert_not_awaited()
    result = client.post(endpoint, json={"source_id": "primary", "consent": True})
    assert result.status_code == 200 and result.headers["cache-control"] == "no-store"
    service.load.assert_awaited_once_with(user, item, "primary", consent=True)
    service.history.side_effect = ValueError("not_found")
    assert client.get(endpoint).status_code == 404


def test_anonymous_discussion_access_is_denied_before_service_access() -> None:
    app = create_app(Settings())
    service = create_autospec(DiscussionService, instance=True)
    app.state.discussions = service
    client = TestClient(app)
    endpoint = f"/v1/items/{uuid4()}/discussions"
    assert client.get(endpoint).status_code == 401
    assert client.post(endpoint, json={"source_id": "primary", "consent": True}).status_code == 401
    service.history.assert_not_awaited()
    service.load.assert_not_awaited()
