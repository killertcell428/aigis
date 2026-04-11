"""Tenant settings API — notification preferences."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_admin_user
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class NotificationSettingsRequest(BaseModel):
    slack_webhook_url: Optional[str] = None
    notify_on_block: bool = True
    notify_on_high_risk: bool = False


class NotificationSettingsResponse(BaseModel):
    slack_webhook_url: Optional[str] = None
    notify_on_block: bool
    notify_on_high_risk: bool


@router.get("/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationSettingsResponse:
    """Get current notification settings for the tenant."""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Mask the webhook URL for security (show only last 8 chars)
    masked_url = None
    if tenant.slack_webhook_url:
        masked_url = f"***{tenant.slack_webhook_url[-8:]}"

    return NotificationSettingsResponse(
        slack_webhook_url=masked_url,
        notify_on_block=tenant.notify_on_block,
        notify_on_high_risk=tenant.notify_on_high_risk,
    )


@router.put("/notifications", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    body: NotificationSettingsRequest,
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationSettingsResponse:
    """Update notification settings for the tenant."""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if body.slack_webhook_url is not None:
        tenant.slack_webhook_url = body.slack_webhook_url if body.slack_webhook_url else None
    tenant.notify_on_block = body.notify_on_block
    tenant.notify_on_high_risk = body.notify_on_high_risk

    db.add(tenant)

    masked_url = None
    if tenant.slack_webhook_url:
        masked_url = f"***{tenant.slack_webhook_url[-8:]}"

    return NotificationSettingsResponse(
        slack_webhook_url=masked_url,
        notify_on_block=tenant.notify_on_block,
        notify_on_high_risk=tenant.notify_on_high_risk,
    )
