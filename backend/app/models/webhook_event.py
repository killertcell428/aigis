"""WebhookEvent model — idempotency ledger for external webhooks (Stripe)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebhookEvent(Base):
    """Records processed webhook event IDs to prevent replay / duplicate processing."""

    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Source system ("stripe", "github", ...). Composite uniqueness with event_id.
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    # Provider-assigned event ID (e.g. Stripe "evt_...").
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<WebhookEvent source={self.source} id={self.event_id}>"
