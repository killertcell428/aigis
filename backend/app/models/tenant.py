"""Tenant model - represents an organization using Aigis."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tenant(Base):
    """An organization/customer that uses Aigis."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Billing
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    plan: Mapped[str] = mapped_column(
        String(50), default="free", server_default="free", nullable=False
    )
    subscription_status: Mapped[str] = mapped_column(
        String(50), default="none", server_default="none", nullable=False
    )
    subscription_current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    monthly_request_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    request_count_reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Notifications
    slack_webhook_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    notify_on_block: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    notify_on_high_risk: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="tenant", lazy="selectin")
    policies: Mapped[list["Policy"]] = relationship(back_populates="tenant", lazy="selectin")
    requests: Mapped[list["Request"]] = relationship(back_populates="tenant")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="tenant")

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug}>"
