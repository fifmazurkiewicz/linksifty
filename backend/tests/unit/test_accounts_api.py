from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from linksifty.api.auth import current_identity
from linksifty.application.account_contracts import (
    AccountProfile,
    AccountService,
    AdminAccountSummary,
    AuthenticatedIdentity,
)
from linksifty.config import Settings
from linksifty.main import create_app

USER = UUID("11111111-1111-4111-8111-111111111111")
OTHER = UUID("22222222-2222-4222-8222-222222222222")


class ProfileRepository:
    def __init__(self, status: str = "pending", trials: int = 0) -> None:
        self.status = status
        self.trials = trials
        self.is_admin: bool | None = None
        self.profiles = [
            AccountProfile(
                user_id=USER,
                email="user@example.com",
                status="pending",
                trial_links_used=2,
                created_at=datetime(2026, 10, 14, tzinfo=UTC),
            )
        ]

    async def get_or_create_profile(
        self, user_id: UUID, email: str, *, is_admin: bool
    ) -> AccountProfile:
        self.is_admin = is_admin
        return AccountProfile(
            user_id=user_id,
            email=email,
            status="approved" if is_admin else self.status,
            trial_links_used=self.trials,
            created_at=datetime(2026, 10, 14, tzinfo=UTC),
        )

    async def list_profiles(self) -> list[AccountProfile]:
        return self.profiles

    async def list_admin_profiles(self) -> list[AdminAccountSummary]:
        return [
            AdminAccountSummary.model_validate(profile.model_dump()) for profile in self.profiles
        ]

    async def set_profile_status(
        self, user_id: UUID, status: str
    ) -> tuple[str, AccountProfile, UUID | None] | None:
        for profile in self.profiles:
            if profile.user_id == user_id:
                updated = profile.model_copy(update={"status": status})
                self.profiles = [updated]
                return profile.status, updated, None
        return None


def test_me_returns_pending_status_and_trial_allowance() -> None:
    identity = AuthenticatedIdentity(USER, "user@example.com", True)
    app = create_app(Settings(linksifty_admin_email="admin@example.com"))
    app.dependency_overrides[current_identity] = lambda: identity
    repository = ProfileRepository(trials=2)
    app.state.accounts = AccountService(repository, "admin@example.com")

    with TestClient(app) as client:
        response = client.get("/v1/me")

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["trial_links_remaining"] == 1
    assert response.json()["role"] == "user"
    assert repository.is_admin is False


def test_verified_configured_identity_is_bootstrapped_as_admin() -> None:
    identity = AuthenticatedIdentity(USER, "Admin@Example.com", True)
    app = create_app(Settings(linksifty_admin_email="admin@example.com"))
    app.dependency_overrides[current_identity] = lambda: identity
    repository = ProfileRepository()
    app.state.accounts = AccountService(repository, "admin@example.com")

    with TestClient(app) as client:
        response = client.get("/v1/me")

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.json()["status"] == "approved"
    assert repository.is_admin is True


def test_rejected_account_is_denied_before_private_data_access() -> None:
    identity = AuthenticatedIdentity(USER, "user@example.com", True)
    app = create_app(Settings())
    app.dependency_overrides[current_identity] = lambda: identity
    app.state.accounts = AccountService(ProfileRepository(status="rejected"), None)

    with TestClient(app) as client:
        response = client.get("/v1/items")

    assert response.status_code == 403
    assert response.json()["detail"] == "This account is not approved"


def test_admin_can_list_and_approve_accounts_without_content_fields() -> None:
    identity = AuthenticatedIdentity(USER, "admin@example.com", True)
    repository = ProfileRepository()
    repository.profiles[0] = repository.profiles[0].model_copy(update={"user_id": OTHER})
    app = create_app(Settings(linksifty_admin_email="admin@example.com"))
    app.dependency_overrides[current_identity] = lambda: identity
    app.state.accounts = AccountService(repository, "admin@example.com")

    with TestClient(app) as client:
        listing = client.get("/v1/admin/accounts")
        approval = client.patch(f"/v1/admin/accounts/{OTHER}", json={"status": "approved"})

    assert listing.status_code == 200
    assert listing.json()[0]["email"] == "user@example.com"
    assert set(listing.json()[0]) == {
        "user_id",
        "email",
        "status",
        "trial_links_used",
        "created_at",
        "approval_email_status",
        "approval_email_failure_code",
    }
    assert approval.status_code == 200
    assert approval.json()["account"]["status"] == "approved"


def test_regular_user_cannot_list_admin_accounts() -> None:
    identity = AuthenticatedIdentity(USER, "user@example.com", True)
    app = create_app(Settings(linksifty_admin_email="admin@example.com"))
    app.dependency_overrides[current_identity] = lambda: identity
    app.state.accounts = AccountService(ProfileRepository(), "admin@example.com")

    with TestClient(app) as client:
        response = client.get("/v1/admin/accounts")

    assert response.status_code == 403


def test_admin_cannot_change_the_initial_admin_account() -> None:
    identity = AuthenticatedIdentity(USER, "admin@example.com", True)
    app = create_app(Settings(linksifty_admin_email="admin@example.com"))
    app.dependency_overrides[current_identity] = lambda: identity
    app.state.accounts = AccountService(ProfileRepository(), "admin@example.com")

    with TestClient(app) as client:
        response = client.patch(f"/v1/admin/accounts/{USER}", json={"status": "rejected"})

    assert response.status_code == 409
