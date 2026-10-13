from fastapi.testclient import TestClient

from linksifty.config import Settings
from linksifty.main import create_app


def test_inbox_returns_explicit_demo_items() -> None:
    response = TestClient(create_app(Settings.for_test())).get("/v1/items")

    assert response.status_code == 200
    assert response.json()["items"][0]["status"] == "completed"


def test_submit_rejects_more_than_five_sources() -> None:
    response = TestClient(create_app(Settings.for_test())).post(
        "/v1/items", json={"sources": [{"url": "https://example.com"}] * 6}
    )

    assert response.status_code == 422


def test_item_detail_returns_manual_content_recovery_state() -> None:
    response = TestClient(create_app(Settings.for_test())).get("/v1/items/demo-manual-content")

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_manual_content"


def test_unknown_item_is_not_found() -> None:
    response = TestClient(create_app(Settings.for_test())).get("/v1/items/nope")

    assert response.status_code == 404
