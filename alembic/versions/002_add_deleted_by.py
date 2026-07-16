"""Add deleted_by column to diagnostics

Revision ID: 002
Revises: 001
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("diagnostics") as batch_op:
        batch_op.add_column(
            sa.Column("deleted_by", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_diagnostics_deleted_by_users", "users", ["deleted_by"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("diagnostics") as batch_op:
        batch_op.drop_constraint("fk_diagnostics_deleted_by_users", type_="foreignkey")
        batch_op.drop_column("deleted_by")
