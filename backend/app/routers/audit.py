"""Audit log router: searchable log viewer."""
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    request_id: uuid.UUID | None
    actor_id: uuid.UUID | None
    event_type: str
    severity: str
    summary: str
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    event_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[AuditLog]:
    """List audit logs for the current tenant with optional filters."""
    query = select(AuditLog).where(AuditLog.tenant_id == current_user.tenant_id)

    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if severity:
        query = query.where(AuditLog.severity == severity)

    query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())
