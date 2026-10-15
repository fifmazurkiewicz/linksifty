import asyncio
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

from linksifty.application.processing_contracts import (
    AssessmentProvider,
    ModelResult,
    ProcessingJob,
    ProcessingStore,
    Reservation,
    SourceAssessment,
    SourceCriterion,
)
from linksifty.application.processing_service import ProcessingService
from linksifty.domain.acquisition import FetchFailure, FetchResult
from linksifty.domain.models import CriterionName

TEXT = "Complete source evidence with a practical reproducible example. " * 10


def test_completed_result_uses_reserved_threshold_and_real_citations() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.record_result.return_value = True
        store.reserve.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=Decimal(75)
        )
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.estimate.return_value = Decimal("0.02")
        provider.assess.return_value = ModelResult(
            cost=Decimal("0.00012"),
            generation_id="gen-test",
            assessment=SourceAssessment(
                note="Source note.",
                criteria=[
                    SourceCriterion(
                        name=name,
                        score=3,
                        rationale="Supported by source.",
                        excerpt="Complete source evidence",
                    )
                    for name in CriterionName
                ],
            ),
        )
        job = ProcessingJob(
            id=uuid4(), item_id=uuid4(), user_id=uuid4(), lease_token=uuid4(), source_text=TEXT
        )
        fetch = AsyncMock()
        await ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), fetch
        ).process(job)
        store.settle.assert_awaited_once_with(job.user_id, job.reservation_id, Decimal("0.00012"))
        result = store.complete.call_args.args[1]
        assert result.threshold_snapshot == 75
        assert result.verdict == "to_review"
        assert len(result.citations) == 8
        for citation in result.citations:
            assert TEXT[citation.start_position : citation.end_position] == citation.excerpt
        fetch.assert_not_awaited()

    asyncio.run(run())


def test_partial_fetch_never_reserves_or_calls_model() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        provider = create_autospec(AssessmentProvider, instance=True)
        fetch = AsyncMock(return_value=FetchResult(failure=FetchFailure.PARTIAL))
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            original_url="https://example.com",
        )
        await ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), fetch
        ).process(job)
        provider.assess.assert_not_awaited()
        store.reserve.assert_not_awaited()
        store.complete.assert_not_awaited()
        store.stage.assert_awaited_with(job, "partial_content", "awaiting_manual_content")

    asyncio.run(run())


def test_existing_uncertain_reservation_never_repeats_paid_request() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.reconcile.return_value = None
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            source_text=TEXT,
            reservation_id=uuid4(),
            reservation_state="reserved",
            generation_id="gen-unknown",
        )
        await ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), AsyncMock()
        ).process(job)
        provider.reconcile.assert_awaited_once_with("gen-unknown")
        provider.assess.assert_not_awaited()
        store.settle.assert_not_awaited()
        store.stage.assert_awaited_with(job, "cost_unknown", "failed")

    asyncio.run(run())


def test_lost_lease_accounts_cost_but_cannot_publish_result() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.record_result.return_value = False
        store.reserve.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=Decimal(60)
        )
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.estimate.return_value = Decimal("0.02")
        provider.assess.return_value = ModelResult(cost=Decimal("0.001"), generation_id="gen-stale")
        job = ProcessingJob(
            id=uuid4(), item_id=uuid4(), user_id=uuid4(), lease_token=uuid4(), source_text=TEXT
        )
        await ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), AsyncMock()
        ).process(job)
        store.settle.assert_awaited_once()
        store.complete.assert_not_awaited()

    asyncio.run(run())


