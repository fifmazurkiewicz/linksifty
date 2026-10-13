"""Verify bearer tokens using Supabase's authenticated user endpoint."""

from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError


class InvalidToken(Exception):
    """The authentication service rejected the supplied token."""


class AuthenticationUnavailable(Exception):
    """No verified identity can be established right now."""


class _UserIdentity(BaseModel):
    id: UUID


class SupabaseAuthenticator:
    """Resolve identities from server validation, never unverified JWT claims."""

    def __init__(self, url: str, api_key: str, client: httpx.AsyncClient) -> None:
        self._url = f"{url.rstrip('/')}/auth/v1/user"
        self._api_key = api_key
        self._client = client

    async def verify(self, token: str) -> UUID:
        try:
            response = await self._client.get(
                self._url,
                headers={"apikey": self._api_key, "Authorization": f"Bearer {token}"},
                timeout=10,
                follow_redirects=False,
            )
        except httpx.HTTPError as error:
            raise AuthenticationUnavailable from error
        if response.status_code in (401, 403):
            raise InvalidToken
        if response.status_code != 200:
            raise AuthenticationUnavailable
        try:
            return _UserIdentity.model_validate_json(response.content).id
        except ValidationError as error:
            raise AuthenticationUnavailable from error
