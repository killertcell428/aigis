"""Billing API endpoints for subscription management."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.plans import get_plan_limits
from app.billing.stripe_client import (
    create_checkout_session,
    create_customer_portal_session,
    get_subscription_status,
)
from app.db.session import get_db
from app.dependencies import get_admin_user, get_current_user
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


# --- Schemas ---


class CheckoutRequest(BaseModel):
    plan: str  # "pro" or "business"
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    url: str


class SubscriptionStatusResponse(BaseModel):
    plan: str
    status: str
    trial_ends_at: datetime | None = None
    current_period_end: datetime | None = None


class UsageResponse(BaseModel):
    plan: str
    monthly_requests_used: int
    monthly_requests_limit: int | None
    team_size: int
    team_limit: int | None
    retention_days: int | None


# --- Endpoints ---


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CheckoutResponse:
    """Create a Stripe Checkout session for plan subscription."""
    if body.plan not in ("pro", "business"):
        raise HTTPException(status_code=400, detail="Plan must be 'pro' or 'business'")

    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    session = create_checkout_session(
        customer_email=current_user.email,
        plan=body.plan,
        tenant_id=str(tenant.id),
        success_url=body.success_url,
        cancel_url=body.cancel_url,
    )
    return CheckoutResponse(url=session.url)


@router.post("/portal", response_model=CheckoutResponse)
async def create_portal(
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CheckoutResponse:
    """Create a Stripe Customer Portal session for self-service management."""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant or not tenant.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    session = create_customer_portal_session(
        customer_id=tenant.stripe_customer_id,
        return_url="",  # Frontend will provide via query param
    )
    return CheckoutResponse(url=session.url)


@router.get("/status", response_model=SubscriptionStatusResponse)
async def billing_status(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SubscriptionStatusResponse:
    """Get the current subscription status for the user's tenant."""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return SubscriptionStatusResponse(
        plan=tenant.plan,
        status=tenant.subscription_status,
        trial_ends_at=tenant.trial_ends_at,
        current_period_end=tenant.subscription_current_period_end,
    )


@router.get("/usage", response_model=UsageResponse)
async def billing_usage(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsageResponse:
    """Get current usage metrics for the user's tenant."""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Count active team members
    result = await db.execute(
        select(func.count()).select_from(User).where(
            User.tenant_id == tenant.id,
            User.is_active == True,
        )
    )
    team_size = result.scalar() or 0

    limits = get_plan_limits(tenant.plan)

    return UsageResponse(
        plan=tenant.plan,
        monthly_requests_used=tenant.monthly_request_count,
        monthly_requests_limit=limits["monthly_requests"],
        team_size=team_size,
        team_limit=limits["max_users"],
        retention_days=limits["retention_days"],
    )