def test_crash_after_saved_result_settles_then_publishes_without_repeating_inference() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.reconcile.return_value = Decimal("0.00012")
        result = ModelResult(
            generation_id="gen-recovered",
            assessment=SourceAssessment(
                note="Recovered source note.",
                criteria=[
                    SourceCriterion(
                        name=name,
                        score=3,
                        rationale="Supported by source.",
                        excerpt="Complete source evidence",
                    )
                    for name in CriterionName
                ],
            ),
        )
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            source_text=TEXT,
            reservation_id=uuid4(),
            reservation_state="reserved",
            generation_id="gen-recovered",
            threshold_snapshot=Decimal(75),
            model_result=result,
        )
        await ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), AsyncMock()
        ).process(job)
        provider.assess.assert_not_awaited()
        store.reserve.assert_not_awaited()
        store.settle.assert_awaited_once_with(job.user_id, job.reservation_id, Decimal("0.00012"))
        store.complete.assert_awaited_once()
        assert store.complete.call_args.args[1].threshold_snapshot == 75

    asyncio.run(run())


def test_orphaned_reservation_is_reconciled_after_source_cleanup() -> None:
    from linksifty.application.processing_contracts import PendingReservation

    async def run() -> None:
        user_id = uuid4()
        reservation = PendingReservation(id=uuid4(), generation_id="gen-expired-source")
        store = create_autospec(ProcessingStore, instance=True)
        store.orphaned_reservations.return_value = [reservation]
        store.claim.return_value = None
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.reconcile.return_value = Decimal("0.002")
        service = ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), AsyncMock()
        )
        await service._run(user_id)
        store.cleanup.assert_awaited_once_with(user_id)
        store.settle.assert_awaited_once_with(user_id, reservation.id, Decimal("0.002"))
        provider.assess.assert_not_awaited()

    asyncio.run(run())


def test_lost_heartbeat_cancels_execution_without_retry(monkeypatch: object) -> None:
    import pytest

    patch = cast(pytest.MonkeyPatch, monkeypatch)
    patch.setattr("linksifty.application.processing_service.HEARTBEAT_SECONDS", 0.001)

    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.heartbeat.return_value = False
        service = ProcessingService(cast(ProcessingStore, store), None, AsyncMock())
        interrupted = asyncio.Event()

        async def blocked(job: ProcessingJob) -> None:
            try:
                await asyncio.Event().wait()
            finally:
                interrupted.set()

        service.process = blocked
        job = ProcessingJob(id=uuid4(), item_id=uuid4(), user_id=uuid4(), lease_token=uuid4())
        await service._execute(job)
        assert interrupted.is_set()
        store.heartbeat.assert_awaited_once_with(job)
        store.complete.assert_not_awaited()

    asyncio.run(run())


def test_crash_after_charge_before_job_commit_does_not_send_model_again() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        provider = create_autospec(AssessmentProvider, instance=True)
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            source_text=TEXT,
            reservation_id=uuid4(),
            reservation_state="settled",
            actual_usd=Decimal("0.001"),
            threshold_snapshot=Decimal(60),
        )
        await ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), AsyncMock()
        ).process(job)
        provider.assess.assert_not_awaited()
        store.reserve.assert_not_awaited()
        store.settle.assert_not_awaited()
        store.stage.assert_awaited_with(job, "invalid_model_output", "failed")

    asyncio.run(run())


def test_saved_actual_cost_recovers_without_a_generation_lookup() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.reconcile.return_value = None
        result = ModelResult(
            cost=Decimal("0.004"),
            assessment=SourceAssessment(
                note="Saved result with known cost.",
                criteria=[
                    SourceCriterion(
                        name=name,
                        score=3,
                        rationale="Supported.",
                        excerpt="Complete source evidence",
                    )
                    for name in CriterionName
                ],
            ),
        )
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            source_text=TEXT,
            reservation_id=uuid4(),
            reservation_state="reserved",
            model_result=result,
            threshold_snapshot=Decimal(60),
        )
        await ProcessingService(
            cast(ProcessingStore, store), cast(AssessmentProvider, provider), AsyncMock()
        ).process(job)
        store.settle.assert_awaited_once_with(job.user_id, job.reservation_id, Decimal("0.004"))
        store.complete.assert_awaited_once()
        provider.reconcile.assert_not_awaited()
        provider.assess.assert_not_awaited()

    asyncio.run(run())
