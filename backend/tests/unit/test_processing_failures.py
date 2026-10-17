import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, create_autospec
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

from linksifty.api.auth import current_user
from linksifty.application.account_contracts import AccountService
from linksifty.application.processing_contracts import ProcessingStore, UsageSummary
from linksifty.application.processing_service import ProcessingService
from linksifty.config import Settings
from linksifty.infrastructure.supabase_repository import RepositoryUnavailable
from linksifty.main import create_app

USER = UUID("11111111-1111-4111-8111-111111111111")


def test_worker_failure_identifies_step_and_cause_without_private_data(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)

        async def unavailable(user_id: UUID) -> None:
            try:
                raise httpx.ReadTimeout("synthetic-private-timeout")
            except httpx.ReadTimeout as error:
                raise RepositoryUnavailable("synthetic-private-payload") from error

        store.claim.side_effect = unavailable
        service = ProcessingService(store, None, AsyncMock())
        service.wake(USER)
        await service._tasks[USER]
        assert USER not in service._tasks
        store.claim.assert_awaited_once_with(USER)
        store.reserve.assert_not_awaited()
        store.settle.assert_not_awaited()

    asyncio.run(run())
    assert "operation=claim" in caplog.text
    assert "error_type=RepositoryUnavailable" in caplog.text
    assert "cause_type=ReadTimeout" in caplog.text
    assert "synthetic-private" not in caplog.text
    assert str(USER) not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


@pytest.mark.parametrize("failed_step", ["inbox", "usage", "account"])
def test_database_failure_after_snapshot_ends_stream_for_reconnect(failed_step: str) -> None:
    service = create_autospec(ProcessingService, instance=True)
    service.inbox.return_value = []
    usage = UsageSummary(
        month="2026-10-01",
        spent_usd=Decimal("0.01"),
        reserved_usd=Decimal(0),
        limit_usd=Decimal(10),
        remaining_usd=Decimal("9.99"),
        resets_at="2026-11-01T00:00:00Z",
    )
    service.usage.return_value = usage
    accounts = create_autospec(AccountService, instance=True)
    accounts.can_access.return_value = True
    failed = {
        "inbox": (service.inbox, []),
        "usage": (service.usage, usage),
        "account": (accounts.can_access, True),
    }[failed_step]
    failed[0].side_effect = [failed[1], RepositoryUnavailable("synthetic-private-payload")]
    app = create_app(Settings(demo_mode=True))
    app.state.processing = service
    app.state.accounts = accounts
    app.dependency_overrides[current_user] = lambda: USER

    response = TestClient(app).get("/v1/activity")

    assert response.status_code == 200
    assert response.text.count("event: snapshot") == 1
    assert response.text.endswith(": temporarily unavailable\n\n")
    assert "synthetic-private" not in response.text
    assert "event: denied" not in response.text
    failed[0].assert_awaited_with(USER)
