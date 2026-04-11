"""Audit logger: write all events to audit_logs table."""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    event_type: str,
    summary: str,
    details: dict[str, Any] | None = None,
    request_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    severity: str = "info",
) -> AuditLog:
    """Create an immutable audit log entry.

    Args:
        db: Database session.
        tenant_id: Tenant this event belongs to.
        event_type: Dot-separated event type (e.g., "request.blocked").
        summary: Human-readable one-line summary.
        details: Additional structured data.
        request_id: Associated request ID if applicable.
        actor_id: User who triggered the event (None = system).
        severity: info | warning | critical.

    Returns:
        The created AuditLog record.
    """
    entry = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        request_id=request_id,
        actor_id=actor_id,
        event_type=event_type,
        severity=severity,
        summary=summary,
        details=details or {},
    )
    db.add(entry)
    # Flush so the record has an ID, but don't commit—caller owns the transaction.
    await db.flush()
    return entry
