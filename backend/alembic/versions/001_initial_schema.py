"""Initial schema: tenants, users, policies, requests, review_items, audit_logs.

Revision ID: 001
Revises:
Create Date: 2026-03-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- tenants ---
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="reviewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("api_key_hash", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    # --- policies ---
    op.create_table(
        "policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("auto_allow_threshold", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("auto_block_threshold", sa.Integer(), nullable=False, server_default="81"),
        sa.Column("review_sla_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("sla_fallback", sa.String(20), nullable=False, server_default="block"),
        sa.Column("custom_rules", JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_policies_tenant_id", "policies", ["tenant_id"])

    # --- requests ---
    op.create_table(
        "requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("messages", JSONB(), nullable=False),
        sa.Column("request_headers", JSONB(), nullable=False, server_default="{}"),
        sa.Column("client_ip", sa.String(50), nullable=True),
        sa.Column("input_risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_risk_level", sa.String(20), nullable=False, server_default="low"),
        sa.Column("input_matched_rules", JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("response_body", JSONB(), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("output_risk_score", sa.Integer(), nullable=True),
        sa.Column("output_risk_level", sa.String(20), nullable=True),
        sa.Column("output_matched_rules", JSONB(), nullable=False, server_default="[]"),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_requests_tenant_id", "requests", ["tenant_id"])
    op.create_index("ix_requests_status", "requests", ["status"])
    op.create_index("ix_requests_created_at", "requests", ["created_at"])

    # --- review_items ---
    op.create_table(
        "review_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requests.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "reviewer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decision", sa.String(30), nullable=True),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_review_items_status", "review_items", ["status"])
    op.create_index("ix_review_items_sla_deadline", "review_items", ["sla_deadline"])

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_id", UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("details", JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("review_items")
    op.drop_table("requests")
    op.drop_table("policies")
    op.drop_table("users")
    op.drop_table("tenants")
