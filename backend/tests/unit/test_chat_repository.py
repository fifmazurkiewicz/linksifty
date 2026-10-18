import asyncio
import json
from decimal import Decimal
from uuid import uuid4

import httpx

from linksifty.infrastructure.chat_repository import ChatRepository


def test_context_reads_are_owner_filtered_and_saved_sources_are_restored() -> None:
    async def run() -> None:
        user, item = uuid4(), uuid4()
        requests = []

        def respond(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            assert request.url.params["user_id"] == f"eq.{user}"
            if request.url.path.endswith("/items"):
                assert request.url.params["id"] == f"eq.{item}"
                assert request.url.params["status"] == "eq.completed"
                assert request.url.params["expires_at"].startswith("gt.")
                return httpx.Response(
                    200, json=[{"id": str(item), "original_url": "https://original.test"}]
                )
            if request.url.path.endswith("/source_contents"):
                return httpx.Response(200, json=[{"content": "Complete saved text. " * 30}])
            if request.url.path.endswith("/assessments"):
                return httpx.Response(
                    200,
                    json=[
                        {
                            "id": str(uuid4()),
                            "note": "Saved note",
                            "criteria": [],
                            "score": 75,
                            "verdict": "valuable",
                            "threshold_snapshot": 60,
                        }
                    ],
                )
            if request.url.path.endswith("/citations"):
                return httpx.Response(200, json=[])
            if request.url.path.endswith("/jobs"):
                return httpx.Response(
                    200,
                    json=[
                        {
                            "search_context": {
                                "status": "ready",
                                "sources": [
                                    {
                                        "id": "source1",
                                        "url": "https://saved.test",
                                        "text": "Saved research",
                                    }
                                ],
                            }
                        }
                    ],
                )
            raise AssertionError("Unexpected read")

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            context = await ChatRepository("https://db.test", "service-test-key", client).context(
                user, item
            )
        assert context and context.sources[0].url == "https://saved.test"
        assert context.assessment.note == "Saved note"
        assert requests

    asyncio.run(run())


def test_claim_and_call_reservation_send_verified_owner_and_request_identity() -> None:
    async def run() -> None:
        user, item, request_id, reservation = uuid4(), uuid4(), uuid4(), uuid4()

        def respond(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            assert payload["p_user_id"] == str(user)
            if request.url.path.endswith("/begin_chat_turn"):
                assert payload["p_item_id"] == str(item)
                assert payload["p_request_id"] == str(request_id)
                return httpx.Response(
                    200,
                    json=[
                        {
                            "claimed": True,
                            "turn": {
                                "id": str(request_id),
                                "item_id": str(item),
                                "question": "Why?",
                                "status": "pending",
                            },
                        }
                    ],
                )
            assert payload["p_turn_id"] == str(request_id)
            assert payload["p_slot"] == "decision"
            assert payload["p_amount"] == "0.15"
            return httpx.Response(200, json=[{"id": str(reservation)}])

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            repository = ChatRepository("https://db.test", "service-test-key", client)
            claim = await repository.claim_turn(user, item, request_id, "Why?")
            assert claim and claim.claimed
            assert (
                await repository.reserve_call(user, claim.turn, "decision", Decimal("0.15"))
                == reservation
            )

    asyncio.run(run())
