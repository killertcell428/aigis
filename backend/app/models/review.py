"""ReviewItem model - human review queue entries."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReviewItem(Base):
    """A request queued for human review."""

    __tablename__ = "review_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    # pending | approved | rejected | escalated | timed_out

    # SLA deadline - set when item is created
    sla_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Review outcome
    decision: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # approve | reject | escalate
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    request: Mapped["Request"] = relationship(back_populates="review_item")
    reviewer: Mapped["User | None"] = relationship(back_populates="review_items")

    def __repr__(self) -> str:
        return f"<ReviewItem id={self.id} status={self.status}>"
