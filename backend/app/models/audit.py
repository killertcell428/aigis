"""AuditLog model - immutable record of all events."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    """Immutable audit trail for all filter decisions and review actions."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # user who performed the action (null = system)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # request.filtered | request.blocked | request.allowed | request.queued
    # review.approved | review.rejected | review.escalated | review.timed_out
    # policy.updated | user.login | api_key.created

    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info"
    )  # info | warning | critical

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="audit_logs")
    request: Mapped["Request | None"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} event={self.event_type}>"
