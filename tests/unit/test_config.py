from fastapi.testclient import TestClient

from linksifty.config import Settings
from linksifty.main import create_app


def test_settings_report_incomplete_when_server_secrets_are_missing() -> None:
    settings = Settings(supabase_url="https://db.example")

    assert settings.is_configured is False


def test_health_endpoint_needs_no_provider_call() -> None:
    client = TestClient(create_app(Settings.for_test()))

    assert client.get("/health").json() == {"status": "ok"}
