"""Create incidents table for incident lifecycle management.

Revision ID: 004
Revises: 003
Create Date: 2026-04-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("incident_number", sa.String(30), unique=True, nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("request_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("risk_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("matched_rules", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("detection_layers", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("related_event_ids", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("source_ip", sa.String(50), nullable=True),
        sa.Column("trigger_category", sa.String(100), nullable=True),
        sa.Column(
            "assigned_to",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolution", sa.String(50), nullable=True),
        sa.Column("resolution_note", sa.Text, nullable=True),
        sa.Column("suggested_rule", postgresql.JSONB, nullable=True),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_met", sa.Boolean, nullable=True),
        sa.Column("timeline", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_incidents_tenant_status", "incidents", ["tenant_id", "status"])
    op.create_index("idx_incidents_severity", "incidents", ["severity"])
    op.create_index("idx_incidents_detected_at", "incidents", ["detected_at"])


def downgrade() -> None:
    op.drop_index("idx_incidents_detected_at")
    op.drop_index("idx_incidents_severity")
    op.drop_index("idx_incidents_tenant_status")
    op.drop_table("incidents")
