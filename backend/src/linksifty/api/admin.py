"""Administrator-only account state endpoints."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from linksifty.api.auth import CurrentIdentity
from linksifty.application.account_contracts import (
    AccountAccessDenied,
    AccountNotFound,
    AccountProfile,
    AccountService,
    AdminAccountSummary,
    EmailDeliveryStatus,
    InitialAdminProtected,
)

router = APIRouter(prefix="/v1/admin")


class AccountStatusUpdate(BaseModel):
    status: Literal["approved", "rejected"]


class AccountActionResponse(BaseModel):
    account: AccountProfile
    approval_email_status: EmailDeliveryStatus | None = None
    approval_email_failure_code: str | None = None


class ApprovalEmailRetryResponse(BaseModel):
    status: EmailDeliveryStatus
    failure_code: str | None = None


def _service(request: Request) -> AccountService:
    service: AccountService | None = request.app.state.accounts
    if service is None:
        raise HTTPException(503, "Account access is not configured")
    return service


@router.get("/accounts", response_model=list[AdminAccountSummary])
async def list_accounts(request: Request, identity: CurrentIdentity) -> list[AdminAccountSummary]:
    """List account metadata only; never include user-owned content."""
    try:
        return await _service(request).list_accounts(identity)
    except AccountAccessDenied as error:
        raise HTTPException(403, "Administrator access required") from error


@router.patch("/accounts/{user_id}", response_model=AccountActionResponse)
async def set_account_status(
    user_id: UUID,
    update: AccountStatusUpdate,
    request: Request,
    identity: CurrentIdentity,
) -> AccountActionResponse:
    """Approve or reject an account without accessing its links or assessments."""
    try:
        _, profile, email_status, failure_code = await _service(request).set_status(
            identity, user_id, update.status
        )
        return AccountActionResponse(
            account=profile,
            approval_email_status=email_status,
            approval_email_failure_code=failure_code,
        )
    except AccountAccessDenied as error:
        raise HTTPException(403, "Administrator access required") from error
    except InitialAdminProtected as error:
        raise HTTPException(409, "The initial administrator cannot be changed") from error
    except AccountNotFound as error:
        raise HTTPException(404, "Account not found") from error


@router.post("/accounts/{user_id}/approval-email/retry", response_model=ApprovalEmailRetryResponse)
async def retry_approval_email(
    user_id: UUID, request: Request, identity: CurrentIdentity
) -> ApprovalEmailRetryResponse:
    """Explicitly retry the latest approval notification for a user."""
    try:
        result = await _service(request).retry_approval_email(identity, user_id)
    except AccountAccessDenied as error:
        raise HTTPException(403, "Administrator access required") from error
    if result is None:
        raise HTTPException(404, "No approval notification exists")
    status, failure_code = result
    return ApprovalEmailRetryResponse(status=status, failure_code=failure_code)
