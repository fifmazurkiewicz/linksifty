import asyncio
import json
from typing import Literal

import httpx
import pytest

from linksifty.application.processing_contracts import RubricConfig
from linksifty.domain.models import CriterionName
from linksifty.infrastructure.openrouter_client import OpenRouterClient

SOURCE = (
    "A rain garden is a shallow planted area that collects runoff from roofs or paving. "
    "Water soaks into the soil instead of immediately entering storm drains. "
    "Suitable soil and a location away from building foundations are important. "
    "A rain garden can reduce runoff during small storms but cannot prevent all flooding."
)
SUMMARIES = [
    "A rain garden is a shallow planted area that collects water running off roofs or "
    "paved surfaces. It lets that water soak into the soil instead of immediately "
    "entering storm drains.\n\n"
    "This can help reduce runoff during small storms. Suitable soil and a location "
    "away from foundations are important, and a rain garden cannot prevent all flooding.",
    "Rain gardens collect runoff in shallow planted areas so water can soak into the soil.\n\n"
    "Key considerations\n"
    "• Use suitable soil and keep the garden away from building foundations.\n"
    "• The benefit is reduced runoff in small storms, without a promise to prevent flooding.",
]


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("summary", SUMMARIES, ids=["prose", "sections"])
def test_summary_request_teaches_topic_and_preserves_flexible_plain_text(
    version: Literal[1, 2], summary: str
) -> None:
    """Check the provider contract; a mock cannot demonstrate live writing quality."""
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = json.loads(request.content)
        instructions = body["messages"][0]["content"].lower()
        # Inspect the actual outgoing request, including both historic rubric paths.
        assert "topic basics" in instructions
        assert "concrete facts" in instructions
        assert "why" in instructions and "matter" in instructions
        assert "adapt" in instructions and "paragraphs" in instructions
        assert "no fixed" in instructions
        assert "do not invent" in instructions
        assert "primary-source passages" in instructions
        note_schema = body["response_format"]["json_schema"]["schema"]["properties"]["note"]
        assert "summary" in note_schema.get("description", "").lower()
        assert note_schema["maxLength"] == 6000
        supplied = json.loads(body["messages"][-1]["content"])
        assert supplied == [{"passage_id": "primary:1", "text": SOURCE}]
        payload = {
            "note": summary,
            "criteria": [
                {
                    "name": name.value,
                    "score": 3,
                    "status": "assessed",
                    "rationale": "The supplied explanation supports this assessment.",
                    "passage_id": "primary:1",
                }
                for name in CriterionName
            ],
            "hype_signals": [],
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
            provider = OpenRouterClient("test-key", "openai/gpt-4o-mini", client)
            result = await provider.assess(SOURCE, rubric=RubricConfig.default(version=version))
        assert result.failure_reason is None
        assert result.assessment is not None
        assert result.assessment.note == summary
        assert len(result.assessment.criteria) == 8
        assert calls == 1

    asyncio.run(run())
