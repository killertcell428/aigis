"""Add enterprise mode and report delivery fields to tenants.

Revision ID: 005
Revises: 004
Create Date: 2026-04-17

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("enterprise_mode", sa.Boolean, server_default="false", nullable=False))
    op.add_column("tenants", sa.Column("weekly_report_enabled", sa.Boolean, server_default="true", nullable=False))
    op.add_column("tenants", sa.Column("weekly_report_slack", sa.Boolean, server_default="false", nullable=False))
    op.add_column("tenants", sa.Column("weekly_report_email", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "weekly_report_email")
    op.drop_column("tenants", "weekly_report_slack")
    op.drop_column("tenants", "weekly_report_enabled")
    op.drop_column("tenants", "enterprise_mode")
