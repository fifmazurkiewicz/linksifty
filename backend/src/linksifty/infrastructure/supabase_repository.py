"""User-scoped Supabase REST persistence with validated responses."""

import logging
from datetime import datetime
from uuid import UUID

import httpx
from pydantic import BaseModel, TypeAdapter, ValidationError

from linksifty.application.account_contracts import (
    AccountProfile,
    AccountStatus,
    AdminAccountSummary,
    ApprovalNotification,
    EmailDeliveryStatus,
)
from linksifty.application.item_contracts import ItemRecord


class RepositoryUnavailable(Exception):
    """Persistence failed; provider details remain server-side."""


class AccountPolicyViolation(Exception):
    """A stable account rule rejected a persistence operation."""

    def __init__(self, reason: str) -> None:
        if reason not in {"trial_limit_exceeded", "account_rejected", "profile_missing"}:
            raise ValueError("unsupported account policy reason")
        super().__init__(reason)


class _StoredAccountProfile(AccountProfile):
    """Full row shape returned by the profile RPC, including its audit timestamp."""

    updated_at: datetime


_items = TypeAdapter(list[ItemRecord])
_profiles = TypeAdapter(list[_StoredAccountProfile])
_logger = logging.getLogger(__name__)


class _ProfileStatusChange(BaseModel):
    previous_status: AccountStatus
    user_id: UUID
    email: str
    status: AccountStatus
    trial_links_used: int
    created_at: str
    approval_notification_id: UUID | None = None


