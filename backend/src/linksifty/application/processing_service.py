"""Resume bounded owner-scoped work independently of the browser connection."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from decimal import Decimal
from uuid import UUID, uuid4

from linksifty.application.item_contracts import ItemRecord
from linksifty.application.processing_contracts import (
    AssessmentProvider,
    AssessmentView,
    CitationView,
    ProcessingJob,
    ProcessingStore,
    UsageSummary,
    UserSettings,
)
from linksifty.domain.acquisition import FetchResult
from linksifty.domain.content_policy import ContentReadiness, evaluate_content
from linksifty.domain.models import AssessmentDraft, Criterion
from linksifty.domain.scoring import complete_assessment

_logger = logging.getLogger(__name__)
HEARTBEAT_SECONDS = 15


class ProcessingService:
    def __init__(
        self,
        store: ProcessingStore,
        provider: AssessmentProvider | None,
        fetch: Callable[[str], Awaitable[FetchResult]],
    ) -> None:
        self._store = store
        self._provider = provider
        self._fetch = fetch
        self._tasks: dict[UUID, asyncio.Task[None]] = {}
        self._slots = asyncio.Semaphore(3)

    async def usage(self, user_id: UUID) -> UsageSummary:
        return await self._store.usage(user_id)

    async def settings(self, user_id: UUID) -> UserSettings:
        return await self._store.settings(user_id)

    async def update_threshold(self, user_id: UUID, threshold: Decimal) -> UserSettings:
        return await self._store.update_threshold(user_id, threshold)

    async def update_budget(self, user_id: UUID, limit: Decimal) -> UsageSummary:
        return await self._store.update_budget(user_id, limit)

    async def inbox(self, user_id: UUID) -> list[ItemRecord]:
        self.wake(user_id)
        return await self._store.inbox(user_id)

    async def paste(
        self, user_id: UUID, text: str, item_id: UUID | None = None
    ) -> ItemRecord | None:
        record = await self._store.paste(user_id, text, item_id)
        if record is not None:
            self.wake(user_id)
        return record

    async def resume(self, user_id: UUID, item_id: UUID) -> ItemRecord | None:
        record = await self._store.resume(user_id, item_id)
        if record is not None:
            self.wake(user_id)
        return record

    async def assessment(self, user_id: UUID, item_id: UUID) -> AssessmentView | None:
        await self._store.cleanup(user_id)
        return await self._store.assessment(user_id, item_id)

    def wake(self, user_id: UUID) -> None:
        task = self._tasks.get(user_id)
        if task is None or task.done():
            self._tasks[user_id] = asyncio.create_task(self._run(user_id))

    async def close(self) -> None:
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()

    async def _run(self, user_id: UUID) -> None:
        try:
            async with self._slots:
                await self._store.cleanup(user_id)
                if self._provider is not None:
                    for reservation in await self._store.orphaned_reservations(user_id):
                        cost = await self._provider.reconcile(reservation.generation_id)
                        if cost is not None:
                            await self._store.settle(user_id, reservation.id, cost)
                for _ in range(5):
                    job = await self._store.claim(user_id)
                    if job is None:
                        break
                    await self._execute(job)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Do not log provider payloads, source content or tokens.
            _logger.warning("processing_interrupted; persisted lease/reservation retained")
        finally:
            self._tasks.pop(user_id, None)

    async def _execute(self, job: ProcessingJob) -> None:
        operation = asyncio.create_task(self.process(job))
        try:
            while True:
                done, _ = await asyncio.wait({operation}, timeout=HEARTBEAT_SECONDS)
                if done:
                    await operation
                    return
                if not await self._store.heartbeat(job):
                    return  # Lost ownership: never publish from this execution.
        finally:
            if not operation.done():
                operation.cancel()
            await asyncio.gather(operation, return_exceptions=True)

    async def process(self, job: ProcessingJob) -> None:
        provider = self._provider
        if provider is None:
            await self._store.stage(job, "not_configured", "failed")
            return
        text = job.source_text
        if text is None:
            if not await self._store.stage(job, "fetching"):
                return
            fetched = await self._fetch(job.original_url or "")
            if fetched.text is None:
                await self._store.stage(
                    job, str(fetched.failure or "unavailable"), "awaiting_manual_content"
                )
                return
            if not await self._store.stage(job, "checking_content"):
                return
            evaluation = evaluate_content(fetched.text, fetched=True)
            if evaluation.readiness is not ContentReadiness.READY:
                await self._store.stage(
                    job, str(evaluation.reason or "incomplete"), "awaiting_manual_content"
                )
                return
            text = fetched.text
            if not await self._store.save_source(job, text):
                return
        if evaluate_content(text, fetched=False).readiness is not ContentReadiness.READY:
            await self._store.stage(job, "too_short", "awaiting_manual_content")
            return
        result = job.model_result
        if job.reservation_id is not None:
            # Any existing reservation means the paid attempt may already have been sent.
            if job.reservation_state == "reserved":
                cost = result.cost if result is not None else None
                if cost is None and job.generation_id:
                    cost = await provider.reconcile(job.generation_id)
                if cost is None:
                    await self._store.stage(job, "cost_unknown", "failed")
                    return
                await self._store.settle(job.user_id, job.reservation_id, cost)
            if result is None:
                await self._store.stage(job, "invalid_model_output", "failed")
                return
        else:
            if not await self._store.stage(job, "waiting_analysis"):
                return
            try:
                amount = provider.estimate(text)
            except ValueError:
                await self._store.stage(job, "not_configured", "failed")
                return
            reservation = await self._store.reserve(job, amount)
            if reservation is None:
                return
            job.reservation_id = reservation.id
            job.threshold_snapshot = reservation.threshold_snapshot
            if not await self._store.stage(job, "analyzing"):
                return
            result = await provider.assess(text)
            recorded = await self._store.record_result(job, result)
            if result.cost is not None:
                await self._store.settle(job.user_id, reservation.id, result.cost)
            if not recorded:
                return
            if result.cost is None:
                await self._store.stage(job, "cost_unknown", "failed")
                return
        if result.assessment is None:
            await self._store.stage(job, "invalid_model_output", "failed")
            return
        if job.threshold_snapshot is None:
            await self._store.stage(job, "invalid_model_output", "failed")
            return
        citations: list[CitationView] = []
        criteria: list[Criterion] = []
        for criterion in result.assessment.criteria:
            start = text.find(criterion.excerpt)
            if start < 0:
                await self._store.stage(job, "invalid_model_output", "failed")
                return
            identifier = uuid4()
            citations.append(
                CitationView(
                    id=identifier,
                    excerpt=criterion.excerpt,
                    start_position=start,
                    end_position=start + len(criterion.excerpt),
                    source_url=job.original_url,
                )
            )
            criteria.append(
                Criterion(criterion.name, criterion.score, criterion.rationale, (str(identifier),))
            )
        assessment = complete_assessment(
            AssessmentDraft(result.assessment.note, tuple(criteria)), float(job.threshold_snapshot)
        )
        view = AssessmentView(
            note=assessment.note,
            criteria=[
                {
                    "name": criterion.name.value,
                    "score": criterion.score,
                    "rationale": criterion.rationale,
                    "citation_ids": list(criterion.citation_ids),
                }
                for criterion in assessment.criteria
            ],
            score=assessment.score,
            verdict=assessment.verdict.value,
            threshold_snapshot=assessment.threshold_snapshot,
            citations=citations,
        )
        if await self._store.stage(job, "saving"):
            await self._store.complete(job, view)
