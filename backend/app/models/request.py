"""Request model - every proxied LLM request."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Request(Base):
    """A single proxied LLM API request and its filter outcome."""

    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )

    # Original request metadata
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    messages: Mapped[list] = mapped_column(JSONB, nullable=False)  # OpenAI messages array
    request_headers: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    client_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Input filter result
    input_risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="low"
    )  # low | medium | high | critical
    input_matched_rules: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Routing decision
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    # pending | allowed | blocked | queued_for_review | escalated

    # LLM response (if forwarded)
    response_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Output filter result
    output_risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    output_matched_rules: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Timing
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="requests")
    review_item: Mapped["ReviewItem | None"] = relationship(
        back_populates="request", uselist=False
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="request")

    def __repr__(self) -> str:
        return f"<Request id={self.id} status={self.status} score={self.input_risk_score}>"
