"""Authenticated transport for item conversations."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from linksifty.api.auth import CurrentUser
from linksifty.application.chat_contracts import ChatError, ChatHistory, ChatTurn
from linksifty.application.chat_service import ChatService

router = APIRouter(prefix="/v1/items/{item_id}/chat", tags=["chat"])


class ChatQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    question: str = Field(min_length=1, max_length=4000)
    max_searches: Literal[1, 2] = 1

    @field_validator("question")
    @classmethod
    def readable_question(cls, value: str) -> str:
        if not value.strip() or "\x00" in value or len(value.encode()) > 16000:
            raise ValueError("Enter a readable question of at most 4000 characters")
        return value.strip()


def _service(request: Request) -> ChatService:
    service: ChatService | None = request.app.state.chat
    if service is None:
        raise HTTPException(503, "Chat is not configured")
    return service


def _error(error: ChatError) -> HTTPException:
    reason = str(error)
    if reason == "not_found":
        return HTTPException(404, "Chat requires your completed analysis and saved source content")
    if reason in {"busy", "request_conflict"}:
        return HTTPException(
            409, "A question is already running, or this request ID was already used"
        )
    return HTTPException(503, "Chat is temporarily unavailable")


@router.get("")
async def history(
    item_id: UUID, request: Request, response: Response, user_id: CurrentUser
) -> ChatHistory:
    response.headers["Cache-Control"] = "no-store"
    try:
        return await _service(request).history(user_id, item_id)
    except ChatError as error:
        raise _error(error) from error


@router.post("")
async def ask(
    item_id: UUID,
    question: ChatQuestion,
    request: Request,
    response: Response,
    user_id: CurrentUser,
) -> ChatTurn:
    response.headers["Cache-Control"] = "no-store"
    try:
        return await _service(request).ask(
            user_id,
            item_id,
            question.request_id,
            question.question,
            max_searches=question.max_searches,
        )
    except ChatError as error:
        raise _error(error) from error
