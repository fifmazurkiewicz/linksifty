import asyncio
import json
from decimal import Decimal

import httpx
import pytest

from linksifty.domain.models import CriterionName
from linksifty.infrastructure.openrouter_client import OpenRouterClient


@pytest.mark.parametrize("marker", ["", "...", "…"])
def test_whitespace_variation_is_reanchored_to_the_exact_saved_source(marker: str) -> None:
    source = "Before: exact\nexternal\u00a0evidence passage. After."
    payload = {
        "note": "Note",
        "criteria": [
            {
                "name": name.value,
                "score": 3,
                "rationale": "Supported",
                "excerpt": "exact external evidence passage." + marker,
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


def test_trailing_omission_markers_reanchor_only_a_complete_exact_quote() -> None:
    from linksifty.domain.excerpts import resolve_excerpt

    source = (
        "Od 1 stycznia 2027 r. Polacy będą mogli korzystać z Osobistych Kont "
        "Inwestycyjnych (OKI) – nowego sposobu inwestowania."
    )
    prefix = source.split(" – ")[0]
    for marker in ("...", "…"):
        assert resolve_excerpt(source, prefix + marker) == prefix
        assert resolve_excerpt(source, prefix + " " + marker + " \n") == prefix
        assert (
            resolve_excerpt(
                "Before: exact\nevidence passage. After.", "exact evidence passage" + marker
            )
            == "exact\nevidence passage"
        )
        assert resolve_excerpt(source, "Invented investment claim" + marker) is None
        assert resolve_excerpt(source, "od 1 stycznia 2027 r." + marker) is None
        assert resolve_excerpt("unrelated source", prefix + marker) is None
        assert (
            resolve_excerpt(source, "Od 1 stycznia" + marker + "Kont Inwestycyjnych (OKI)") is None
        )
        assert resolve_excerpt("OKI is an investment account", "OKI" + marker) is None
        assert resolve_excerpt(source, marker) is None
    assert (
        resolve_excerpt("Literal evidence... is retained.", "Literal evidence...")
        == "Literal evidence..."
    )
    assert (
        resolve_excerpt("Literal evidence… is retained.", "Literal evidence…")
        == "Literal evidence…"
    )
