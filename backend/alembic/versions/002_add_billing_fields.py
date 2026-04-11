"""Add billing fields to tenants table.

Revision ID: 002
Revises: 001
Create Date: 2026-03-30

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("stripe_customer_id", sa.String(255), unique=True, nullable=True))
    op.add_column("tenants", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))
    op.add_column("tenants", sa.Column("plan", sa.String(50), nullable=False, server_default="free"))
    op.add_column("tenants", sa.Column("subscription_status", sa.String(50), nullable=False, server_default="none"))
    op.add_column("tenants", sa.Column("subscription_current_period_end", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenants", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenants", sa.Column("monthly_request_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tenants", sa.Column("request_count_reset_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "request_count_reset_at")
    op.drop_column("tenants", "monthly_request_count")
    op.drop_column("tenants", "trial_ends_at")
    op.drop_column("tenants", "subscription_current_period_end")
    op.drop_column("tenants", "subscription_status")
    op.drop_column("tenants", "plan")
    op.drop_column("tenants", "stripe_subscription_id")
    op.drop_column("tenants", "stripe_customer_id")
