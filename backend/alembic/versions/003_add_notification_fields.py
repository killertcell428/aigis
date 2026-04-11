"""Add notification fields to tenants table.

Revision ID: 003
Revises: 002
Create Date: 2026-03-30

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("slack_webhook_url", sa.String(500), nullable=True))
    op.add_column("tenants", sa.Column("notify_on_block", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("tenants", sa.Column("notify_on_high_risk", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("tenants", "notify_on_high_risk")
    op.drop_column("tenants", "notify_on_block")
    op.drop_column("tenants", "slack_webhook_url")
