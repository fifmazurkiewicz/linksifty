import asyncio
import json
from decimal import Decimal

import httpx

from linksifty.domain.models import CriterionName
from linksifty.infrastructure.openrouter_client import OpenRouterClient


def test_whitespace_variation_is_reanchored_to_the_exact_saved_source() -> None:
    source = "Before: exact\nexternal\u00a0evidence passage. After."
    payload = {
        "note": "Note",
        "criteria": [
            {
                "name": name.value,
                "score": 3,
                "rationale": "Supported",
                "excerpt": "exact external evidence passage.",
                "source_id": "primary",
            }
            for name in CriterionName
        ],
    }

    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "usage": {"cost": "0.001"},
                        "choices": [
                            {"finish_reason": "stop", "message": {"content": json.dumps(payload)}}
                        ],
                    },
                )
            )
        ) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess(source)
            assert result.assessment is not None
            assert result.assessment.criteria[0].excerpt == "exact\nexternal\u00a0evidence passage."
            assert result.assessment.criteria[0].excerpt in source
            assert result.cost == Decimal("0.001")

    asyncio.run(run())


def test_matching_never_changes_words_case_or_source() -> None:
    from linksifty.domain.excerpts import resolve_excerpt

    assert (
        resolve_excerpt("exact evidence passage", "exact\nevidence\tpassage")
        == "exact evidence passage"
    )
    assert resolve_excerpt("exact evidence passage", "invented evidence passage") is None
    assert resolve_excerpt("Exact evidence passage", "exact evidence passage") is None
    assert resolve_excerpt("source text", " ") is None
