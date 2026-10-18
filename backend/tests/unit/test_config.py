import pytest
from fastapi.testclient import TestClient

from linksifty.config import Settings
from linksifty.main import create_app


def test_settings_report_incomplete_when_server_secrets_are_missing() -> None:
    settings = Settings(supabase_url="https://db.example")

    assert settings.is_configured is False


def test_health_endpoint_needs_no_provider_call() -> None:
    client = TestClient(create_app(Settings.for_test()))

    assert client.get("/health").json() == {"status": "ok"}


def test_x_reads_require_explicit_operator_enablement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_API_BEARER_TOKEN", "test-x-token")
    monkeypatch.delenv("X_API_READS_ENABLED", raising=False)
    assert not Settings.from_environment().x_api_reads_enabled
    monkeypatch.setenv("X_API_READS_ENABLED", "true")
    assert Settings.from_environment().x_api_reads_enabled
