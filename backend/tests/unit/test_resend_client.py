import asyncio
from uuid import UUID

import httpx
import pytest

from linksifty.infrastructure.resend_client import ResendApprovalMailer, ResendDeliveryError

EVENT_ID = UUID("33333333-3333-4333-8333-333333333333")


def test_resend_sends_only_approval_message_with_stable_idempotency_key() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.resend.com/emails"
        assert request.headers["Authorization"] == "Bearer resend-test-key"
        assert request.headers["Idempotency-Key"] == str(EVENT_ID)
        body = request.read().decode()
        assert "Your Linksifty account is approved" in body
        assert "gmail.readonly" not in body
        return httpx.Response(200, json={"id": "email_123"})

    async def run() -> str:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            mailer = ResendApprovalMailer(
                "resend-test-key", "Linksifty <hello@example.com>", client
            )
            result = await mailer.send_approval("person@example.com", EVENT_ID)
            return result.message_id

    assert asyncio.run(run()) == "email_123"


def test_resend_provider_error_has_safe_failure_code() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda _: httpx.Response(422, text="secret recipient/provider response")
        )
        async with httpx.AsyncClient(transport=transport) as client:
            await ResendApprovalMailer(
                "resend-test-key", "Linksifty <hello@example.com>", client
            ).send_approval("person@example.com", EVENT_ID)

    with pytest.raises(ResendDeliveryError, match="provider_rejected") as captured:
        asyncio.run(run())
    assert "secret" not in str(captured.value)


def test_resend_timeout_has_safe_failure_code() -> None:
    async def run() -> None:
        def timeout(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("private provider detail", request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(timeout)) as client:
            await ResendApprovalMailer(
                "resend-test-key", "Linksifty <hello@example.com>", client
            ).send_approval("person@example.com", EVENT_ID)

    with pytest.raises(ResendDeliveryError, match="timeout") as captured:
        asyncio.run(run())
    assert "private" not in str(captured.value)


@pytest.mark.parametrize("body", ["not-json", "{}"])
def test_resend_malformed_success_response_is_rejected(body: str) -> None:
    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))
        ) as client:
            await ResendApprovalMailer(
                "resend-test-key", "Linksifty <hello@example.com>", client
            ).send_approval("person@example.com", EVENT_ID)

    with pytest.raises(ResendDeliveryError, match="invalid_response"):
        asyncio.run(run())
