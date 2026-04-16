"""Incidents API — incident lifecycle management endpoints."""

import uuid as uuid_mod
from datetime import datetime, timezone
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.incidents.service import add_timeline_entry
from app.models.incident import Incident
from app.models.user import User

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])

MAX_NOTE_LENGTH = 5000


# === Request schemas ===

class StatusUpdate(BaseModel):
    status: Literal["investigating", "mitigated", "closed"]
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class AssignRequest(BaseModel):
    user_id: uuid_mod.UUID


class NoteRequest(BaseModel):
    note: str = Field(..., min_length=1, max_length=MAX_NOTE_LENGTH)


class ResolveRequest(BaseModel):
    resolution: Literal["approved", "rejected", "allowlisted", "blocklisted", "false_positive", "escalated"]
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


# === Endpoints ===

@router.get("")
async def list_incidents(
    status: str | None = Query(None),
    severity: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """List incidents for the current tenant."""
    query = select(Incident).where(Incident.tenant_id == user.tenant_id)

    if status:
        query = query.where(Incident.status == status)
    if severity:
        query = query.where(Incident.severity == severity)

    query = query.order_by(Incident.detected_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    incidents = result.scalars().all()

    return JSONResponse([_serialize(inc) for inc in incidents])


@router.get("/stats")
async def incident_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Get incident count by status."""
    result = await db.execute(
        select(Incident).where(Incident.tenant_id == user.tenant_id)
    )
    incidents = result.scalars().all()

    stats = {"open": 0, "investigating": 0, "mitigated": 0, "closed": 0}
    for inc in incidents:
        if inc.status in stats:
            stats[inc.status] += 1

    return JSONResponse({
        "total": len(incidents),
        **stats,
    })


@router.get("/{incident_id}")
async def get_incident(
    incident_id: uuid_mod.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Get a single incident with full details."""
    inc = await _get_incident(db, incident_id, user.tenant_id)
    return JSONResponse(_serialize(inc))


@router.post("/{incident_id}/status")
async def update_status(
    incident_id: uuid_mod.UUID,
    body: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Update incident status (investigating / mitigated / closed)."""
    inc = await _get_incident(db, incident_id, user.tenant_id)

    valid_transitions = {
        "open": ["investigating", "mitigated", "closed"],
        "investigating": ["mitigated", "closed"],
        "mitigated": ["closed"],
        "closed": [],
    }
    allowed = valid_transitions.get(inc.status, [])
    if body.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{inc.status}' to '{body.status}'. Allowed: {allowed}",
        )

    now = datetime.now(timezone.utc)
    inc.status = body.status

    if body.status == "investigating":
        inc.responded_at = now
    elif body.status == "mitigated":
        inc.resolved_at = now
        if inc.sla_deadline:
            inc.sla_met = now <= inc.sla_deadline
    elif body.status == "closed":
        if not inc.resolved_at:
            inc.resolved_at = now
            if inc.sla_deadline:
                inc.sla_met = now <= inc.sla_deadline
        inc.closed_at = now

    add_timeline_entry(
        inc,
        action=f"status_change:{body.status}",
        actor=user.email,
        detail=body.note or f"Status changed to {body.status}",
    )

    db.add(inc)
    await db.commit()
    return JSONResponse(_serialize(inc))


@router.post("/{incident_id}/assign")
async def assign_incident(
    incident_id: uuid_mod.UUID,
    body: AssignRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Assign an incident to a user."""
    inc = await _get_incident(db, incident_id, user.tenant_id)
    # Verify target user belongs to same tenant
    target = await db.execute(
        select(User).where(User.id == body.user_id, User.tenant_id == user.tenant_id)
    )
    if not target.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User not found in this tenant")
    inc.assigned_to = body.user_id

    add_timeline_entry(
        inc,
        action="assigned",
        actor=user.email,
        detail=f"Assigned to {body.user_id}",
    )

    db.add(inc)
    await db.commit()
    return JSONResponse(_serialize(inc))


@router.post("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: uuid_mod.UUID,
    body: ResolveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Resolve an incident with a specific resolution type."""
    inc = await _get_incident(db, incident_id, user.tenant_id)

    if inc.status == "closed":
        raise HTTPException(status_code=400, detail="Incident is already closed")

    now = datetime.now(timezone.utc)
    inc.resolution = body.resolution
    inc.resolution_note = body.note
    inc.status = "mitigated"
    inc.resolved_at = now
    if inc.sla_deadline:
        inc.sla_met = now <= inc.sla_deadline

    add_timeline_entry(
        inc,
        action=f"resolved:{body.resolution}",
        actor=user.email,
        detail=body.note or f"Resolved as {body.resolution}",
    )

    db.add(inc)
    await db.commit()
    return JSONResponse(_serialize(inc))


@router.post("/{incident_id}/note")
async def add_note(
    incident_id: uuid_mod.UUID,
    body: NoteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Add a note to the incident timeline."""
    inc = await _get_incident(db, incident_id, user.tenant_id)

    add_timeline_entry(
        inc,
        action="note",
        actor=user.email,
        detail=body.note,
    )

    db.add(inc)
    await db.commit()
    return JSONResponse(_serialize(inc))


# === Helpers ===

async def _get_incident(db: AsyncSession, incident_id: uuid_mod.UUID, tenant_id) -> Incident:
    result = await db.execute(
        select(Incident).where(
            Incident.id == incident_id,
            Incident.tenant_id == tenant_id,
        )
    )
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


def _serialize(inc: Incident) -> dict[str, Any]:
    return {
        "id": str(inc.id),
        "incident_number": inc.incident_number,
        "severity": inc.severity,
        "status": inc.status,
        "title": inc.title,
        "request_id": str(inc.request_id) if inc.request_id else None,
        "risk_score": inc.risk_score,
        "matched_rules": [
            {k: v for k, v in rule.items() if k != "matched_text"}
            for rule in (inc.matched_rules or [])
        ],
        "detection_layers": inc.detection_layers,
        "source_ip": inc.source_ip,
        "trigger_category": inc.trigger_category,
        "assigned_to": str(inc.assigned_to) if inc.assigned_to else None,
        "resolution": inc.resolution,
        "resolution_note": inc.resolution_note,
        "sla_deadline": inc.sla_deadline.isoformat() if inc.sla_deadline else None,
        "sla_met": inc.sla_met,
        "timeline": inc.timeline,
        "related_event_ids": inc.related_event_ids,
        "detected_at": inc.detected_at.isoformat() if inc.detected_at else None,
        "responded_at": inc.responded_at.isoformat() if inc.responded_at else None,
        "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
        "closed_at": inc.closed_at.isoformat() if inc.closed_at else None,
    }
