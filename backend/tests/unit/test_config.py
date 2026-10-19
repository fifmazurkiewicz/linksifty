from dataclasses import replace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from linksifty.config import Settings
from linksifty.main import create_app


def test_settings_report_incomplete_when_server_secrets_are_missing() -> None:
    settings = Settings(supabase_url="https://db.example")

    assert settings.is_configured is False


def test_chat_model_defaults_to_sonnet_independently_of_assessment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_CHAT_MODEL", raising=False)
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    settings = Settings.from_environment()
    assert settings.openrouter_chat_model == "anthropic/claude-sonnet-5.5"
    assert settings.openrouter_model == "openai/gpt-4o-mini"
    monkeypatch.setenv("OPENROUTER_CHAT_MODEL", "openai/gpt-4o-mini")
    assert Settings.from_environment().openrouter_chat_model == "openai/gpt-4o-mini"


def test_startup_wires_the_independent_chat_model() -> None:
    settings = Settings.for_test()
    with patch("linksifty.main.OpenRouterClient") as provider:
        with TestClient(create_app(settings)):
            pass
    assert provider.call_args.kwargs["chat_model"] == "anthropic/claude-sonnet-5.5"
    assert provider.call_args.args[1] == "openai/gpt-4o-mini"


def test_health_endpoint_needs_no_provider_call() -> None:
    client = TestClient(create_app(Settings.for_test()))

    assert client.get("/health").json() == {"status": "ok"}


def test_x_reads_require_explicit_operator_enablement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_API_BEARER_TOKEN", "test-x-token")
    monkeypatch.delenv("X_API_READS_ENABLED", raising=False)
    assert not Settings.from_environment().x_api_reads_enabled
    monkeypatch.setenv("X_API_READS_ENABLED", "true")
    assert Settings.from_environment().x_api_reads_enabled


def test_x_debug_requires_explicit_operator_enablement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("X_API_DEBUG", raising=False)
    assert not Settings.from_environment().x_api_debug
    monkeypatch.setenv("X_API_DEBUG", "true")
    assert Settings.from_environment().x_api_debug


def test_startup_wires_x_debug_and_configured_secrets_without_langfuse() -> None:
    settings = replace(
        Settings.for_test(),
        x_api_bearer_token="test-x-token",
        x_api_reads_enabled=True,
        x_api_debug=True,
    )
    with patch("linksifty.main.XAdapter") as adapter:
        with TestClient(create_app(settings)):
            pass
    assert adapter.call_args.kwargs["debug"] is True
    assert "test-x-token" in adapter.call_args.kwargs["secrets"]
    assert "test-service-role-key" in adapter.call_args.kwargs["secrets"]


def test_legacy_image_model_setting_does_not_activate_a_reader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_IMAGE_MODEL", raising=False)
    assert Settings.from_environment().openrouter_image_model == "openai/gpt-4.1-mini"
    monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "openai/gpt-4o-mini")
    assert Settings.from_environment().openrouter_image_model == "openai/gpt-4o-mini"
    with patch("linksifty.infrastructure.openrouter_images.OpenRouterImageReader") as reader:
        with TestClient(create_app(Settings.for_test())):
            pass
    reader.assert_not_called()
