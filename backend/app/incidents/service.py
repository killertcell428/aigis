"""Incident service — create and manage security incidents."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.request import Request


async def create_incident(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    request_id: uuid.UUID | None,
    severity: str,
    title: str,
    risk_score: int,
    matched_rules: list[dict],
    source_ip: str | None = None,
    trigger_category: str | None = None,
    request_snapshot: dict | None = None,
    sla_minutes: int = 30,
) -> Incident:
    """Create a new incident from a detected threat.

    Called automatically when CRITICAL/HIGH threats are detected.
    """
    now = datetime.now(timezone.utc)

    # Generate incident number: INC-YYYY-NNNN
    incident_number = await _next_incident_number(db, tenant_id, now)

    # Infer detection layers from matched rules
    layers = set()
    for rule in matched_rules:
        rid = rule.get("rule_id", "")
        if rid.startswith("sim_"):
            layers.add("similarity")
        elif "(decoded)" in rule.get("rule_name", ""):
            layers.add("decoded")
        elif rid:
            layers.add("regex")

    # Find related events (same IP or category in last 24h)
    related_ids = await _find_related_events(
        db, tenant_id, source_ip, trigger_category, now,
    )

    # Initial timeline entry
    timeline = [
        {
            "timestamp": now.isoformat(),
            "action": "detected",
            "actor": "system",
            "detail": f"Threat detected: {title} (score={risk_score})",
        },
    ]

    incident = Incident(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        incident_number=incident_number,
        severity=severity,
        status="open",
        title=title,
        request_id=request_id,
        request_snapshot=request_snapshot,
        risk_score=risk_score,
        matched_rules=matched_rules,
        detection_layers=sorted(layers),
        related_event_ids=[str(rid) for rid in related_ids],
        source_ip=source_ip,
        trigger_category=trigger_category,
        sla_deadline=now + timedelta(minutes=sla_minutes),
        timeline=timeline,
        detected_at=now,
    )

    db.add(incident)
    await db.flush()
    return incident


def add_timeline_entry(
    incident: Incident,
    action: str,
    actor: str,
    detail: str,
) -> None:
    """Append an entry to the incident timeline."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor,
        "detail": detail,
    }
    # JSONB mutation: reassign to trigger SQLAlchemy dirty detection
    incident.timeline = [*incident.timeline, entry]


async def _next_incident_number(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    now: datetime,
) -> str:
    """Generate next incident number for this tenant: INC-YYYY-NNNN."""
    year = now.year
    prefix = f"INC-{year}-"

    result = await db.execute(
        select(func.count())
        .select_from(Incident)
        .where(
            Incident.tenant_id == tenant_id,
            Incident.incident_number.like(f"{prefix}%"),
        )
    )
    count = result.scalar_one()
    return f"{prefix}{count + 1:04d}"


async def _find_related_events(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    source_ip: str | None,
    trigger_category: str | None,
    now: datetime,
) -> list[uuid.UUID]:
    """Find related request IDs from the last 24 hours."""
    cutoff = now - timedelta(hours=24)
    related: list[uuid.UUID] = []

    if not source_ip and not trigger_category:
        return related

    result = await db.execute(
        select(Request.id).where(
            Request.tenant_id == tenant_id,
            Request.created_at >= cutoff,
            Request.status.in_(["blocked", "queued_for_review"]),
        ).limit(20)
    )
    related = [row[0] for row in result.all()]
    return related
