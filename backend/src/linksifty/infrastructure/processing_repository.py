"""Supabase processing RPCs, always scoped to the verified owner."""

from decimal import Decimal
from uuid import UUID

from linksifty.application.item_contracts import ItemRecord
from linksifty.application.processing_contracts import (
    AssessmentView,
    CitationView,
    ModelResult,
    PendingReservation,
    ProcessingJob,
    ResearchContext,
    Reservation,
    RubricConfig,
    UsageSummary,
    UserSettings,
)
from linksifty.infrastructure.supabase_repository import RepositoryUnavailable, SupabaseRepository


class ProcessingRepository(SupabaseRepository):
    async def reserve_selection(self, job: ProcessingJob, amount: Decimal) -> UUID | None:
        rows = await self._rpc(
            "reserve_source_selection", job.user_id, **self._job_values(job), p_amount=str(amount)
        )
        return UUID(str(rows[0]["id"])) if rows else None

    async def record_selection_generation(
        self, job: ProcessingJob, reservation_id: UUID, generation_id: str | None
    ) -> None:
        await self._rpc(
            "record_source_selection_generation",
            job.user_id,
            p_job_id=str(job.id),
            p_reservation=str(reservation_id),
            p_generation=generation_id,
        )

    async def reserve_images(self, job: ProcessingJob, amount: Decimal) -> UUID | None:
        rows = await self._rpc(
            "reserve_image_reading", job.user_id, **self._job_values(job), p_amount=str(amount)
        )
        return UUID(str(rows[0]["id"])) if rows else None

    async def record_image_generation(
        self, job: ProcessingJob, reservation_id: UUID, generation_id: str | None
    ) -> None:
        await self._rpc(
            "record_image_generation",
            job.user_id,
            p_job_id=str(job.id),
            p_reservation=str(reservation_id),
            p_generation=generation_id,
        )

    async def begin_x_fetch(self, job: ProcessingJob) -> bool:
        rows = await self._rpc("begin_x_fetch", job.user_id, **self._job_values(job))
        return bool(rows and rows[0].get("admitted") is True)

    async def submit_search(self, user_id: UUID, urls: list[str]) -> list[ItemRecord]:
        return [
            ItemRecord.model_validate(row)
            for row in await self._rpc("submit_search_items", user_id, p_urls=urls)
        ]

    async def reserve_search(self, job: ProcessingJob, amount: Decimal) -> Reservation | None:
        rows = await self._rpc(
            "reserve_web_search", job.user_id, **self._job_values(job), p_amount=str(amount)
        )
        return Reservation.model_validate(rows[0]) if rows else None

    async def save_research(self, job: ProcessingJob, context: ResearchContext) -> bool:
        return bool(
            await self._rpc(
                "save_research_context",
                job.user_id,
                **self._job_values(job),
                p_context=context.model_dump(mode="json"),
            )
        )

    async def orphaned_reservations(self, user_id: UUID) -> list[PendingReservation]:
        rows = await self._profile_request(
            "GET",
            "usage_reservations",
            params={
                "user_id": f"eq.{user_id}",
                "or": "(job_id.is.null,purpose.in.(image_extraction,source_selection))",
                "state": "eq.reserved",
                "generation_id": "not.is.null",
                "select": "id,generation_id",
                "limit": "5",
            },
        )
        return [PendingReservation.model_validate(row) for row in rows]

    async def _rpc(self, name: str, user_id: UUID, **values: object) -> list[dict[str, object]]:
        return await self._profile_request(
            "POST", f"rpc/{name}", payload={"p_user_id": str(user_id), **values}
        )

    @staticmethod
    def _first(rows: list[dict[str, object]]) -> dict[str, object]:
        if not rows:
            raise RepositoryUnavailable("Persistence temporarily unavailable")
        return rows[0]

    async def usage(self, user_id: UUID) -> UsageSummary:
        return UsageSummary.model_validate(
            self._first(await self._rpc("get_usage_summary", user_id))
        )

    async def settings(self, user_id: UUID) -> UserSettings:
        return UserSettings.model_validate(
            self._first(await self._rpc("get_user_settings", user_id))
        )

    async def update_settings(
        self, user_id: UUID, threshold: Decimal, rubric: RubricConfig | None
    ) -> UserSettings:
        return UserSettings.model_validate(
            self._first(
                await self._rpc(
                    "update_user_assessment_settings",
                    user_id,
                    p_threshold=str(threshold),
                    p_rubric=rubric.model_dump(mode="json") if rubric is not None else None,
                )
            )
        )

    async def update_budget(self, user_id: UUID, limit: Decimal) -> UsageSummary:
        await self._rpc("set_user_budget", user_id, p_limit=str(limit))
        return await self.usage(user_id)

    async def inbox(self, user_id: UUID) -> list[ItemRecord]:
        return [
            ItemRecord.model_validate(row)
            for row in await self._rpc("list_processing_items", user_id)
        ]

    async def claim(self, user_id: UUID) -> ProcessingJob | None:
        rows = await self._rpc("claim_processing_job", user_id)
        return ProcessingJob.model_validate(rows[0]) if rows else None

    @staticmethod
    def _job_values(job: ProcessingJob) -> dict[str, object]:
        return {"p_job_id": str(job.id), "p_lease": str(job.lease_token)}

    async def heartbeat(self, job: ProcessingJob) -> bool:
        return bool(
            await self._rpc("heartbeat_processing_job", job.user_id, **self._job_values(job))
        )

    async def stage(self, job: ProcessingJob, stage: str, status: str = "processing") -> bool:
        return bool(
            await self._rpc(
                "set_processing_stage",
                job.user_id,
                **self._job_values(job),
                p_stage=stage,
                p_status=status,
            )
        )

    async def save_source(self, job: ProcessingJob, text: str) -> bool:
        return bool(
            await self._rpc("save_job_source", job.user_id, **self._job_values(job), p_text=text)
        )

    async def reserve(self, job: ProcessingJob, amount: Decimal) -> Reservation | None:
        rows = await self._rpc(
            "reserve_analysis", job.user_id, **self._job_values(job), p_amount=str(amount)
        )
        return Reservation.model_validate(rows[0]) if rows else None

    async def record_result(self, job: ProcessingJob, result: ModelResult) -> bool:
        return bool(
            await self._rpc(
                "record_model_result",
                job.user_id,
                **self._job_values(job),
                p_reservation=str(job.reservation_id),
                p_result=result.model_dump(mode="json"),
                p_generation=result.generation_id,
            )
        )

    async def settle(self, user_id: UUID, reservation_id: UUID, cost: Decimal) -> None:
        await self._rpc(
            "settle_analysis", user_id, p_reservation=str(reservation_id), p_cost=str(cost)
        )

    async def complete(self, job: ProcessingJob, assessment: AssessmentView) -> bool:
        return bool(
            await self._rpc(
                "complete_processing_job",
                job.user_id,
                **self._job_values(job),
                p_assessment=assessment.model_dump(mode="json", exclude={"citations"}),
                p_citations=[citation.model_dump(mode="json") for citation in assessment.citations],
            )
        )

    async def paste(
        self, user_id: UUID, text: str, item_id: UUID | None = None
    ) -> ItemRecord | None:
        rows = await self._rpc(
            "paste_item_content", user_id, p_text=text, p_item_id=str(item_id) if item_id else None
        )
        return ItemRecord.model_validate(rows[0]) if rows else None

    async def resume(self, user_id: UUID, item_id: UUID) -> ItemRecord | None:
        rows = await self._rpc("resume_processing_item", user_id, p_item_id=str(item_id))
        return ItemRecord.model_validate(rows[0]) if rows else None

    async def assessment(self, user_id: UUID, item_id: UUID) -> AssessmentView | None:
        rows = await self._profile_request(
            "GET",
            "assessments",
            params={"user_id": f"eq.{user_id}", "item_id": f"eq.{item_id}", "limit": "1"},
        )
        if not rows:
            return None
        assessment_id = str(rows[0]["id"])
        citations = await self._profile_request(
            "GET",
            "citations",
            params={
                "user_id": f"eq.{user_id}",
                "assessment_id": f"eq.{assessment_id}",
                "order": "start_position.asc",
            },
        )
        jobs = await self._profile_request(
            "GET",
            "jobs",
            params={
                "user_id": f"eq.{user_id}",
                "item_id": f"eq.{item_id}",
                "select": "search_context",
                "limit": "1",
            },
        )
        context = (
            ResearchContext.model_validate(jobs[0].get("search_context") or {})
            if jobs
            else ResearchContext()
        )
        return AssessmentView.model_validate(
            {
                "research_status": context.status,
                "research_sources": [
                    {"id": source.id, "url": source.url} for source in context.sources
                ],
                **rows[0],
                "citations": [CitationView.model_validate(citation) for citation in citations],
            }
        )

    async def cleanup(self, user_id: UUID) -> None:
        await self._rpc("cleanup_processing_data", user_id)
