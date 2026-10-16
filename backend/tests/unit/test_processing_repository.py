import asyncio
from decimal import Decimal
from uuid import UUID

import httpx

from linksifty.infrastructure.processing_repository import ProcessingRepository

USER = UUID("11111111-1111-4111-8111-111111111111")


def test_usage_is_owner_scoped_and_preserves_subcent_cost() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/rpc/get_usage_summary")
        assert request.read() == b'{"p_user_id":"11111111-1111-4111-8111-111111111111"}'
        return httpx.Response(
            200,
            json=[
                {
                    "spent_usd": "0.00012345",
                    "reserved_usd": "0.02",
                    "limit_usd": "10",
                    "remaining_usd": "9.97987655",
                    "month": "2026-10-01",
                    "resets_at": "2026-11-01T00:00:00Z",
                }
            ],
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repo = ProcessingRepository("https://supabase.example", "sb_secret_test", client)
            usage = await repo.usage(USER)
            assert usage.spent_usd == Decimal("0.00012345")
            assert usage.remaining_usd == Decimal("9.97987655")

    asyncio.run(run())


def test_late_result_is_bound_to_its_original_reservation() -> None:
    import json

    from linksifty.application.processing_contracts import ModelResult, ProcessingJob

    reservation = UUID("33333333-3333-4333-8333-333333333333")
    job_id = UUID("22222222-2222-4222-8222-222222222222")
    lease = UUID("44444444-4444-4444-8444-444444444444")

    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["p_reservation"] == str(reservation)
        assert payload["p_lease"] == str(lease)
        assert payload["p_user_id"] == str(USER)
        return httpx.Response(200, json=[])

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repo = ProcessingRepository("https://supabase.example", "sb_secret_test", client)
            job = ProcessingJob(
                id=job_id,
                item_id=job_id,
                user_id=USER,
                lease_token=lease,
                reservation_id=reservation,
            )
            assert not await repo.record_result(
                job, ModelResult(generation_id="gen-late", cost=Decimal("0.001"))
            )

    asyncio.run(run())


def test_settings_write_is_one_owner_scoped_rpc_with_complete_rubric() -> None:
    import json

    from linksifty.application.processing_contracts import RubricConfig

    rubric = RubricConfig.default()

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/rpc/update_user_assessment_settings")
        payload = json.loads(request.content)
        assert payload == {
            "p_user_id": str(USER),
            "p_threshold": "75",
            "p_rubric": rubric.model_dump(mode="json"),
        }
        return httpx.Response(
            200, json=[{"valuable_threshold": "75", "rubric": rubric.model_dump(mode="json")}]
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repo = ProcessingRepository("https://supabase.example", "sb_secret_test", client)
            result = await repo.update_settings(USER, Decimal(75), rubric)
            assert result.rubric == rubric
            assert result.valuable_threshold == 75

    asyncio.run(run())
