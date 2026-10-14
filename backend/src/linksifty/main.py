"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl

from linksifty.api import accounts, admin
from linksifty.api.auth import CurrentUser
from linksifty.application.account_contracts import AccountService
from linksifty.application.item_contracts import ItemRecord
from linksifty.application.item_service import ItemService
from linksifty.config import Settings
from linksifty.infrastructure.resend_client import ResendApprovalMailer
from linksifty.infrastructure.supabase_auth import SupabaseAuthenticator
from linksifty.infrastructure.supabase_repository import (
    AccountPolicyViolation,
    RepositoryUnavailable,
    SupabaseRepository,
)


class SourceInput(BaseModel):
    url: HttpUrl


class SubmitItems(BaseModel):
    sources: list[SourceInput] = Field(min_length=1, max_length=5)


class ItemResponse(BaseModel):
    id: str
    title: str
    status: str
    score: float | None = None
    verdict: str | None = None


class InboxResponse(BaseModel):
    items: list[ItemResponse]
    demo: bool = False


def _response(item: ItemRecord) -> ItemResponse:
    return ItemResponse(
        id=str(item.id),
        title=item.title or item.original_url or "Pasted content",
        status=item.status,
    )


_DEMO_ITEMS = [
    ItemResponse(
        id="demo-completed",
        title="Why small models are winning practical workloads",
        status="completed",
        score=78,
        verdict="valuable",
    ),
    ItemResponse(
        id="demo-manual-content",
        title="The next wave of AI will change everything",
        status="awaiting_manual_content",
    ),
]


def create_app(
    settings: Settings | None = None, *, transport: httpx.AsyncBaseTransport | None = None
) -> FastAPI:
    """Create the HTTP application without contacting external providers."""
    configuration = settings or Settings.from_environment()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient(transport=transport) as client:
            if configuration.supabase_url and configuration.supabase_anon_key:
                application.state.authenticator = SupabaseAuthenticator(
                    configuration.supabase_url, configuration.supabase_anon_key, client
                )
            if configuration.supabase_url and configuration.supabase_service_role_key:
                repository = SupabaseRepository(
                    configuration.supabase_url, configuration.supabase_service_role_key, client
                )
                application.state.items = ItemService(repository)
                mailer = (
                    ResendApprovalMailer(
                        configuration.resend_api_key,
                        configuration.resend_from_email,
                        client,
                    )
                    if configuration.resend_api_key and configuration.resend_from_email
                    else None
                )
                application.state.accounts = AccountService(
                    repository, configuration.linksifty_admin_email, mailer
                )
            yield

    app = FastAPI(title="Linksifty", lifespan=lifespan)
    app.include_router(accounts.router)
    app.include_router(admin.router)
    app.state.settings = configuration
    app.state.authenticator = None
    app.state.items = None
    app.state.accounts = None

    @app.exception_handler(RepositoryUnavailable)
    async def persistence_error(request: Request, error: RepositoryUnavailable) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": "Persistence temporarily unavailable"}
        )

    @app.exception_handler(AccountPolicyViolation)
    async def account_policy_error(request: Request, error: AccountPolicyViolation) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(error)})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=(
            [configuration.frontend_origin]
            if configuration.frontend_origin
            else ["http://localhost:5173", "http://127.0.0.1:5173"]
        ),
        allow_methods=["GET", "POST", "PATCH", "PUT"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        """Return a liveness response safe for unauthenticated monitoring."""
        return {"status": "ok"}

    @app.get("/v1/items", response_model=InboxResponse)
    async def list_items(user_id: CurrentUser) -> InboxResponse:
        """List records belonging to the verified user."""
        if configuration.demo_mode:
            return InboxResponse(items=_DEMO_ITEMS, demo=True)
        service: ItemService | None = app.state.items
        if service is None:
            raise HTTPException(503, "Persistence is not configured")
        return InboxResponse(items=[_response(item) for item in await service.inbox(user_id)])

    @app.get("/v1/items/{item_id}", response_model=ItemResponse)
    async def get_item(item_id: str, user_id: CurrentUser) -> ItemResponse:
        """Return a record only if it belongs to the verified user."""
        if configuration.demo_mode:
            for item in _DEMO_ITEMS:
                if item.id == item_id:
                    return item
            raise HTTPException(404, "Item not found")
        service: ItemService | None = app.state.items
        if service is None:
            raise HTTPException(503, "Persistence is not configured")
        try:
            identifier = UUID(item_id)
        except ValueError as error:
            raise HTTPException(404, "Item not found") from error
        record = await service.detail(user_id, identifier)
        if record is not None:
            return _response(record)
        raise HTTPException(status_code=404, detail="Item not found")

    @app.post("/v1/items", response_model=InboxResponse, status_code=202)
    async def submit_items(submission: SubmitItems, user_id: CurrentUser) -> InboxResponse:
        """Persist items and queued jobs together before acknowledging submission."""
        if not configuration.demo_mode:
            service: ItemService | None = app.state.items
            if service is None:
                raise HTTPException(503, "Persistence is not configured")
            records = await service.submit(
                user_id, [str(source.url) for source in submission.sources]
            )
            return InboxResponse(items=[_response(item) for item in records])
        return InboxResponse(
            demo=True,
            items=[
                ItemResponse(id=f"demo-queued-{index}", title=str(source.url), status="queued")
                for index, source in enumerate(submission.sources, start=1)
            ],
        )

    return app


app = create_app()
