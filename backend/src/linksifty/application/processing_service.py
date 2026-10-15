"""Resume bounded owner-scoped work independently of the browser connection."""

import asyncio
import hashlib
import logging
from collections.abc import Awaitable, Callable
from contextlib import nullcontext
from decimal import Decimal
from urllib.parse import unquote, urlparse
from uuid import UUID, uuid4

from linksifty.application.item_contracts import ItemRecord
from linksifty.application.processing_contracts import (
    AssessmentProvider,
    AssessmentView,
    CitationView,
    EvidenceSource,
    ProcessingJob,
    ProcessingStore,
    ResearchContext,
    Telemetry,
    UsageSummary,
    UserSettings,
)
from linksifty.application.research_contracts import SearchProvider
from linksifty.domain.acquisition import FetchResult
from linksifty.domain.content_policy import ContentReadiness, evaluate_content
from linksifty.domain.models import AssessmentDraft, Criterion, CriterionName
from linksifty.domain.scoring import complete_assessment

_logger = logging.getLogger(__name__)
HEARTBEAT_SECONDS = 15


class ProcessingService:
    def __init__(
        self,
        store: ProcessingStore,
        provider: AssessmentProvider | None,
        fetch: Callable[[str], Awaitable[FetchResult]],
        *,
        search: SearchProvider | None = None,
        search_price: Decimal = Decimal(0),
        telemetry: Telemetry | None = None,
    ) -> None:
        self._search = search
        self._search_price = search_price
        self._telemetry = telemetry
        self._store = store
        self._provider = provider
        self._fetch = fetch
        self._tasks: dict[UUID, asyncio.Task[None]] = {}
        self._slots = asyncio.Semaphore(3)

    @property
    def search_available(self) -> bool:
        return self._search is not None and self._search_price > 0

    @property
    def search_price(self) -> Decimal:
        return self._search_price

    async def submit_search(self, user_id: UUID, urls: list[str]) -> list[ItemRecord]:
        if not self.search_available:
            raise ValueError("Web search is not configured")
        records = await self._store.submit_search(user_id, urls)
        self.wake(user_id)
        return records

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
        operation = asyncio.create_task(self._traced_process(job))
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

    async def _traced_process(self, job: ProcessingJob) -> None:
        with self._telemetry.scope("processing", str(job.id)) if self._telemetry else nullcontext():
            await self.process(job)

    async def research(self, job: ProcessingJob, text: str) -> ResearchContext:
        if job.search_context is not None:
            return job.search_context
        context = ResearchContext(status="unavailable")
        if job.search_reservation_id is not None:
            context.status = "uncertain"  # A previous search may have been billed; never resend.
        elif self.search_available and self._search is not None:
            reservation = await self._store.reserve_search(job, self._search_price)
            if reservation is None:
                context.status = "budget_exhausted"
            else:
                job.search_reservation_id = reservation.id
                if not await self._store.stage(job, "searching_sources"):
                    raise RuntimeError("lease_lost")
                slug = unquote(urlparse(job.original_url or "").path.rsplit("/", 1)[-1])
                query = " ".join(slug.replace("-", " ").replace("_", " ").split())[:250]
                response = await self._search.search(query or " ".join(text.split())[:250])
                if not response.confirmed:
                    context.status = "uncertain"
                else:
                    await self._store.settle(job.user_id, reservation.id, self._search_price)
                    context.status = "no_sources"
                    domains = {urlparse(job.original_url or "").hostname}
                    hashes = {hashlib.sha256(" ".join(text.split()).encode()).hexdigest()}
                    attempts = 0
                    for url in response.urls:
                        try:
                            parsed = urlparse(url)
                            host = parsed.hostname
                        except ValueError:
                            continue
                        if (
                            host is None
                            or host in domains
                            or parsed.scheme not in {"http", "https"}
                        ):
                            continue
                        domains.add(host)
                        if attempts == 5:
                            break
                        attempts += 1
                        if not await self._store.stage(job, "checking_sources"):
                            raise RuntimeError("lease_lost")
                        fetched = await self._fetch(url)
                        if (
                            fetched.text is None
                            or evaluate_content(fetched.text, fetched=True).readiness
                            is not ContentReadiness.READY
                        ):
                            continue
                        # A bounded passage, not a claim to hold the complete external page.
                        passage = fetched.text[:12000]
                        digest = hashlib.sha256(" ".join(fetched.text.split()).encode()).hexdigest()
                        if digest in hashes:
                            continue
                        hashes.add(digest)
                        context.sources.append(
                            EvidenceSource(id=str(uuid4()), url=url, text=passage)
                        )
                    if context.sources:
                        context.status = "ready"
        if not await self._store.save_research(job, context):
            raise RuntimeError("lease_lost")
        job.search_context = context
        return context

    async def process(self, job: ProcessingJob) -> None:
        provider = self._provider
        if provider is None:
            await self._store.stage(job, "not_configured", "failed")
            return
        text = job.source_text
        if text is None:
            if not await self._store.stage(job, "fetching"):
                return
            with (
                self._telemetry.scope("source.fetch", str(job.id))
                if self._telemetry
                else nullcontext()
            ):
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
        research = ResearchContext()
        if job.web_search:
            with (
                self._telemetry.scope("web.research", str(job.id))
                if self._telemetry
                else nullcontext()
            ):
                research = await self.research(job, text)
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
            result = (
                await provider.assess(text, sources=research.sources)
                if research.sources
                else await provider.assess(text)
            )
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
        source_texts = {"primary": text, **{source.id: source.text for source in research.sources}}
        source_urls = {
            "primary": job.original_url,
            **{source.id: source.url for source in research.sources},
        }
        citations: list[CitationView] = []
        criteria: list[Criterion] = []
        for criterion in result.assessment.criteria:
            start = source_texts.get(criterion.source_id, "").find(criterion.excerpt)
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
                    source_url=source_urls.get(criterion.source_id),
                    source_id=criterion.source_id,
                )
            )
            independently_cited = bool(research.sources) and criterion.source_id != "primary"
            if (
                criterion.name is CriterionName.INDEPENDENT_CORROBORATION
                and not independently_cited
            ):
                criterion.score = 1
                criterion.rationale = (
                    "Independent corroboration was not established. " + criterion.rationale
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
