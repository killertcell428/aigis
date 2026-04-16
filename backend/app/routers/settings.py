"""Tenant settings API — notification and enterprise preferences."""
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

    masked_url = None
    if tenant.slack_webhook_url:
        masked_url = "***configured"

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
    await db.commit()

    masked_url = None
    if tenant.slack_webhook_url:
        masked_url = "***configured"

    return NotificationSettingsResponse(
        slack_webhook_url=masked_url,
        notify_on_block=tenant.notify_on_block,
        notify_on_high_risk=tenant.notify_on_high_risk,
    )


# --- Enterprise & Report Settings ---

class EnterpriseSettingsRequest(BaseModel):
    enterprise_mode: bool = False
    weekly_report_enabled: bool = True
    weekly_report_slack: bool = False
    weekly_report_email: Optional[str] = None


class EnterpriseSettingsResponse(BaseModel):
    enterprise_mode: bool
    weekly_report_enabled: bool
    weekly_report_slack: bool
    weekly_report_email: Optional[str] = None


@router.get("/enterprise", response_model=EnterpriseSettingsResponse)
async def get_enterprise_settings(
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnterpriseSettingsResponse:
    """Get enterprise mode and report delivery settings."""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return EnterpriseSettingsResponse(
        enterprise_mode=tenant.enterprise_mode,
        weekly_report_enabled=tenant.weekly_report_enabled,
        weekly_report_slack=tenant.weekly_report_slack,
        weekly_report_email=tenant.weekly_report_email,
    )


@router.put("/enterprise", response_model=EnterpriseSettingsResponse)
async def update_enterprise_settings(
    body: EnterpriseSettingsRequest,
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnterpriseSettingsResponse:
    """Update enterprise mode and report delivery settings."""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.enterprise_mode = body.enterprise_mode
    tenant.weekly_report_enabled = body.weekly_report_enabled
    tenant.weekly_report_slack = body.weekly_report_slack
    tenant.weekly_report_email = body.weekly_report_email or None

    db.add(tenant)
    await db.commit()

    return EnterpriseSettingsResponse(
        enterprise_mode=tenant.enterprise_mode,
        weekly_report_enabled=tenant.weekly_report_enabled,
        weekly_report_slack=tenant.weekly_report_slack,
        weekly_report_email=tenant.weekly_report_email,
    )
