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
REQUEST_AGAIN_EVENT = UUID("44444444-4444-4444-8444-444444444444")


class NotificationRepository:
    def __init__(self) -> None:
        self.status = "pending"
        self.email_status = "pending"
        self.failure_code: str | None = None
        self.access_requests: list[UUID] = []
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

    async def request_access_again(
        self, user_id: UUID
    ) -> tuple[AccountProfile, UUID | None] | None:
        self.access_requests.append(user_id)
        if user_id != USER:
            return None
        if self.profile.status != "rejected":
            return self.profile, None
        self.profile = self.profile.model_copy(update={"status": "pending"})
        self.email_status = "pending"
        return self.profile, REQUEST_AGAIN_EVENT

    async def claim_approval_notification(
        self, notification_id: UUID
    ) -> ApprovalNotification | None:
        if self.email_status not in {"pending", "failed"}:
            return None
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

    async def send_account_request(
        self, recipient: str, user_email: str, event_id: UUID
    ) -> DeliveryReceipt:
        assert recipient == "fifmazurkiewicz@gmail.com"
        assert user_email == "user@example.com"
        self.events.append(event_id)
        if self.fail_once:
            self.fail_once = False
            raise MailDeliveryError("timeout")
        return DeliveryReceipt("resend-message-id")


def test_first_login_notifies_owner_once_and_approval_only_grants_access() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        mailer = FakeMailer()
        service = AccountService(repository, "admin@example.com", mailer)
        user = AuthenticatedIdentity(USER, "user@example.com", True)
        admin = AuthenticatedIdentity(
            UUID("99999999-9999-4999-8999-999999999999"), "admin@example.com", True
        )
        first = await service.profile(user)
        await service.profile(user)
        assert first.status == "pending"
        assert first.trial_links_remaining == 2
        assert repository.email_status == "sent"
        approved = await service.set_status(admin, USER, "approved")
        await service.profile(user)
        assert approved[1].status == "approved"
        assert approved[2] is None
        assert mailer.events == [EVENT]

    import asyncio

    asyncio.run(run())


def test_failed_login_notification_never_blocks_or_retries_on_later_login() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        mailer = FakeMailer(fail_once=True)
        service = AccountService(repository, "admin@example.com", mailer)
        user = AuthenticatedIdentity(USER, "user@example.com", True)
        assert (await service.profile(user)).status == "pending"
        assert repository.email_status == "failed"
        assert repository.failure_code == "timeout"
        await service.profile(user)
        assert mailer.events == [EVENT]
        admin = AuthenticatedIdentity(
            UUID("99999999-9999-4999-8999-999999999999"), "admin@example.com", True
        )
        assert await service.retry_approval_email(admin, USER) == ("sent", None)
        assert mailer.events == [EVENT, EVENT]
        assert await service.retry_approval_email(admin, USER) == ("sent", None)
        assert mailer.events == [EVENT, EVENT]

    import asyncio

    asyncio.run(run())


def test_admin_rejected_and_unverified_accounts_do_not_send_notification() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        mailer = FakeMailer()
        service = AccountService(repository, "admin@example.com", mailer)
        await service.profile(AuthenticatedIdentity(USER, "admin@example.com", True))
        await service.profile(AuthenticatedIdentity(USER, "user@example.com", False))
        repository.profile = repository.profile.model_copy(update={"status": "rejected"})
        await service.profile(AuthenticatedIdentity(USER, "user@example.com", True))
        assert mailer.events == []
        admin = AuthenticatedIdentity(
            UUID("99999999-9999-4999-8999-999999999999"), "admin@example.com", True
        )
        assert await service.retry_approval_email(admin, USER) is None

    import asyncio

    asyncio.run(run())


def test_missing_resend_configuration_keeps_login_available() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        service = AccountService(repository, "admin@example.com")
        assert (
            await service.profile(AuthenticatedIdentity(USER, "user@example.com", True))
        ).status == "pending"
        assert repository.email_status == "failed"
        assert repository.failure_code == "not_configured"

    import asyncio

    asyncio.run(run())


def test_notification_storage_outage_does_not_block_login() -> None:
    class BrokenNotifications(NotificationRepository):
        async def get_approval_notification(self, user_id: UUID) -> None:
            raise RuntimeError("unavailable")

    async def run() -> None:
        service = AccountService(BrokenNotifications(), "admin@example.com", FakeMailer())
        assert (
            await service.profile(AuthenticatedIdentity(USER, "user@example.com", True))
        ).status == "pending"

    import asyncio

    asyncio.run(run())


def test_interrupted_sending_event_is_not_resent_on_login_or_admin_retry() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        repository.email_status = "sending"
        mailer = FakeMailer()
        service = AccountService(repository, "admin@example.com", mailer)
        assert (
            await service.profile(AuthenticatedIdentity(USER, "user@example.com", True))
        ).status == "pending"
        admin = AuthenticatedIdentity(
            UUID("99999999-9999-4999-8999-999999999999"), "admin@example.com", True
        )
        assert await service.retry_approval_email(admin, USER) == ("sending", None)
        assert mailer.events == []

    import asyncio

    asyncio.run(run())


def test_blocked_user_requests_access_again_with_one_new_owner_notification() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        repository.profile = repository.profile.model_copy(update={"status": "rejected"})
        mailer = FakeMailer()
        service = AccountService(repository, "admin@example.com", mailer)
        user = AuthenticatedIdentity(USER, "user@example.com", True)
        summary = await service.request_access_again(user)
        assert summary.status == "pending"
        assert summary.trial_links_used == 1
        assert mailer.events == [REQUEST_AGAIN_EVENT]
        assert repository.email_status == "sent"
        # A second click on the now-pending account neither changes state nor sends mail.
        assert (await service.request_access_again(user)).status == "pending"
        assert repository.access_requests == [USER]
        assert mailer.events == [REQUEST_AGAIN_EVENT]
        admin = AuthenticatedIdentity(
            UUID("99999999-9999-4999-8999-999999999999"), "admin@example.com", True
        )
        approved = await service.set_status(admin, USER, "approved")
        assert approved[1].status == "approved"
        assert mailer.events == [REQUEST_AGAIN_EVENT]

    import asyncio

    asyncio.run(run())


def test_access_request_succeeds_when_owner_mail_fails_and_admin_can_retry() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        repository.profile = repository.profile.model_copy(update={"status": "rejected"})
        mailer = FakeMailer(fail_once=True)
        service = AccountService(repository, "admin@example.com", mailer)
        summary = await service.request_access_again(
            AuthenticatedIdentity(USER, "user@example.com", True)
        )
        assert summary.status == "pending"
        assert repository.email_status == "failed"
        admin = AuthenticatedIdentity(
            UUID("99999999-9999-4999-8999-999999999999"), "admin@example.com", True
        )
        assert await service.retry_approval_email(admin, USER) == ("sent", None)

    import asyncio

    asyncio.run(run())


def test_access_request_never_touches_unblocked_or_administrator_accounts() -> None:
    async def run() -> None:
        repository = NotificationRepository()
        mailer = FakeMailer()
        service = AccountService(repository, "admin@example.com", mailer)
        user = AuthenticatedIdentity(USER, "user@example.com", True)
        assert (await service.request_access_again(user)).status == "pending"
        admin = await service.request_access_again(
            AuthenticatedIdentity(USER, "admin@example.com", True)
        )
        assert admin.status == "approved"
        assert admin.role == "admin"
        assert repository.access_requests == []
        assert mailer.events == []

    import asyncio

    asyncio.run(run())
