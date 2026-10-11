"""Configuration read from server-side environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Server configuration; values are never exposed through HTTP responses."""

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    openrouter_api_key: str | None = None
    x_api_bearer_token: str | None = None

    @property
    def is_configured(self) -> bool:
        """Return whether the minimum non-optional API configuration exists."""
        return all(
            (
                self.supabase_url,
                self.supabase_anon_key,
                self.supabase_service_role_key,
                self.openrouter_api_key,
            )
        )

    @classmethod
    def from_environment(cls) -> Settings:
        """Build settings without loading files or logging secret values."""
        return cls(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY"),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            x_api_bearer_token=os.getenv("X_API_BEARER_TOKEN"),
        )

    @classmethod
    def for_test(cls) -> Settings:
        """Return complete non-secret placeholders for local unit tests."""
        return cls(
            supabase_url="https://supabase.example",
            supabase_anon_key="test-anon-key",
            supabase_service_role_key="test-service-role-key",
            openrouter_api_key="test-openrouter-key",
        )
