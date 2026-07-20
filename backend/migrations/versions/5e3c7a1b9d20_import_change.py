"""bang tab_import_change (snapshot phieu de revert import)

Revision ID: 5e3c7a1b9d20
Revises: 4d2a6b8c1e9f
Create Date: 2026-07-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "5e3c7a1b9d20"
down_revision: Union[str, None] = "4d2a6b8c1e9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_import_change",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.BigInteger(), nullable=False),
        sa.Column("survey_id", sa.BigInteger(), server_default="0"),
        sa.Column("was_new", sa.SmallInteger(), server_default="0"),
        sa.Column("snapshot", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), server_default="0"),
        sa.Column("updated_by", sa.BigInteger(), server_default="0"),
    )
    op.create_index(op.f("ix_tab_import_change_batch_id"), "tab_import_change", ["batch_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tab_import_change_batch_id"), table_name="tab_import_change")
    op.drop_table("tab_import_change")
