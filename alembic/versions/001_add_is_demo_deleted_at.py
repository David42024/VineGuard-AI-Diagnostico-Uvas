"""Add is_demo and deleted_at columns to diagnostics

Revision ID: 001
Revises:
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("diagnostics") as batch_op:
        batch_op.add_column(sa.Column("is_demo", sa.Integer(), server_default="0"))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("diagnostics") as batch_op:
        batch_op.drop_column("is_demo")
        batch_op.drop_column("deleted_at")
