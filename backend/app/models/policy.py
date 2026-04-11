"""Policy model - per-tenant filter configuration."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Policy(Base):
    """Filter policy for a specific tenant."""

    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Risk thresholds override
    auto_allow_threshold: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    auto_block_threshold: Mapped[int] = mapped_column(Integer, default=81, nullable=False)
    review_sla_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    sla_fallback: Mapped[str] = mapped_column(
        String(20), default="block", nullable=False
    )  # block | allow | escalate

    # Custom rules as JSON array
    # Each rule: {"id": str, "name": str, "pattern": str, "score_delta": int, "enabled": bool}
    custom_rules: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="policies")

    def __repr__(self) -> str:
        return f"<Policy id={self.id} name={self.name}>"
