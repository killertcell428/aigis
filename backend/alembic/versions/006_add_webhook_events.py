"""Add webhook_events table for idempotency ledger.

Revision ID: 006
Revises: 005
Create Date: 2026-04-17

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_webhook_events_source_event_id",
        "webhook_events",
        ["source", "event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_events_source_event_id", table_name="webhook_events")
    op.drop_table("webhook_events")
