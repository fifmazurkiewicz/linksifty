"""Resolve authenticated identities before entering application services."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from linksifty.config import Settings
from linksifty.infrastructure.supabase_auth import (
    AuthenticationUnavailable,
    InvalidToken,
    SupabaseAuthenticator,
)

_bearer = HTTPBearer(auto_error=False)
_demo_user = UUID("00000000-0000-4000-8000-000000000001")


async def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UUID:
    settings: Settings = request.app.state.settings
    if settings.demo_mode:
        return _demo_user
    if credentials is None:
        raise HTTPException(401, "Sign in to continue", headers={"WWW-Authenticate": "Bearer"})
    authenticator: SupabaseAuthenticator | None = request.app.state.authenticator
    if authenticator is None:
        raise HTTPException(503, "Authentication is not configured")
    try:
        return await authenticator.verify(credentials.credentials)
    except InvalidToken as error:
        raise HTTPException(
            401, "Session expired or invalid", headers={"WWW-Authenticate": "Bearer"}
        ) from error
    except AuthenticationUnavailable as error:
        raise HTTPException(503, "Authentication temporarily unavailable") from error


CurrentUser = Annotated[UUID, Depends(current_user)]
