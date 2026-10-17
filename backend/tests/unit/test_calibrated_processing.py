import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

from linksifty.application.processing_contracts import (
    AssessmentProvider,
    ModelResult,
    ProcessingJob,
    ProcessingStore,
    Reservation,
    RubricConfig,
    SourceAssessment,
    SourceCriterion,
    SourceHypeSignal,
)
from linksifty.application.processing_service import ProcessingService
from linksifty.domain.models import CriterionName

TEXT = "Official explanation of account rules and limits. " * 20


def saved_model_result(*, legacy: bool = False, hype: bool = False) -> ModelResult:
    return ModelResult(
        cost=Decimal("0.001"),
        assessment=SourceAssessment(
            note="Useful account explanation",
            criteria=[
                SourceCriterion(
                    name=n,
                    score=None if n is CriterionName.REPLICABILITY and not legacy else 5,
                    status="not_applicable"
                    if n is CriterionName.REPLICABILITY and not legacy
                    else "assessed",
                    rationale="Specific account conditions are explained.",
                    excerpt=TEXT[:100],
                )
                for n in CriterionName
            ],
            hype_signals=[
                SourceHypeSignal(
                    rationale="Unqualified guarantee exceeds the supplied evidence.",
                    excerpt=TEXT[:100],
                )
            ]
            if hype
            else [],
        ),
    )


def test_v2_explainer_excludes_na_and_missing_corroboration_and_persists_hype_evidence() -> None:
    async def run(hype: bool) -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.record_result.return_value = True
        store.reserve.return_value = Reservation(
            id=uuid4(), state="reserved", threshold_snapshot=60
        )
        provider = create_autospec(AssessmentProvider, instance=True)
        provider.estimate.return_value = Decimal("0.15")
        provider.assess.return_value = saved_model_result(hype=hype)
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            source_text=TEXT,
            original_url="https://www.gov.pl/example",
        )
        await ProcessingService(store, provider, AsyncMock()).process(job)
        result = store.complete.call_args.args[1]
        assert result.score == 100
        assert result.verdict == ("hype" if hype else "valuable")
        assert result.criteria[4]["status"] == "not_applicable"
        assert result.criteria[5]["status"] == "not_verified"
        assert result.criteria[5]["score"] is None
        assert len(result.hype_signals) == int(hype)
        if hype:
            identifier = result.hype_signals[0]["citation_ids"][0]
            citation = next(c for c in result.citations if str(c.id) == identifier)
            assert citation.source_id == "primary"
            assert TEXT[citation.start_position : citation.end_position] == citation.excerpt
        assert provider.assess.call_args.kwargs["primary_url"] == job.original_url

    asyncio.run(run(False))
    asyncio.run(run(True))


def test_pre_migration_cached_result_keeps_legacy_rules_after_settings_upgrade() -> None:
    async def run() -> None:
        store = create_autospec(ProcessingStore, instance=True)
        store.stage.return_value = True
        store.settings.return_value = {"rubric": RubricConfig.default()}
        legacy = RubricConfig.default(version=1).model_dump(mode="json", exclude={"version"})
        job = ProcessingJob(
            id=uuid4(),
            item_id=uuid4(),
            user_id=uuid4(),
            lease_token=uuid4(),
            source_text=TEXT,
            rubric_snapshot=legacy,
            reservation_id=uuid4(),
            reservation_state="settled",
            threshold_snapshot=60,
            model_result=saved_model_result(legacy=True),
        )
        provider = create_autospec(AssessmentProvider, instance=True)
        await ProcessingService(store, provider, AsyncMock()).process(job)
        result = store.complete.call_args.args[1]
        assert result.rubric_snapshot.version == 1
        assert result.score == 93.33  # Legacy missing corroboration remains 1, other scores 5.
        assert result.criteria[5]["score"] == 1
        store.settings.assert_not_awaited()
        store.reserve.assert_not_awaited()
        provider.assess.assert_not_awaited()

    asyncio.run(run())