class _NotificationClaim(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    attempts: int


class _NotificationSummary(BaseModel):
    id: UUID
    status: EmailDeliveryStatus
    failure_code: str | None = None


class SupabaseRepository:
    """Service-role adapter; every operation also enforces the verified owner."""

    def __init__(self, url: str, service_key: str, client: httpx.AsyncClient) -> None:
        self._url = f"{url.rstrip('/')}/rest/v1"
        self._headers = {"apikey": service_key}
        if not service_key.startswith("sb_secret_"):
            self._headers["Authorization"] = f"Bearer {service_key}"
        self._client = client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, object] | None = None,
    ) -> list[ItemRecord]:
        try:
            response = await self._client.request(
                method,
                f"{self._url}/{path}",
                headers={**self._headers, "Prefer": "return=representation"},
                params=params,
                json=payload,
                timeout=10,
                follow_redirects=False,
            )
            if not response.is_success:
                if response.status_code == 400:
                    try:
                        error = response.json()
                    except ValueError:
                        error = None
                    if isinstance(error, dict) and error.get("code") == "P0001":
                        message = error.get("message")
                        reasons = {
                            "account_trial_limit_exceeded": "trial_limit_exceeded",
                            "account_rejected": "account_rejected",
                            "account_profile_missing": "profile_missing",
                        }
                        if isinstance(message, str) and message in reasons:
                            raise AccountPolicyViolation(reasons[message])
                raise RepositoryUnavailable("Persistence temporarily unavailable")
            return _items.validate_json(response.content)
        except (httpx.HTTPError, ValidationError) as error:
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def get_or_create_profile(
        self, user_id: UUID, email: str, *, is_admin: bool
    ) -> AccountProfile:
        try:
            response = await self._client.post(
                f"{self._url}/rpc/get_or_create_account_profile",
                headers=self._headers,
                json={"p_user_id": str(user_id), "p_email": email, "p_is_admin": is_admin},
                timeout=10,
                follow_redirects=False,
            )
            if not response.is_success:
                try:
                    body = response.json()
                except ValueError:
                    body = None
                code = body.get("code") if isinstance(body, dict) else None
                safe_code = code if isinstance(code, str) else "unknown"
                _logger.warning(
                    "supabase_profile_rpc_failed status=%s code=%s",
                    response.status_code,
                    safe_code,
                )
                raise RepositoryUnavailable("Persistence temporarily unavailable")
            profiles = _profiles.validate_json(response.content)
            if len(profiles) != 1:
                _logger.warning("supabase_profile_rpc_invalid_result")
                raise RepositoryUnavailable("Persistence temporarily unavailable")
            stored_profile = profiles[0]
            return AccountProfile(
                user_id=stored_profile.user_id,
                email=stored_profile.email,
                status=stored_profile.status,
                trial_links_used=stored_profile.trial_links_used,
                created_at=stored_profile.created_at,
            )
        except httpx.HTTPError as error:
            _logger.warning(
                "supabase_profile_rpc_transport_failed error_type=%s",
                type(error).__name__,
            )
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error
        except ValidationError as error:
            _logger.warning("supabase_profile_rpc_invalid_payload")
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def _profile_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        try:
            response = await self._client.request(
                method,
                f"{self._url}/{path}",
                headers={**self._headers, "Prefer": "return=representation"},
                params=params,
                json=payload,
                timeout=10,
                follow_redirects=False,
            )
            if not response.is_success:
                if response.status_code == 400:
                    try:
                        error = response.json()
                    except ValueError:
                        error = None
                    if isinstance(error, dict) and error.get("code") == "P0001":
                        message = error.get("message")
                        reasons = {
                            "account_trial_limit_exceeded": "trial_limit_exceeded",
                            "account_rejected": "account_rejected",
                            "account_profile_missing": "profile_missing",
                        }
                        if isinstance(message, str) and message in reasons:
                            raise AccountPolicyViolation(reasons[message])
                raise RepositoryUnavailable("Persistence temporarily unavailable")
            body = response.json()
            if not isinstance(body, list) or any(not isinstance(row, dict) for row in body):
                raise RepositoryUnavailable("Persistence temporarily unavailable")
            return body
        except (httpx.HTTPError, ValueError) as error:
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def list_profiles(self) -> list[AccountProfile]:
        rows = await self._profile_request(
            "GET",
            "account_profiles",
            params={
                "select": "user_id,email,status,trial_links_used,created_at",
                "order": "created_at.desc",
            },
        )
        try:
            return [AccountProfile.model_validate(row) for row in rows]
        except ValidationError as error:
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def get_profile(self, user_id: UUID) -> AccountProfile | None:
        rows = await self._profile_request(
            "GET",
            "account_profiles",
            params={
                "user_id": f"eq.{user_id}",
                "select": "user_id,email,status,trial_links_used,created_at",
                "limit": "1",
            },
        )
        if not rows:
            return None
        try:
            return AccountProfile.model_validate(rows[0])
        except ValidationError as error:
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def list_admin_profiles(self) -> list[AdminAccountSummary]:
        rows = await self._profile_request("POST", "rpc/list_admin_account_summaries")
        try:
            return [AdminAccountSummary.model_validate(row) for row in rows]
        except ValidationError as error:
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def set_profile_status(
        self, user_id: UUID, status: AccountStatus
    ) -> tuple[AccountStatus, AccountProfile, UUID | None] | None:
        rows = await self._profile_request(
            "POST",
            "rpc/set_account_profile_status",
            payload={"p_user_id": str(user_id), "p_status": status},
        )
        if not rows:
            return None
        try:
            change = _ProfileStatusChange.model_validate(rows[0])
            profile = AccountProfile.model_validate(
                change.model_dump(exclude={"previous_status", "approval_notification_id"})
            )
            return change.previous_status, profile, change.approval_notification_id
        except ValidationError as error:
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def claim_approval_notification(
        self, notification_id: UUID
    ) -> ApprovalNotification | None:
        rows = await self._profile_request(
            "POST",
            "rpc/claim_account_notification",
            payload={"p_notification_id": str(notification_id)},
        )
        if not rows:
            return None
        try:
            claim = _NotificationClaim.model_validate(rows[0])
            return ApprovalNotification(claim.id, claim.user_id, claim.email)
        except ValidationError as error:
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def finish_approval_notification(
        self,
        notification_id: UUID,
        *,
        status: str,
        provider_message_id: str | None,
        failure_code: str | None,
    ) -> None:
        await self._profile_request(
            "POST",
            "rpc/finish_account_notification",
            payload={
                "p_notification_id": str(notification_id),
                "p_status": status,
                "p_provider_message_id": provider_message_id,
                "p_failure_code": failure_code,
            },
        )

    async def get_approval_notification(
        self, user_id: UUID
    ) -> tuple[UUID, EmailDeliveryStatus, str | None] | None:
        rows = await self._profile_request(
            "GET",
            "account_notifications",
            params={
                "user_id": f"eq.{user_id}",
                "kind": "eq.account_approved",
                "select": "id,status,failure_code",
                "order": "created_at.desc",
                "limit": "1",
            },
        )
        if not rows:
            return None
        try:
            summary = _NotificationSummary.model_validate(rows[0])
            return summary.id, summary.status, summary.failure_code
        except ValidationError as error:
            raise RepositoryUnavailable("Persistence temporarily unavailable") from error

    async def list_items(self, user_id: UUID, *, offset: int = 0) -> list[ItemRecord]:
        if offset < 0:
            raise ValueError("offset must not be negative")
        return await self._request(
            "GET",
            "items",
            params={
                "user_id": f"eq.{user_id}",
                "order": "unread.desc,created_at.desc",
                "limit": "50",
                "offset": str(offset),
            },
        )

    async def get_item(self, user_id: UUID, item_id: UUID) -> ItemRecord | None:
        records = await self._request(
            "GET", "items", params={"user_id": f"eq.{user_id}", "id": f"eq.{item_id}", "limit": "1"}
        )
        return records[0] if records else None

    async def create_items(self, user_id: UUID, urls: list[str]) -> list[ItemRecord]:
        if not 1 <= len(urls) <= 5:
            raise ValueError("submit between one and five links")
        return await self._request(
            "POST", "rpc/submit_fetch_items", payload={"p_user_id": str(user_id), "p_urls": urls}
        )

    async def delete_item(self, user_id: UUID, item_id: UUID) -> bool:
        records = await self._request(
            "DELETE", "items", params={"user_id": f"eq.{user_id}", "id": f"eq.{item_id}"}
        )
        return bool(records)

    async def mark_read(self, user_id: UUID, item_id: UUID, *, unread: bool) -> ItemRecord | None:
        records = await self._request(
            "PATCH",
            "items",
            params={"user_id": f"eq.{user_id}", "id": f"eq.{item_id}"},
            payload={"unread": unread},
        )
        return records[0] if records else None
