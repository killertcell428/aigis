"""Plan enforcement utilities for Aigis SaaS.

In 'warn' mode (default during beta), violations are logged but not blocked.
In 'strict' mode, violations return HTTP 402/403/429.
"""
import logging
from datetime import datetime, timezone
from typing import Annotated, Callable

from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.plans import get_plan_limits, is_plan_at_least
from app.config import settings
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User

logger = logging.getLogger(__name__)


def _is_strict() -> bool:
    return settings.billing_enforcement_mode == "strict"


async def check_request_quota(
    tenant: Tenant,
    db: AsyncSession,
) -> None:
    """Check if the tenant is within their monthly request quota.

    Increments the counter and resets it on month boundary.
    """
    limits = get_plan_limits(tenant.plan)
    monthly_limit = limits["monthly_requests"]

    # Unlimited plans (None or 0 for free with no cloud access)
    if monthly_limit is None:
        return

    # Reset counter on month boundary
    now = datetime.now(timezone.utc)
    if tenant.request_count_reset_at is None or tenant.request_count_reset_at.month != now.month:
        tenant.monthly_request_count = 0
        tenant.request_count_reset_at = now

    if tenant.monthly_request_count >= monthly_limit:
        msg = f"Tenant {tenant.slug} exceeded monthly request quota ({monthly_limit})"
        if _is_strict():
            logger.warning(msg)
            raise HTTPException(
                status_code=429,
                detail=f"Monthly request limit ({monthly_limit:,}) exceeded. Upgrade your plan.",
            )
        else:
            logger.info("[warn mode] %s", msg)

    tenant.monthly_request_count += 1


async def check_user_limit(
    tenant: Tenant,
    db: AsyncSession,
) -> None:
    """Check if the tenant can add more users."""
    limits = get_plan_limits(tenant.plan)
    max_users = limits["max_users"]
    if max_users is None:
        return

    result = await db.execute(
        select(func.count()).select_from(User).where(
            User.tenant_id == tenant.id,
            User.is_active == True,
        )
    )
    current_count = result.scalar() or 0

    if current_count >= max_users:
        msg = f"Tenant {tenant.slug} at user limit ({max_users})"
        if _is_strict():
            logger.warning(msg)
            raise HTTPException(
                status_code=403,
                detail=f"Team member limit ({max_users}) reached. Upgrade your plan.",
            )
        else:
            logger.info("[warn mode] %s", msg)


def require_plan(minimum_plan: str) -> Callable:
    """FastAPI dependency factory: require a minimum plan tier.

    Usage:
        @router.get("/reports", dependencies=[Depends(require_plan("business"))])
    """
    # Import here to avoid circular dependency at module load time
    from app.dependencies import get_current_user

    async def _check_plan(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> None:
        tenant = await db.get(Tenant, user.tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        if not is_plan_at_least(tenant.plan, minimum_plan):
            msg = f"Tenant {tenant.slug} requires {minimum_plan} plan (current: {tenant.plan})"
            if _is_strict():
                logger.warning(msg)
                raise HTTPException(
                    status_code=403,
                    detail=f"This feature requires the {minimum_plan.title()} plan or higher.",
                )
            else:
                logger.info("[warn mode] %s", msg)

    return _check_plan
