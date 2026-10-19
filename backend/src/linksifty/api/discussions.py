"""Authenticated, no-store transport for explicit reader-reply loading."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from linksifty.api.auth import CurrentUser
from linksifty.application.discussions import Discussion, DiscussionHistory, DiscussionService

router = APIRouter(prefix="/v1/items/{item_id}/discussions", tags=["discussions"])


class LoadReplies(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(min_length=1, max_length=64)
    consent: bool = Field(strict=True)

    @field_validator("consent")
    @classmethod
    def approved(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Explicit consent to X reads is required")
        return value


def _service(request: Request) -> DiscussionService:
    service: DiscussionService | None = request.app.state.discussions
    if service is None:
        raise HTTPException(503, "Reader comments are not configured")
    return service


def _error(error: ValueError) -> HTTPException:
    if str(error) == "not_found":
        return HTTPException(404, "Discussion source is not available for this account")
    return HTTPException(503, "Reader comments are unavailable for this source")


@router.get("")
async def history(
    item_id: UUID, request: Request, response: Response, user_id: CurrentUser
) -> DiscussionHistory:
    response.headers["Cache-Control"] = "no-store"
    try:
        return await _service(request).history(user_id, item_id)
    except ValueError as error:
        raise _error(error) from error


@router.post("")
async def load(
    item_id: UUID, body: LoadReplies, request: Request, response: Response, user_id: CurrentUser
) -> Discussion:
    response.headers["Cache-Control"] = "no-store"
    try:
        return await _service(request).load(user_id, item_id, body.source_id, consent=body.consent)
    except ValueError as error:
        raise _error(error) from error
