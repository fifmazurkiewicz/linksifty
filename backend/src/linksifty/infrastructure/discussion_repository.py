"""Server-only discussion RPCs; the verified owner accompanies every operation."""

from uuid import UUID

from pydantic import TypeAdapter

from linksifty.application.discussions import Discussion, DiscussionClaim, DiscussionResult
from linksifty.infrastructure.processing_repository import ProcessingRepository


class DiscussionRepository(ProcessingRepository):
    async def history(self, user_id: UUID, item_id: UUID) -> list[Discussion] | None:
        rows = await self._rpc("get_item_discussions", user_id, p_item_id=str(item_id))
        return TypeAdapter(list[Discussion]).validate_python(rows[0]["sources"]) if rows else None

    async def begin(self, user_id: UUID, item_id: UUID, source_id: str) -> DiscussionClaim | None:
        rows = await self._rpc(
            "begin_item_discussion", user_id, p_item_id=str(item_id), p_source_id=source_id
        )
        return DiscussionClaim.model_validate(rows[0]) if rows else None

    async def finish(
        self, user_id: UUID, item_id: UUID, attempt_id: UUID, result: DiscussionResult
    ) -> Discussion | None:
        rows = await self._rpc(
            "finish_item_discussion",
            user_id,
            p_item_id=str(item_id),
            p_attempt_id=str(attempt_id),
            p_status=result.status,
            p_replies=[reply.model_dump(mode="json") for reply in result.replies],
        )
        return Discussion.model_validate(rows[0]) if rows else None
