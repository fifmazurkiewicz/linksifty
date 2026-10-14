"""Configuration read from server-side environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Settings:
    """Server configuration; values are never exposed through HTTP responses."""

    supabase_url: str | None = None
    supabase_anon_key: str | None = field(default=None, repr=False)
    supabase_service_role_key: str | None = field(default=None, repr=False)
    openrouter_api_key: str | None = field(default=None, repr=False)
    resend_api_key: str | None = field(default=None, repr=False)
    resend_from_email: str | None = None
    x_api_bearer_token: str | None = field(default=None, repr=False)
    demo_mode: bool = False
    frontend_origin: str | None = None
    linksifty_admin_email: str | None = None

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
            resend_api_key=os.getenv("RESEND_API_KEY"),
            resend_from_email=os.getenv("RESEND_FROM_EMAIL"),
            x_api_bearer_token=os.getenv("X_API_BEARER_TOKEN"),
            demo_mode=os.getenv("LINKSIFTY_DEMO_MODE", "false").lower() == "true",
            frontend_origin=os.getenv("FRONTEND_ORIGIN"),
            linksifty_admin_email=os.getenv("LINKSIFTY_ADMIN_EMAIL"),
        )

    @classmethod
    def for_test(cls) -> Settings:
        """Return complete non-secret placeholders for local unit tests."""
        return cls(
            supabase_url="https://supabase.example",
            supabase_anon_key="test-anon-key",
            supabase_service_role_key="test-service-role-key",
            openrouter_api_key="test-openrouter-key",
            demo_mode=True,
        )
