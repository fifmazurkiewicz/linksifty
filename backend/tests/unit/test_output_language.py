"""Generated prose must request English or Polish independently of source language."""

import asyncio
import json
from typing import Literal

import httpx
import pytest

from linksifty.application.chat_contracts import ChatInput
from linksifty.infrastructure.openrouter_client import OpenRouterClient


@pytest.mark.parametrize("operation", ["assess", "preview", "title", "reply"])
def test_generation_requests_only_english_or_polish(
    operation: Literal["assess", "preview", "title", "reply"],
) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        messages = json.loads(request.content)["messages"]
        system = messages[0]["content"]
        assert "Write generated prose in English or Polish only." in system
        assert "in its language" not in system and "in the source's language" not in system
        if operation == "reply":
            assert "default to English" in system
            assert json.loads(messages[-1]["content"])["reply_language"] == "pl"
        else:
            assert "Use Polish when the primary source is Polish; otherwise use English." in system
        # Reject locally after inspecting the outgoing request; no generated translation is mocked.
        return httpx.Response(402, json={"error": "Test-only budget rejection"})

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = OpenRouterClient("test", "openai/gpt-4o-mini", client)
            source = "Il s'agit de construire un outil pour organiser les informations. " * 5
            if operation == "reply":
                await provider.reply(
                    ChatInput(
                        question="Wyjaśnij to.", reply_language="pl", passages={}, history=[]
                    ),
                    allow_search=False,
                )
            elif operation == "assess":
                await provider.assess(source)
            elif operation == "preview":
                await provider.preview(source)
            else:
                await provider.title(source)
        assert calls == 1

    asyncio.run(run())
