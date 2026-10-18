"""FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langfuse import Langfuse
from pydantic import BaseModel, Field, HttpUrl, ValidationError

from linksifty.api import accounts, admin, chat, items, processing
from linksifty.api.auth import CurrentUser
from linksifty.application.account_contracts import AccountService
from linksifty.application.chat_service import ChatService
from linksifty.application.item_contracts import DuplicateSubmission, ItemRecord
from linksifty.application.item_service import ItemService
from linksifty.application.processing_service import ProcessingService
from linksifty.config import Settings
from linksifty.infrastructure.brave_client import BraveSearch
from linksifty.infrastructure.chat_repository import ChatRepository
from linksifty.infrastructure.http_fetcher import fetch_public_text
from linksifty.infrastructure.langfuse_telemetry import LangfuseTelemetry
from linksifty.infrastructure.openrouter_client import OpenRouterClient
from linksifty.infrastructure.openrouter_images import OpenRouterImageReader
from linksifty.infrastructure.processing_repository import ProcessingRepository
from linksifty.infrastructure.resend_client import ResendApprovalMailer
from linksifty.infrastructure.supabase_auth import SupabaseAuthenticator
from linksifty.infrastructure.supabase_repository import (
    AccountPolicyViolation,
    RepositoryUnavailable,
    SupabaseRepository,
)
from linksifty.infrastructure.x_adapter import XAdapter


class SourceInput(BaseModel):
    url: HttpUrl


class SubmitItems(BaseModel):
    sources: list[SourceInput] = Field(min_length=1, max_length=5)
    web_search: bool = False


class ItemResponse(BaseModel):
    id: str
    title: str
    status: str
    score: float | None = None
    verdict: str | None = None
    processing_stage: str = "queued"
    failure_reason: str | None = None
    original_url: str | None = None
    updated_at: datetime | None = None
    worker_active: bool | None = None


class InboxResponse(BaseModel):
    items: list[ItemResponse]
    demo: bool = False


def _response(item: ItemRecord) -> ItemResponse:
    return ItemResponse(
        id=str(item.id),
        title=item.title or item.original_url or "Pasted content",
        status=item.status,
        score=item.score,
        verdict=item.verdict,
        processing_stage=item.processing_stage,
        failure_reason=item.failure_reason,
        original_url=item.original_url,
        updated_at=item.updated_at,
        worker_active=item.worker_active,
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
        telemetry = LangfuseTelemetry()
        if (
            configuration.langfuse_enabled
            and configuration.langfuse_public_key
            and configuration.langfuse_secret_key
        ):
            try:
                telemetry = LangfuseTelemetry(
                    Langfuse(
                        public_key=configuration.langfuse_public_key,
                        secret_key=configuration.langfuse_secret_key,
                        base_url=configuration.langfuse_base_url,
                        timeout=3,
                    ),
                    secrets=tuple(
                        value
                        for value in (
                            configuration.supabase_anon_key,
                            configuration.supabase_service_role_key,
                            configuration.openrouter_api_key,
                            configuration.brave_search_api_key,
                            configuration.langfuse_public_key,
                            configuration.langfuse_secret_key,
                            configuration.resend_api_key,
                            configuration.x_api_bearer_token,
                        )
                        if value
                    ),
                )
            except Exception:
                logging.getLogger(__name__).warning("telemetry_unavailable")
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
                processing_repository = ProcessingRepository(
                    configuration.supabase_url, configuration.supabase_service_role_key, client
                )
                provider = (
                    OpenRouterClient(
                        configuration.openrouter_api_key,
                        configuration.openrouter_model,
                        client,
                        telemetry,
                    )
                    if configuration.openrouter_api_key
                    else None
                )
                application.state.processing = ProcessingService(
                    processing_repository,
                    provider,
                    fetch_public_text,
                    x_fetch=XAdapter(configuration.x_api_bearer_token, transport=transport).fetch
                    if configuration.x_api_reads_enabled and configuration.x_api_bearer_token
                    else None,
                    image_reader=OpenRouterImageReader(
                        configuration.openrouter_api_key, configuration.openrouter_model, client
                    )
                    if configuration.openrouter_api_key
                    else None,
                    search=BraveSearch(
                        configuration.brave_search_api_key, client, telemetry=telemetry
                    )
                    if configuration.brave_search_api_key
                    else None,
                    search_price=configuration.brave_search_price,
                    telemetry=telemetry,
                )
                application.state.chat = ChatService(
                    ChatRepository(
                        configuration.supabase_url, configuration.supabase_service_role_key, client
                    ),
                    provider,
                    fetch_public_text,
                    search=BraveSearch(
                        configuration.brave_search_api_key, client, telemetry=telemetry
                    )
                    if configuration.brave_search_api_key
                    else None,
                    search_price=configuration.brave_search_price,
                )
            try:
                yield
            finally:
                processor: ProcessingService | None = application.state.processing
                if processor is not None:
                    await processor.close()
                await asyncio.to_thread(telemetry.close)

    app = FastAPI(title="Linksifty", lifespan=lifespan)
    app.include_router(accounts.router)
    app.include_router(admin.router)
    app.include_router(processing.router)
    app.include_router(items.router)
    app.include_router(chat.router)
    app.state.settings = configuration
    app.state.authenticator = None
    app.state.items = None
    app.state.accounts = None
    app.state.processing = None
    app.state.chat = None

    @app.exception_handler(ValidationError)
    async def invalid_persistence(request: Request, error: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": "Persistence temporarily unavailable"}
        )

    @app.exception_handler(RepositoryUnavailable)
    async def persistence_error(request: Request, error: RepositoryUnavailable) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": "Persistence temporarily unavailable"}
        )

    @app.exception_handler(DuplicateSubmission)
    async def duplicate_submission(request: Request, error: DuplicateSubmission) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": (
                    "One or more links are already in your queue or repeated in this batch. "
                    "Use the existing item to read or resume analysis."
                )
            },
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
        processor: ProcessingService | None = app.state.processing
        records = await processor.inbox(user_id) if processor else await service.inbox(user_id)
        return InboxResponse(items=[_response(item) for item in records])

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

    @app.get("/v1/capabilities")
    async def capabilities(user_id: CurrentUser) -> dict[str, object]:
        processor: ProcessingService | None = app.state.processing
        return {
            "web_search": processor.search_available if processor else False,
            "search_price_usd": str(processor.search_price)
            if processor and processor.search_available
            else None,
        }

    @app.post("/v1/items", response_model=InboxResponse, status_code=202)
    async def submit_items(submission: SubmitItems, user_id: CurrentUser) -> InboxResponse:
        """Persist items and queued jobs together before acknowledging submission."""
        if not configuration.demo_mode:
            service: ItemService | None = app.state.items
            if service is None:
                raise HTTPException(503, "Persistence is not configured")
            if submission.web_search:
                processor = app.state.processing
                if processor is None or not processor.search_available:
                    raise HTTPException(503, "Brave search is not configured")
                records = await processor.submit_search(
                    user_id, [str(source.url) for source in submission.sources]
                )
            else:
                records = await service.submit(
                    user_id, [str(source.url) for source in submission.sources]
                )
            processor = app.state.processing
            if processor is not None:
                processor.wake(user_id)
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
