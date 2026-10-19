"""Transport for settings, usage, recovery and authenticated progress snapshots."""

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from linksifty.api.auth import CurrentIdentity, CurrentUser
from linksifty.application.account_contracts import AccountService
from linksifty.application.item_contracts import ItemRecord
from linksifty.application.processing_contracts import (
    AssessmentView,
    RubricConfig,
    TitleGenerationError,
    UsageSummary,
    UserSettings,
)
from linksifty.application.processing_service import ProcessingService
from linksifty.infrastructure.supabase_repository import RepositoryUnavailable

router = APIRouter()
_logger = logging.getLogger(__name__)


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rubric: RubricConfig | None = None
    valuable_threshold: Decimal = Field(
        ge=40, le=100, max_digits=5, decimal_places=2, allow_inf_nan=False
    )


class BudgetUpdate(BaseModel):
    limit_usd: Decimal = Field(
        ge=0, le=1000000, max_digits=15, decimal_places=8, allow_inf_nan=False
    )


class TitleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: bool = Field(strict=True)

    @field_validator("confirmed")
    @classmethod
    def require_confirmation(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Confirm monthly AI budget use")
        return value


class TitleResponse(BaseModel):
    title: str


class ResumeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allow_partial_preview: bool = Field(default=False, strict=True)


class ContentInput(BaseModel):
    text: str = Field(min_length=200, max_length=100000)

    @field_validator("text")
    @classmethod
    def complete_text(cls, text: str) -> str:
        if (
            "\x00" in text
            or len(" ".join(text.split())) < 200
            or len(text.encode("utf-8")) > 100000
        ):
            raise ValueError("Paste between 200 characters and 100 KB of readable content")
        return text


def _service(request: Request) -> ProcessingService:
    service: ProcessingService | None = request.app.state.processing
    if service is None:
        raise HTTPException(503, "Processing and usage are not configured")
    return service


def _require_admin(request: Request, identity: CurrentIdentity) -> None:
    accounts: AccountService | None = request.app.state.accounts
    if accounts is None or not accounts.is_admin(identity):
        raise HTTPException(403, "Administrator access required")


@router.get("/v1/settings")
async def get_settings(request: Request, user_id: CurrentUser) -> UserSettings:
    return await _service(request).settings(user_id)


@router.put("/v1/settings")
async def update_settings(
    update: SettingsUpdate, request: Request, user_id: CurrentUser
) -> UserSettings:
    return await _service(request).update_settings(
        user_id, update.valuable_threshold, update.rubric
    )


@router.get("/v1/usage")
async def get_usage(request: Request, user_id: CurrentUser) -> UsageSummary:
    return await _service(request).usage(user_id)


@router.get("/v1/admin/accounts/{account_id}/usage")
async def get_account_usage(
    account_id: UUID, request: Request, identity: CurrentIdentity
) -> UsageSummary:
    _require_admin(request, identity)
    return await _service(request).usage(account_id)


@router.put("/v1/admin/accounts/{account_id}/usage")
async def update_account_budget(
    account_id: UUID, update: BudgetUpdate, request: Request, identity: CurrentIdentity
) -> UsageSummary:
    _require_admin(request, identity)
    return await _service(request).update_budget(account_id, update.limit_usd)


@router.post("/v1/items/paste", status_code=202)
async def submit_paste(content: ContentInput, request: Request, user_id: CurrentUser) -> ItemRecord:
    record = await _service(request).paste(user_id, content.text)
    if record is None:
        raise HTTPException(409, "Content could not be submitted")
    return record


@router.put("/v1/items/{item_id}/content", status_code=202)
async def paste_content(
    item_id: UUID, content: ContentInput, request: Request, user_id: CurrentUser
) -> ItemRecord:
    record = await _service(request).paste(user_id, content.text, item_id)
    if record is None:
        raise HTTPException(404, "Link is not available for pasted content")
    return record


@router.post("/v1/items/{item_id}/resume", status_code=202)
async def resume_item(
    item_id: UUID, request: Request, user_id: CurrentUser, consent: ResumeInput | None = None
) -> ItemRecord:
    record = await _service(request).resume(
        user_id,
        item_id,
        **({"allow_partial_preview": True} if consent and consent.allow_partial_preview else {}),
    )
    if record is None:
        raise HTTPException(
            409, "This link cannot be safely resumed; unresolved calls remain reserved"
        )
    return record


@router.get("/v1/items/{item_id}/assessment")
async def get_assessment(item_id: UUID, request: Request, user_id: CurrentUser) -> AssessmentView:
    assessment = await _service(request).assessment(user_id, item_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not available")
    return assessment


@router.post("/v1/items/{item_id}/title")
async def generate_title(
    item_id: UUID, content: TitleInput, request: Request, user_id: CurrentUser
) -> TitleResponse:
    try:
        return TitleResponse(title=await _service(request).generate_title(user_id, item_id))
    except TitleGenerationError as error:
        raise HTTPException(409, str(error)) from error


@router.get("/v1/activity")
async def activity(request: Request, user_id: CurrentUser) -> StreamingResponse:
    service = _service(request)

    # Bounded connection renews authentication on reconnect; no bearer in URL/EventSource.
    async def events() -> AsyncIterator[str]:
        deadline = time.monotonic() + 50
        previous = ""
        while time.monotonic() < deadline and not await request.is_disconnected():
            # Recheck account rejection during the stream, not just at connection time.
            try:
                accounts: AccountService | None = request.app.state.accounts
                if accounts is not None:
                    if not await accounts.can_access(user_id):
                        yield "event: denied\ndata: {}\n\n"
                        return
                items = await service.inbox(user_id)
                usage = await service.usage(user_id)
            except RepositoryUnavailable:
                # Headers are already sent; end the stream so the client reconnects.
                _logger.warning("activity_interrupted; persistence temporarily unavailable")
                yield ": temporarily unavailable\n\n"
                return
            snapshot = json.dumps(
                {
                    "items": [item.model_dump(mode="json") for item in items],
                    "usage": usage.model_dump(mode="json"),
                },
                ensure_ascii=False,
            )
            if snapshot != previous:
                yield f"event: snapshot\ndata: {snapshot}\n\n"
                previous = snapshot
            else:
                yield ": heartbeat\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no"},
    )
