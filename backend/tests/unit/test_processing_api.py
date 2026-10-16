from decimal import Decimal
from typing import cast
from unittest.mock import create_autospec
from uuid import UUID

from fastapi.testclient import TestClient

from linksifty.api.auth import current_user
from linksifty.application.account_contracts import AccountService
from linksifty.application.processing_contracts import UsageSummary, UserSettings
from linksifty.application.processing_service import ProcessingService
from linksifty.config import Settings
from linksifty.main import create_app

USER = UUID("11111111-1111-4111-8111-111111111111")
OTHER = UUID("22222222-2222-4222-8222-222222222222")


def test_settings_validate_and_scope_to_verified_user() -> None:
    service = create_autospec(ProcessingService, instance=True)
    service.update_settings.return_value = UserSettings(valuable_threshold=Decimal(75))
    app = create_app(Settings(demo_mode=True))
    app.state.processing = cast(ProcessingService, service)
    app.dependency_overrides[current_user] = lambda: USER
    client = TestClient(app)
    assert client.put("/v1/settings", json={"valuable_threshold": 39}).status_code == 422
    assert client.put("/v1/settings", json={"valuable_threshold": "NaN"}).status_code == 422
    assert (
        client.put(
            "/v1/settings", json={"valuable_threshold": 75, "user_id": str(OTHER)}
        ).status_code
        == 422
    )
    response = client.put("/v1/settings", json={"valuable_threshold": 75})
    assert response.status_code == 200
    service.update_settings.assert_awaited_once_with(USER, Decimal(75), None)


def test_non_admin_cannot_change_another_accounts_budget() -> None:
    service = create_autospec(ProcessingService, instance=True)
    accounts = create_autospec(AccountService, instance=True)
    accounts.is_admin.return_value = False
    app = create_app(Settings(demo_mode=True))
    app.state.processing = service
    app.state.accounts = accounts
    response = TestClient(app).put(f"/v1/admin/accounts/{OTHER}/usage", json={"limit_usd": 100})
    assert response.status_code == 403
    service.update_budget.assert_not_awaited()


def test_admin_can_set_zero_budget_without_content_access() -> None:
    service = create_autospec(ProcessingService, instance=True)
    service.update_budget.return_value = UsageSummary(
        month="2026-10-01",
        spent_usd=Decimal("0.012345"),
        reserved_usd=Decimal(0),
        limit_usd=Decimal(0),
        remaining_usd=Decimal(0),
        resets_at="2026-11-01T00:00:00Z",
    )
    accounts = create_autospec(AccountService, instance=True)
    accounts.is_admin.return_value = True
    app = create_app(Settings(demo_mode=True))
    app.state.processing = service
    app.state.accounts = accounts
    response = TestClient(app).put(f"/v1/admin/accounts/{OTHER}/usage", json={"limit_usd": "0"})
    assert response.status_code == 200
    assert response.json()["spent_usd"] == "0.012345"
    service.update_budget.assert_awaited_once_with(OTHER, Decimal(0))
    service.inbox.assert_not_awaited()
    service.assessment.assert_not_awaited()


def test_foreign_pasted_content_returns_not_found() -> None:
    service = create_autospec(ProcessingService, instance=True)
    service.paste.return_value = None
    app = create_app(Settings(demo_mode=True))
    app.state.processing = service
    app.dependency_overrides[current_user] = lambda: USER
    content = "Readable complete article evidence. " * 10
    response = TestClient(app).put(f"/v1/items/{OTHER}/content", json={"text": content})
    assert response.status_code == 404
    service.paste.assert_awaited_once_with(USER, content, OTHER)
    service.assessment.assert_not_awaited()


def test_anonymous_usage_and_activity_fail_before_service_access() -> None:
    app = create_app(Settings())
    client = TestClient(app)
    assert client.get("/v1/usage").status_code == 401
    assert client.get("/v1/activity").status_code == 401


