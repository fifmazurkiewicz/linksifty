"""Authenticated account self-service endpoints."""

from fastapi import APIRouter, HTTPException, Request

from linksifty.api.auth import CurrentIdentity
from linksifty.application.account_contracts import AccountService, AccountSummary

router = APIRouter()


@router.get("/v1/me", response_model=AccountSummary)
async def get_my_account(request: Request, identity: CurrentIdentity) -> AccountSummary:
    """Return only the verified caller's account status and trial allowance."""
    if request.app.state.settings.demo_mode:
        return AccountSummary(
            user_id=identity.user_id,
            email=identity.email,
            status="approved",
            role="user",
            trial_links_used=0,
            trial_links_remaining=3,
        )
    service: AccountService | None = request.app.state.accounts
    if service is None:
        raise HTTPException(503, "Account access is not configured")
    return await service.profile(identity)
