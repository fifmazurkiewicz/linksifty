"""Supabase chat persistence; owner predicates accompany every content operation."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from linksifty.application.chat_contracts import (
    CallSlot,
    ChatClaim,
    ChatContext,
    ChatParagraph,
    ChatTurn,
)
from linksifty.application.processing_contracts import EvidenceSource, ResearchContext
from linksifty.infrastructure.processing_repository import ProcessingRepository


class ChatRepository(ProcessingRepository):
    async def context(self, user_id: UUID, item_id: UUID) -> ChatContext | None:
        items = await self._profile_request(
            "GET",
            "items",
            params={
                "id": f"eq.{item_id}",
                "user_id": f"eq.{user_id}",
                "status": "eq.completed",
                "expires_at": f"gt.{datetime.now(UTC).isoformat()}",
                "select": "id,original_url",
                "limit": "1",
            },
        )
        if not items:
            return None
        sources = await self._profile_request(
            "GET",
            "source_contents",
            params={
                "item_id": f"eq.{item_id}",
                "user_id": f"eq.{user_id}",
                "select": "content",
                "limit": "1",
            },
        )
        if not sources or not isinstance(sources[0].get("content"), str):
            return None
        text = str(sources[0]["content"])
        if not text.strip():
            return None
        assessment = await self.assessment(user_id, item_id)
        if assessment is None:
            return None
        jobs = await self._profile_request(
            "GET",
            "jobs",
            params={
                "item_id": f"eq.{item_id}",
                "user_id": f"eq.{user_id}",
                "select": "search_context",
                "limit": "1",
            },
        )
        research = (
            ResearchContext.model_validate(jobs[0].get("search_context") or {})
            if jobs
            else ResearchContext()
        )
        url = items[0].get("original_url")
        return ChatContext(
            text=text,
            url=url if isinstance(url, str) else None,
            assessment=assessment,
            sources=research.sources,
        )

    async def history(self, user_id: UUID, item_id: UUID) -> list[ChatTurn]:
        return [
            ChatTurn.model_validate(row)
            for row in await self._rpc(
                "list_chat_turns",
                user_id,
                p_item_id=str(item_id),
            )
        ]

    async def claim_turn(
        self, user_id: UUID, item_id: UUID, request_id: UUID, question: str
    ) -> ChatClaim | None:
        rows = await self._rpc(
            "begin_chat_turn",
            user_id,
            p_item_id=str(item_id),
            p_request_id=str(request_id),
            p_question=question,
        )
        return ChatClaim.model_validate(rows[0]) if rows else None

    async def reserve_call(
        self, user_id: UUID, turn: ChatTurn, slot: CallSlot, amount: Decimal
    ) -> UUID | None:
        rows = await self._rpc(
            "reserve_chat_call", user_id, p_turn_id=str(turn.id), p_slot=slot, p_amount=str(amount)
        )
        return UUID(str(rows[0]["id"])) if rows else None

    async def record_call(
        self, user_id: UUID, reservation_id: UUID, generation_id: str | None
    ) -> None:
        await self._rpc(
            "record_chat_generation",
            user_id,
            p_reservation=str(reservation_id),
            p_generation=generation_id,
        )

    async def finish(
        self,
        user_id: UUID,
        turn: ChatTurn,
        *,
        status: Literal["completed", "failed"],
        answer: list[ChatParagraph],
        insufficient: bool,
        search_status: str,
        sources: list[EvidenceSource],
        error: str | None,
    ) -> ChatTurn | None:
        rows = await self._rpc(
            "finish_chat_turn",
            user_id,
            p_turn_id=str(turn.id),
            p_result={
                "status": status,
                "answer": [p.model_dump(mode="json") for p in answer],
                "insufficient": insufficient,
                "search_status": search_status,
                "error": error,
                "sources": [s.model_dump(mode="json") for s in sources],
            },
        )
        return ChatTurn.model_validate(rows[0]) if rows else None
