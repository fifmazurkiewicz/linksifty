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
                        with (
                            self._telemetry.scope("orphan.reconciliation", str(reservation.id))
                            if self._telemetry
                            else nullcontext()
                        ):
                            self._event("model.recovery", reason="orphaned_reservation")
                            cost = await self._provider.reconcile(reservation.generation_id)
                            self._event(
                                "model.reconciled", cost_usd=str(cost) if cost is not None else None
                            )
                            if cost is not None:
                                await self._store.settle(user_id, reservation.id, cost)
                                self._event(
                                    "budget.settled", provider="openrouter", amount_usd=str(cost)
                                )
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

    def _event(self, name: str, **details: object) -> None:
        if self._telemetry:
            self._telemetry.event(name, details)

    async def _stage(self, job: ProcessingJob, stage: str, status: str = "processing") -> bool:
        self._event("stage.requested", stage=stage, status=status)
        saved = await self._store.stage(job, stage, status)
        self._event("stage.persisted", stage=stage, status=status, saved=saved)
        return saved

    async def _execute(self, job: ProcessingJob) -> None:
        with self._telemetry.scope("processing", str(job.id)) if self._telemetry else nullcontext():
            self._event(
                "processing.started",
                item_id=str(job.item_id),
                web_search=job.web_search,
                source_cached=job.source_text is not None,
                url=job.original_url,
            )
            operation = asyncio.create_task(self.process(job))
            outcome = "returned"
            try:
                while True:
                    done, _ = await asyncio.wait({operation}, timeout=HEARTBEAT_SECONDS)
                    if done:
                        await operation
                        return
                    owned = await self._store.heartbeat(job)
                    self._event("lease.heartbeat", owned=owned)
                    if not owned:
                        outcome = "lease_lost"
                        return
            except asyncio.CancelledError:
                outcome = "cancelled"
                raise
            except Exception:
                outcome = "interrupted"
                raise
            finally:
                if not operation.done():
                    operation.cancel()
                await asyncio.gather(operation, return_exceptions=True)
                self._event("processing.finished", outcome=outcome)

    async def research(self, job: ProcessingJob, text: str) -> ResearchContext:
        if job.search_context is not None:
            self._event(
                "search.reused",
                status=job.search_context.status,
                sources=[source.model_dump() for source in job.search_context.sources],
            )
            return job.search_context
        context = ResearchContext(status="unavailable")
        if job.search_reservation_id is not None:
            self._event("search.skipped", reason="previous_uncertain_request")
            context.status = "uncertain"  # A previous search may have been billed; never resend.
        elif self.search_available and self._search is not None:
            self._event("budget.reserving", provider="brave", amount_usd=str(self._search_price))
            reservation = await self._store.reserve_search(job, self._search_price)
            self._event("budget.reserved", provider="brave", admitted=reservation is not None)
            if reservation is None:
                context.status = "budget_exhausted"
            else:
                job.search_reservation_id = reservation.id
                if not await self._stage(job, "searching_sources"):
                    raise RuntimeError("lease_lost")
                slug = unquote(urlparse(job.original_url or "").path.rsplit("/", 1)[-1])
                query = " ".join(slug.replace("-", " ").replace("_", " ").split())[:250]
                query = query or " ".join(text.split())[:250]
                self._event("search.request", query=query)
                with (
                    self._telemetry.scope("brave.search", str(job.id))
                    if self._telemetry
                    else nullcontext()
                ):
                    response = await self._search.search(query)
                self._event(
                    "search.response", confirmed=response.confirmed, urls=list(response.urls)
                )
                if not response.confirmed:
                    context.status = "uncertain"
                else:
                    await self._store.settle(job.user_id, reservation.id, self._search_price)
                    self._event(
                        "budget.settled", provider="brave", amount_usd=str(self._search_price)
                    )
                    context.status = "no_sources"
                    domains = {urlparse(job.original_url or "").hostname}
                    hashes = {hashlib.sha256(" ".join(text.split()).encode()).hexdigest()}
                    attempts = 0
                    for url in response.urls:
                        try:
                            parsed = urlparse(url)
                            host = parsed.hostname
                        except ValueError:
                            self._event("source.skipped", url=url, reason="invalid_url")
                            continue
                        if (
                            host is None
                            or host in domains
                            or parsed.scheme not in {"http", "https"}
                        ):
                            self._event(
                                "source.skipped",
                                url=url,
                                reason="duplicate_host_or_unsupported_url",
                            )
                            continue
                        domains.add(host)
                        if attempts == 5:
                            self._event("source.skipped", reason="fetch_limit_reached")
                            break
                        attempts += 1
                        if not await self._stage(job, "checking_sources"):
                            raise RuntimeError("lease_lost")
                        self._event("source.fetch_requested", url=url, attempt=attempts)
                        with (
                            self._telemetry.scope("source.additional_fetch", str(job.id))
                            if self._telemetry
                            else nullcontext()
                        ):
                            fetched = await self._fetch(url)
                        self._event(
                            "source.fetched",
                            url=url,
                            text=fetched.text[:12000] if fetched.text else None,
                            failure=fetched.failure,
                        )
                        if (
                            fetched.text is None
                            or evaluate_content(fetched.text, fetched=True).readiness
                            is not ContentReadiness.READY
                        ):
                            self._event(
                                "source.skipped", url=url, reason="unreadable_or_incomplete"
                            )
                            continue
                        # A bounded passage, not a claim to hold the complete external page.
                        passage = fetched.text[:12000]
                        digest = hashlib.sha256(" ".join(fetched.text.split()).encode()).hexdigest()
                        if digest in hashes:
                            self._event("source.skipped", url=url, reason="duplicate_content")
                            continue
                        hashes.add(digest)
                        context.sources.append(
                            EvidenceSource(id=str(uuid4()), url=url, text=passage)
                        )
                    if context.sources:
                        context.status = "ready"
        else:
            self._event("search.skipped", reason="not_configured")
        self._event(
            "search.finished",
            status=context.status,
            sources=[source.model_dump() for source in context.sources],
        )
        if not await self._store.save_research(job, context):
            raise RuntimeError("lease_lost")
        self._event("research.saved", status=context.status)
        job.search_context = context
        return context

    async def process(self, job: ProcessingJob) -> None:
        provider = self._provider
        if provider is None:
            await self._stage(job, "not_configured", "failed")
            return
        text = job.source_text
        if text is None:
            if not await self._stage(job, "fetching"):
                return
            with (
                self._telemetry.scope("source.fetch", str(job.id))
                if self._telemetry
                else nullcontext()
            ):
                fetched = await self._fetch(job.original_url or "")
            self._event(
                "source.fetched", url=job.original_url, text=fetched.text, failure=fetched.failure
            )
            if fetched.text is None:
                await self._stage(
                    job, str(fetched.failure or "unavailable"), "awaiting_manual_content"
                )
                return
            if not await self._stage(job, "checking_content"):
                return
            evaluation = evaluate_content(fetched.text, fetched=True)
            self._event(
                "source.validated", readiness=evaluation.readiness, reason=evaluation.reason
            )
            if evaluation.readiness is not ContentReadiness.READY:
                await self._stage(
                    job, str(evaluation.reason or "incomplete"), "awaiting_manual_content"
                )
                return
            text = fetched.text
            saved = await self._store.save_source(job, text)
            self._event("source.saved", saved=saved, characters=len(text))
            if not saved:
                return
        else:
            self._event("source.reused", text=text)
        if evaluate_content(text, fetched=False).readiness is not ContentReadiness.READY:
            await self._stage(job, "too_short", "awaiting_manual_content")
            return
        research = ResearchContext()
        if job.web_search:
            with (
                self._telemetry.scope("web.research", str(job.id))
                if self._telemetry
                else nullcontext()
            ):
                research = await self.research(job, text)
        else:
            self._event("search.skipped", reason="not_requested")
        result = job.model_result
        if job.reservation_id is not None:
            self._event(
                "model.recovery",
                reservation_state=job.reservation_state,
                result_cached=result is not None,
            )
            # Any existing reservation means the paid attempt may already have been sent.
            if job.reservation_state == "reserved":
                cost = result.cost if result is not None else None
                if cost is None and job.generation_id:
                    with (
                        self._telemetry.scope("model.reconcile", str(job.id))
                        if self._telemetry
                        else nullcontext()
                    ):
                        cost = await provider.reconcile(job.generation_id)
                    self._event(
                        "model.reconciled", cost_usd=str(cost) if cost is not None else None
                    )
                if cost is None:
                    await self._stage(job, "cost_unknown", "failed")
                    return
                await self._store.settle(job.user_id, job.reservation_id, cost)
                self._event("budget.settled", provider="openrouter", amount_usd=str(cost))
            if result is None:
                await self._stage(job, "invalid_model_output", "failed")
                return
        else:
            if not await self._stage(job, "waiting_analysis"):
                return
            try:
                amount = provider.estimate(text)
            except ValueError:
                await self._stage(job, "not_configured", "failed")
                return
            self._event("budget.reserving", provider="openrouter", amount_usd=str(amount))
            reservation = await self._store.reserve(job, amount)
            self._event("budget.reserved", provider="openrouter", admitted=reservation is not None)
            if reservation is None:
                return
            job.reservation_id = reservation.id
            job.threshold_snapshot = reservation.threshold_snapshot
            if not await self._stage(job, "analyzing"):
                return
            result = (
                await provider.assess(text, sources=research.sources)
                if research.sources
                else await provider.assess(text)
            )
            self._event("model.result", result=result.model_dump(mode="json"))
            recorded = await self._store.record_result(job, result)
            self._event("model.result_saved", saved=recorded)
            if result.cost is not None:
                await self._store.settle(job.user_id, reservation.id, result.cost)
                self._event("budget.settled", provider="openrouter", amount_usd=str(result.cost))
            if not recorded:
                return
            if result.cost is None:
                await self._stage(job, "cost_unknown", "failed")
                return
        if result.assessment is None:
            await self._stage(job, "invalid_model_output", "failed")
            return
        if job.threshold_snapshot is None:
            await self._stage(job, "invalid_model_output", "failed")
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
            self._event(
                "citation.offset_checked",
                source_id=criterion.source_id,
                criterion=criterion.name.value,
                start=start,
            )
            if start < 0:
                await self._stage(job, "invalid_model_output", "failed")
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
        if await self._stage(job, "saving"):
            saved = await self._store.complete(job, view)
            self._event("assessment.saved", saved=saved, assessment=view.model_dump(mode="json"))
