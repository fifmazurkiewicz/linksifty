"""Confirmed, owner-scoped item deletion transport."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from linksifty.api.auth import CurrentUser
from linksifty.application.item_service import ItemService

router = APIRouter()


class DeleteItems(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_ids: list[UUID] = Field(min_length=1, max_length=50)
    confirmed: bool = Field(strict=True)

    @field_validator("confirmed")
    @classmethod
    def require_confirmation(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Confirm permanent deletion")
        return value

    @field_validator("item_ids")
    @classmethod
    def unique_ids(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Select each link only once")
        return value


class DeletedItems(BaseModel):
    deleted_ids: list[UUID]


@router.post("/v1/items/delete")
async def delete_items(
    deletion: DeleteItems, request: Request, user_id: CurrentUser
) -> DeletedItems:
    service: ItemService | None = request.app.state.items
    if service is None:
        raise HTTPException(503, "Persistence is not configured")
    identifiers = await service.delete(user_id, deletion.item_ids)
    if not identifiers:
        raise HTTPException(404, "One or more selected links are no longer available")
    return DeletedItems(deleted_ids=identifiers)
