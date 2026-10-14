"""Resolve authenticated identities before entering application services."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from linksifty.application.account_contracts import AccountService, AuthenticatedIdentity
from linksifty.config import Settings
from linksifty.infrastructure.supabase_auth import (
    AuthenticationUnavailable,
    InvalidToken,
    SupabaseAuthenticator,
)

_bearer = HTTPBearer(auto_error=False)
_demo_user = UUID("00000000-0000-4000-8000-000000000001")


async def current_identity(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthenticatedIdentity:
    settings: Settings = request.app.state.settings
    if settings.demo_mode:
        return AuthenticatedIdentity(_demo_user, "demo@linksifty.local", True)
    if credentials is None:
        raise HTTPException(401, "Sign in to continue", headers={"WWW-Authenticate": "Bearer"})
    authenticator: SupabaseAuthenticator | None = request.app.state.authenticator
    if authenticator is None:
        raise HTTPException(503, "Authentication is not configured")
    try:
        identity = await authenticator.verify(credentials.credentials)
        if not identity.email_verified:
            raise InvalidToken
        return identity
    except InvalidToken as error:
        raise HTTPException(
            401, "Session expired or invalid", headers={"WWW-Authenticate": "Bearer"}
        ) from error
    except AuthenticationUnavailable as error:
        raise HTTPException(503, "Authentication temporarily unavailable") from error


async def current_user(
    request: Request,
    identity: Annotated[AuthenticatedIdentity, Depends(current_identity)],
) -> UUID:
    settings: Settings = request.app.state.settings
    if settings.demo_mode:
        return identity.user_id
    accounts: AccountService | None = request.app.state.accounts
    if accounts is None:
        raise HTTPException(503, "Account access is not configured")
    profile = await accounts.profile(identity)
    if profile.status == "rejected":
        raise HTTPException(403, "This account is not approved")
    return identity.user_id


CurrentIdentity = Annotated[AuthenticatedIdentity, Depends(current_identity)]
CurrentUser = Annotated[UUID, Depends(current_user)]
