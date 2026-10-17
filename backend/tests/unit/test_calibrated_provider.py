import asyncio
import json

import httpx
import pytest

from linksifty.application.processing_contracts import EvidenceSource, RubricConfig
from linksifty.domain.models import CriterionName
from linksifty.infrastructure.openrouter_client import OpenRouterClient


@pytest.mark.parametrize(
    "hype_passage,valid", [("primary:1", True), ("source1:1", False), ("invented:1", False)]
)
def test_grounded_hype_and_unscored_criterion(hype_passage: str, valid: bool) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        messages = json.dumps(body["messages"])
        assert "https://www.gov.pl/example" in messages
        assert "not_applicable" in messages
        payload = {
            "note": "An explainer",
            "criteria": [
                {
                    "name": n.value,
                    "status": "not_applicable" if n is CriterionName.REPLICABILITY else "assessed",
                    "score": None if n is CriterionName.REPLICABILITY else 5,
                    "rationale": "Relevant explanation",
                    "passage_id": "primary:1",
                }
                for n in CriterionName
            ],
            "hype_signals": [
                {"rationale": "Unsupported guarantee of returns", "passage_id": hype_passage}
            ],
        }
        return httpx.Response(
            200,
            json={
                "usage": {"cost": "0.01"},
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}],
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess(
                "Primary text promises guaranteed returns.",
                primary_url="https://www.gov.pl/example",
                sources=[
                    EvidenceSource(
                        id="other", url="https://other.example", text="Other source text."
                    )
                ],
            )
            assert (result.assessment is not None) is valid
            if valid:
                assert result.assessment is not None
                assert result.assessment.criteria[4].score is None
                assert result.assessment.hype_signals[0].source_id == "primary"
            else:
                assert result.failure_reason == "invalid_citation"

    asyncio.run(run())


def test_twenty_unicode_sources_fit_prompt_and_keep_primary_intact() -> None:
    primary = "Primary material " * 2000

    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert len(json.dumps(body["messages"], ensure_ascii=False).encode()) < 115000
        passages = json.loads(body["messages"][-1]["content"])
        assert (
            "".join(p["text"] for p in passages if p["passage_id"].startswith("primary:"))
            == primary
        )
        for i in range(1, 21):
            assert any(p["passage_id"].startswith(f"source{i}:") for p in passages)
        return httpx.Response(400, json={})

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess(
                primary,
                sources=[
                    EvidenceSource(
                        id=str(i), url=f"https://source{i}.example", text="漢字🦊" * 4000
                    )
                    for i in range(20)
                ],
                rubric=RubricConfig.default(),
            )

    asyncio.run(run())


def test_oversized_primary_source_is_rejected_before_http() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Oversized input must not be sent to a paid provider")

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await OpenRouterClient("test", "openai/gpt-4o-mini", client).assess(
                "漢" * 50000
            )
            assert result.failure_reason == "input_too_large"
            assert result.cost == 0

    asyncio.run(run())
