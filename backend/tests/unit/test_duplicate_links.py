import asyncio
from uuid import uuid4

import httpx
import pytest

from linksifty.application.item_contracts import DuplicateSubmission
from linksifty.infrastructure.processing_repository import ProcessingRepository


@pytest.mark.parametrize("operation", ["normal", "search", "resume"])
def test_sql_duplicate_is_mapped_to_a_conflict_for_every_submission_path(operation: str) -> None:
    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(400, json={"code": "P0001", "message": "duplicate_link"})
            )
        ) as client:
            repo = ProcessingRepository("https://supabase.example", "test-service-key", client)
            with pytest.raises(DuplicateSubmission):
                if operation == "normal":
                    await repo.create_items(uuid4(), ["https://example.test"])
                elif operation == "search":
                    await repo.submit_search(uuid4(), ["https://example.test"])
                else:
                    await repo.resume(uuid4(), uuid4())

    asyncio.run(run())
