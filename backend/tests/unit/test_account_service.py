from datetime import UTC, datetime
from uuid import UUID

from linksifty.application.account_contracts import (
    AccountProfile,
    AccountService,
    ApprovalNotification,
    AuthenticatedIdentity,
    DeliveryReceipt,
    MailDeliveryError,
)

USER = UUID("11111111-1111-4111-8111-111111111111")
EVENT = UUID("33333333-3333-4333-8333-333333333333")


class NotificationRepository:
    def __init__(self) -> None:
        self.status = "pending"
        self.email_status = "pending"
        self.failure_code: str | None = None
        self.profile = AccountProfile(
            user_id=USER,
            email="user@example.com",
            status="pending",
            trial_links_used=1,
            created_at=datetime(2026, 10, 14, tzinfo=UTC),
        )

    async def get_or_create_profile(
        self, user_id: UUID, email: str, *, is_admin: bool
    ) -> AccountProfile:
        return self.profile

    async def get_profile(self, user_id: UUID) -> AccountProfile | None:
        return self.profile if user_id == USER else None

    async def list_profiles(self) -> list[AccountProfile]:
        return [self.profile]

    async def list_admin_profiles(self) -> list[object]:
        return []

    async def set_profile_status(
        self, user_id: UUID, status: str
    ) -> tuple[str, AccountProfile, UUID | None] | None:
        previous = self.status
        self.status = status
        self.profile = self.profile.model_copy(update={"status": status})
        notification_id = EVENT if status == "approved" and previous != "approved" else None
        return previous, self.profile, notification_id

    async def claim_approval_notification(self, notification_id: UUID) -> ApprovalNotification:
        if self.email_status not in {"pending", "failed"}:
            raise AssertionError("notification should not be claimed twice")
        self.email_status = "sending"
        return ApprovalNotification(notification_id, USER, "user@example.com")

    async def finish_approval_notification(
        self,
        notification_id: UUID,
        *,
        status: str,
        provider_message_id: str | None,
        failure_code: str | None,
    ) -> None:
        self.email_status = status
        self.failure_code = failure_code

    async def get_approval_notification(self, user_id: UUID) -> tuple[UUID, str, str | None] | None:
        return EVENT, self.email_status, self.failure_code


class FakeMailer:
    def __init__(self, fail_once: bool = False) -> None:
        self.fail_once = fail_once
        self.events: list[UUID] = []

    async def send_approval(self, email: str, event_id: UUID) -> DeliveryReceipt:
        self.events.append(event_id)
        if self.fail_once:
            self.fail_once = False
            raise MailDeliveryError("timeout")
        return DeliveryReceipt("resend-message-id")


def test_approval_is_committed_before_email_and_repeat_does_not_resend() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        mailer = FakeMailer()
        service = AccountService(repository, "admin@example.com", mailer)
        admin = AuthenticatedIdentity(
            UUID("99999999-9999-4999-8999-999999999999"), "admin@example.com", True
        )

        first = await service.set_status(admin, USER, "approved")
        second = await service.set_status(admin, USER, "approved")

        assert first[1].status == "approved"
        assert first[2] == "sent"
        assert second[2] is None
        assert mailer.events == [EVENT]

    import asyncio

    asyncio.run(run())


def test_email_failure_keeps_approval_and_admin_retry_sends_same_event() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        mailer = FakeMailer(fail_once=True)
        service = AccountService(repository, "admin@example.com", mailer)
        admin = AuthenticatedIdentity(
            UUID("99999999-9999-4999-8999-999999999999"), "admin@example.com", True
        )

        approved = await service.set_status(admin, USER, "approved")
        retried = await service.retry_approval_email(admin, USER)

        assert approved[1].status == "approved"
        assert approved[2:] == ("failed", "timeout")
        assert repository.status == "approved"
        assert retried == ("sent", None)
        assert mailer.events == [EVENT, EVENT]

    import asyncio

    asyncio.run(run())


def test_approval_email_retry_is_refused_after_account_is_rejected() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        mailer = FakeMailer(fail_once=True)
        service = AccountService(repository, "admin@example.com", mailer)
        admin = AuthenticatedIdentity(
            UUID("99999999-9999-4999-8999-999999999999"), "admin@example.com", True
        )

        await service.set_status(admin, USER, "approved")
        await service.set_status(admin, USER, "rejected")
        retried = await service.retry_approval_email(admin, USER)

        assert retried is None
        assert mailer.events == [EVENT]

    import asyncio

    asyncio.run(run())
