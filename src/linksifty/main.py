"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from linksifty.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the HTTP application without contacting external providers."""
    app = FastAPI(title="Linksifty")
    app.state.settings = settings or Settings.from_environment()

    @app.get("/health")
    def health() -> dict[str, str]:
        """Return a liveness response safe for unauthenticated monitoring."""
        return {"status": "ok"}

    return app


app = create_app()