def test_progress_snapshot_queries_only_the_verified_owner() -> None:
    import asyncio
    from unittest.mock import AsyncMock, Mock

    from fastapi import Request

    from linksifty.api.processing import activity

    async def run() -> None:
        service = create_autospec(ProcessingService, instance=True)
        service.inbox.return_value = []
        service.usage.return_value = UsageSummary(
            month="2026-10-01",
            spent_usd=Decimal("0.01"),
            reserved_usd=Decimal(0),
            limit_usd=Decimal(10),
            remaining_usd=Decimal("9.99"),
            resets_at="2026-11-01T00:00:00Z",
        )
        request = Mock(spec=Request)
        request.app.state.processing = service
        request.app.state.accounts = None
        request.is_disconnected = AsyncMock(return_value=False)
        response = await activity(cast(Request, request), USER)
        iterator = response.body_iterator
        snapshot = await anext(iterator)
        assert "event: snapshot" in snapshot
        assert "0.01" in snapshot
        service.inbox.assert_awaited_once_with(USER)
        service.usage.assert_awaited_once_with(USER)
        await iterator.aclose()

    asyncio.run(run())


def test_account_rejection_ends_stream_before_private_snapshot() -> None:
    import asyncio
    from unittest.mock import AsyncMock, Mock

    from fastapi import Request

    from linksifty.api.processing import activity

    async def run() -> None:
        service = create_autospec(ProcessingService, instance=True)
        accounts = create_autospec(AccountService, instance=True)
        accounts.can_access.return_value = False
        request = Mock(spec=Request)
        request.app.state.processing = service
        request.app.state.accounts = accounts
        request.is_disconnected = AsyncMock(return_value=False)
        response = await activity(cast(Request, request), USER)
        frame = await anext(response.body_iterator)
        assert frame == "event: denied\ndata: {}\n\n"
        accounts.can_access.assert_awaited_once_with(USER)
        service.inbox.assert_not_awaited()
        service.usage.assert_not_awaited()
        await response.body_iterator.aclose()

    asyncio.run(run())


def test_search_submission_is_not_silently_enabled_without_configuration() -> None:
    from linksifty.application.item_service import ItemService

    app = create_app(Settings(demo_mode=False))
    app.state.items = create_autospec(ItemService, instance=True)
    app.state.processing = None
    app.dependency_overrides[current_user] = lambda: USER
    client = TestClient(app)
    assert client.get("/v1/capabilities").json()["web_search"] is False
    response = client.post(
        "/v1/items", json={"sources": [{"url": "https://public.example"}], "web_search": True}
    )
    assert response.status_code == 503
    app.state.items.submit.assert_not_awaited()


def test_duplicate_submission_returns_conflict_without_waking_worker() -> None:
    from linksifty.application.item_contracts import DuplicateSubmission
    from linksifty.application.item_service import ItemService

    app = create_app(Settings(demo_mode=False))
    items = create_autospec(ItemService, instance=True)
    items.submit.side_effect = DuplicateSubmission()
    worker = create_autospec(ProcessingService, instance=True)
    app.state.items = items
    app.state.processing = worker
    app.dependency_overrides[current_user] = lambda: USER
    client = TestClient(app)
    response = client.post("/v1/items", json={"sources": [{"url": "https://example.test/article"}]})
    assert response.status_code == 409
    assert "existing item" in response.json()["detail"]
    worker.wake.assert_not_called()


def test_settings_save_the_entire_validated_owner_rubric() -> None:
    from linksifty.application.processing_contracts import RubricConfig

    service = create_autospec(ProcessingService, instance=True)
    rules = RubricConfig.default().model_dump(mode="json")
    rules["criteria"][0]["weight"] = 10
    rules["criteria"][0]["description"] = "Nowa perspektywa"
    rubric = RubricConfig.model_validate(rules)
    service.update_settings.return_value = UserSettings(
        valuable_threshold=Decimal(75), rubric=rubric
    )
    app = create_app(Settings(demo_mode=True))
    app.state.processing = service
    app.dependency_overrides[current_user] = lambda: USER
    client = TestClient(app)
    response = client.put("/v1/settings", json={"valuable_threshold": 75, "rubric": rules})
    assert response.status_code == 200
    assert response.json()["rubric"] == rules
    service.update_settings.assert_awaited_once_with(USER, Decimal(75), rubric)
    service.wake.assert_not_called()
    for weight in (0, 11, True, 1.5):
        rules["criteria"][0]["weight"] = weight
        assert (
            client.put("/v1/settings", json={"valuable_threshold": 75, "rubric": rules}).status_code
            == 422
        )
    service.update_settings.assert_awaited_once()
