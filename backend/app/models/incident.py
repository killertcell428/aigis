"""Incident model — tracks security incidents from detection to resolution."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Incident(Base):
    """A security incident created when threats are detected.

    Lifecycle: open -> investigating -> mitigated -> closed
    """

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )

    # Identifiers
    incident_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False
    )  # "INC-2026-0001"

    # Classification
    severity: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # critical | high | medium | low
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # open | investigating | mitigated | closed
    title: Mapped[str] = mapped_column(
        String(300), nullable=False
    )  # e.g. "SQL Injection detected from 192.168.1.1"

    # Link to source request
    request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Snapshot of original request (for replay after approval)
    request_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Scan results
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    matched_rules: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    detection_layers: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Related events
    related_event_ids: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    source_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    trigger_category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Assignment & resolution
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # approved | rejected | allowlisted | blocklisted | escalated | false_positive
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auto-fix suggestion
    suggested_rule: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # SLA
    sla_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sla_met: Mapped[bool | None] = mapped_column(default=None, nullable=True)

    # Timeline (append-only journal)
    timeline: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    # [{timestamp, action, actor, detail}]

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship()
    request: Mapped["Request | None"] = relationship()
    assignee: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:
        return f"<Incident {self.incident_number} status={self.status} severity={self.severity}>"
