"""Configuration read from server-side environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class Settings:
    """Server configuration; values are never exposed through HTTP responses."""

    supabase_url: str | None = None
    supabase_anon_key: str | None = field(default=None, repr=False)
    supabase_service_role_key: str | None = field(default=None, repr=False)
    openrouter_api_key: str | None = field(default=None, repr=False)
    openrouter_model: str = "openai/gpt-4o-mini"
    brave_search_api_key: str | None = field(default=None, repr=False)
    brave_search_price: Decimal = Decimal(0)
    langfuse_enabled: bool = False
    langfuse_public_key: str | None = field(default=None, repr=False)
    langfuse_secret_key: str | None = field(default=None, repr=False)
    langfuse_base_url: str = "https://cloud.langfuse.com"
    resend_api_key: str | None = field(default=None, repr=False)
    resend_from_email: str | None = None
    x_api_bearer_token: str | None = field(default=None, repr=False)
    x_api_reads_enabled: bool = False
    x_api_debug: bool = False
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
        try:
            search_price = Decimal(os.getenv("BRAVE_SEARCH_PRICE_PER_REQUEST_USD", "0"))
            if not search_price.is_finite() or not 0 <= search_price <= 1000000:
                search_price = Decimal(0)
        except InvalidOperation:
            search_price = Decimal(0)
        return cls(
            brave_search_api_key=os.getenv("BRAVE_SEARCH_API_KEY"),
            brave_search_price=search_price,
            langfuse_enabled=os.getenv("LANGFUSE_ENABLED", "false").lower() == "true",
            langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            langfuse_base_url=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY"),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            resend_api_key=os.getenv("RESEND_API_KEY"),
            resend_from_email=os.getenv("RESEND_FROM_EMAIL"),
            x_api_bearer_token=os.getenv("X_API_BEARER_TOKEN"),
            x_api_reads_enabled=os.getenv("X_API_READS_ENABLED", "false").lower() == "true",
            x_api_debug=os.getenv("X_API_DEBUG", "false").lower() == "true",
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
