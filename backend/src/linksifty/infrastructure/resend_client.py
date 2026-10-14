"""Send account approval notifications through Resend's HTTP API."""

from uuid import UUID

import httpx

from linksifty.application.account_contracts import DeliveryReceipt, MailDeliveryError


class ResendDeliveryError(MailDeliveryError):
    """A sanitized Resend failure category safe to persist and display."""

    def __init__(self, failure_code: str) -> None:
        super().__init__(failure_code)


class ResendApprovalMailer:
    """Minimal HTTPX adapter for the one email Linksifty currently sends."""

    def __init__(self, api_key: str, from_email: str, client: httpx.AsyncClient) -> None:
        self._api_key = api_key
        self._from_email = from_email
        self._client = client

    async def send_approval(self, email: str, event_id: UUID) -> DeliveryReceipt:
        payload = {
            "from": self._from_email,
            "to": [email],
            "subject": "Your Linksifty account is approved",
            "text": "Your Linksifty account has been approved. Sign in to continue.",
            "html": "<p>Your Linksifty account has been approved.</p><p>Sign in to continue.</p>",
        }
        try:
            response = await self._client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Idempotency-Key": str(event_id),
                },
                json=payload,
                timeout=10,
                follow_redirects=False,
            )
        except httpx.TimeoutException as error:
            raise ResendDeliveryError("timeout") from error
        except httpx.HTTPError as error:
            raise ResendDeliveryError("unavailable") from error

        if not response.is_success:
            raise ResendDeliveryError("provider_rejected")
        try:
            message_id = response.json().get("id")
        except (ValueError, AttributeError) as error:
            raise ResendDeliveryError("invalid_response") from error
        if not isinstance(message_id, str) or not message_id:
            raise ResendDeliveryError("invalid_response")
        return DeliveryReceipt(message_id)
