"""Account identity and profile contracts shared by application and adapters."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

AccountStatus = Literal["pending", "approved", "rejected"]
AccountRole = Literal["user", "admin"]
EmailDeliveryStatus = Literal["pending", "sending", "sent", "failed"]


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    """Identity resolved by Supabase from an access token, never client claims."""

    user_id: UUID
    email: str
    email_verified: bool


class AccountProfile(BaseModel):
    """Server-owned account state returned by the account repository."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    email: str
    status: AccountStatus
    trial_links_used: int = Field(ge=0)
    created_at: datetime


class AccountSummary(BaseModel):
    """Safe account view for the authenticated user."""

    user_id: UUID
    email: str
    status: AccountStatus
    role: AccountRole
    trial_links_used: int
    trial_links_remaining: int


class AdminAccountSummary(AccountProfile):
    """Account metadata visible to the administrator, including email delivery state."""

    approval_email_status: EmailDeliveryStatus | None = None
    approval_email_failure_code: str | None = None


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    message_id: str


@dataclass(frozen=True, slots=True)
class ApprovalNotification:
    notification_id: UUID
    user_id: UUID
    email: str


class MailDeliveryError(Exception):
    """Sanitized error category returned by an approval mail adapter."""

    def __init__(self, failure_code: str) -> None:
        if failure_code not in {
            "timeout",
            "provider_rejected",
            "invalid_response",
            "unavailable",
            "not_configured",
        }:
            raise ValueError("unsupported email failure code")
        super().__init__(failure_code)


class ApprovalMailer(Protocol):
    async def send_approval(self, email: str, event_id: UUID) -> DeliveryReceipt: ...


class AccountRepository(Protocol):
    async def get_or_create_profile(
        self, user_id: UUID, email: str, *, is_admin: bool
    ) -> AccountProfile: ...

    async def get_profile(self, user_id: UUID) -> AccountProfile | None: ...

    async def list_profiles(self) -> list[AccountProfile]: ...

    async def list_admin_profiles(self) -> list[AdminAccountSummary]: ...

    async def set_profile_status(
        self, user_id: UUID, status: AccountStatus
    ) -> tuple[AccountStatus, AccountProfile, UUID | None] | None: ...

    async def claim_approval_notification(
        self, notification_id: UUID
    ) -> ApprovalNotification | None: ...

    async def finish_approval_notification(
        self,
        notification_id: UUID,
        *,
        status: Literal["sent", "failed"],
        provider_message_id: str | None,
        failure_code: str | None,
    ) -> None: ...

    async def get_approval_notification(
        self, user_id: UUID
    ) -> tuple[UUID, EmailDeliveryStatus, str | None] | None: ...


class AccountAccessDenied(Exception):
    """The verified caller does not have administrator access."""


class InitialAdminProtected(Exception):
    """The configured initial administrator cannot be modified by account controls."""


class AccountNotFound(Exception):
    """The target account does not exist."""


class AccountService:
    """Apply account bootstrap rules using server-verified identity data."""

    def __init__(
        self,
        repository: AccountRepository,
        admin_email: str | None,
        mailer: ApprovalMailer | None = None,
    ) -> None:
        self._repository = repository
        self._admin_email = admin_email.strip().casefold() if admin_email else None
        self._mailer = mailer

    async def profile(self, identity: AuthenticatedIdentity) -> AccountSummary:
        is_admin = self.is_admin(identity)
        profile = await self._repository.get_or_create_profile(
            identity.user_id, identity.email, is_admin=is_admin
        )
        role: AccountRole = "admin" if is_admin else "user"
        return AccountSummary(
            user_id=profile.user_id,
            email=profile.email,
            status="approved" if is_admin else profile.status,
            role=role,
            trial_links_used=profile.trial_links_used,
            trial_links_remaining=max(0, 3 - profile.trial_links_used),
        )

    def is_admin(self, identity: AuthenticatedIdentity) -> bool:
        return bool(
            identity.email_verified
            and self._admin_email
            and identity.email.strip().casefold() == self._admin_email
        )

    def require_admin(self, identity: AuthenticatedIdentity) -> None:
        if not self.is_admin(identity):
            raise AccountAccessDenied

    async def can_access(self, user_id: UUID) -> bool:
        profile = await self._repository.get_profile(user_id)
        return profile is not None and profile.status != "rejected"

    async def list_accounts(self, identity: AuthenticatedIdentity) -> list[AdminAccountSummary]:
        self.require_admin(identity)
        return await self._repository.list_admin_profiles()

    async def set_status(
        self,
        identity: AuthenticatedIdentity,
        target_user_id: UUID,
        status: AccountStatus,
    ) -> tuple[AccountStatus, AccountProfile, EmailDeliveryStatus | None, str | None]:
        self.require_admin(identity)
        if target_user_id == identity.user_id:
            raise InitialAdminProtected
        changed = await self._repository.set_profile_status(target_user_id, status)
        if changed is None:
            raise AccountNotFound
        previous_status, profile, notification_id = changed
        if notification_id is None:
            return previous_status, profile, None, None
        delivery_status, failure_code = await self._deliver_approval(notification_id)
        return previous_status, profile, delivery_status, failure_code

    async def retry_approval_email(
        self, identity: AuthenticatedIdentity, target_user_id: UUID
    ) -> tuple[EmailDeliveryStatus, str | None] | None:
        self.require_admin(identity)
        profile = await self._repository.get_profile(target_user_id)
        if profile is None or profile.status != "approved":
            return None
        current = await self._repository.get_approval_notification(target_user_id)
        if current is None:
            return None
        notification_id, status, failure_code = current
        if status == "sent":
            return status, None
        if status == "sending":
            return status, None
        return await self._deliver_approval(notification_id)

    async def _deliver_approval(
        self, notification_id: UUID
    ) -> tuple[EmailDeliveryStatus, str | None]:
        notification = await self._repository.claim_approval_notification(notification_id)
        if notification is None:
            return "sending", None
        try:
            if self._mailer is None:
                raise MailDeliveryError("not_configured")
            receipt = await self._mailer.send_approval(
                notification.email, notification.notification_id
            )
        except MailDeliveryError as error:
            await self._repository.finish_approval_notification(
                notification_id,
                status="failed",
                provider_message_id=None,
                failure_code=str(error),
            )
            return "failed", str(error)
        await self._repository.finish_approval_notification(
            notification_id,
            status="sent",
            provider_message_id=receipt.message_id,
            failure_code=None,
        )
        return "sent", None
