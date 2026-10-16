import asyncio
import json
from decimal import Decimal

import httpx
import pytest

from linksifty.application.processing_contracts import EvidenceSource
from linksifty.domain.models import CriterionName
from linksifty.infrastructure.openrouter_client import OpenRouterClient

PRIMARY = (
    "Na IKE można co roku wpłacić maksymalnie 300% prognozowanego na dany rok "
    "przeciętnego miesięcznego wynagrodzenia w gospodarce narodowej."
)
EXTERNAL = (
    "IKE – to nie jest żaden konkretny produkt finansowy, tylko swego rodzaju "
    "„prawne opakowanie” na różne produkty finansowe."
)


@pytest.mark.parametrize("unknown", [False, True])
def test_selected_passage_controls_exact_quote_and_source_without_retry(unknown: bool) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = json.loads(request.content)
        passages = json.loads(body["messages"][-1]["content"])
        primary_id = next(p["passage_id"] for p in passages if p["text"] == PRIMARY)
        external_id = next(p["passage_id"] for p in passages if p["text"] == EXTERNAL)
        schema = body["response_format"]["json_schema"]["schema"]
        assert "excerpt" not in json.dumps(schema)
        assert "source_id" not in json.dumps(schema)
        payload = {
            "note": "Source-backed note",
            "criteria": [
                {
                    "name": name.value,
                    "score": 3,
                    "rationale": "Supported by the selected passage",
                    "passage_id": (
                        "invented:99"
                        if unknown
                        else external_id
                        if name == CriterionName.EVIDENCE
                        else primary_id
                    ),
                }
                for name in CriterionName
            ],
        }
        return httpx.Response(
            200,
            json={
                "id": "gen-passages",
                "usage": {"cost": "0.001"},
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}],
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess(
                PRIMARY,
                sources=[EvidenceSource(id="iwuc", url="https://example.test/ike", text=EXTERNAL)],
            )
        assert calls == 1
        assert result.cost == Decimal("0.001")
        assert result.generation_id == "gen-passages"
        if unknown:
            assert result.assessment is None
            assert result.failure_reason == "invalid_citation"
        else:
            assert result.assessment is not None
            evidence = next(c for c in result.assessment.criteria if c.name.value == "evidence")
            assert evidence.source_id == "iwuc"
            assert evidence.excerpt == EXTERNAL
            assert result.assessment.criteria[0].source_id == "primary"
            assert result.assessment.criteria[0].excerpt == PRIMARY

    asyncio.run(run())


@pytest.mark.parametrize(
    "source",
    [
        "A" * 1001,
        "A" * 2000,
        ("Długi tekst z polskimi znakami – i\u00a0odstępami.\n" * 100) + "Koniec.",
        "A" * 999 + " " + "Z" * 1009,
    ],
)
def test_long_source_keeps_all_text_and_selected_original_offsets(source: str) -> None:
    selected = ""

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal selected
        passages = json.loads(json.loads(request.content)["messages"][-1]["content"])
        assert "".join(p["text"] for p in passages) == source
        assert len({p["passage_id"] for p in passages}) == len(passages)
        assert all(10 <= len(p["text"]) <= 2000 for p in passages)
        selected = passages[-1]["text"]
        payload = {
            "note": "Note",
            "criteria": [
                {
                    "name": n.value,
                    "score": 3,
                    "rationale": "Supported",
                    "passage_id": passages[-1]["passage_id"],
                }
                for n in CriterionName
            ],
        }
        return httpx.Response(
            200,
            json={
                "usage": {"cost": "0.001"},
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}],
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess(source)
        assert result.assessment is not None
        for criterion in result.assessment.criteria:
            assert criterion.source_id == "primary"
            assert criterion.excerpt == selected
            start = source.index(criterion.excerpt)
            assert source[start : start + len(criterion.excerpt)] == selected

    asyncio.run(run())
