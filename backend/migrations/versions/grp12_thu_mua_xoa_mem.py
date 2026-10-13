"""cum thu mua: xoa mem DMH / YCTT / PKS (ai-CR-176)

Revision ID: grp12
Revises: grp11

Ba cot cua `SoftDeleteMixin` (core/base_model.py) cho `tab_purchase_order`, `tab_payment_request`,
`tab_survey`: is_deleted 0/1 (co chi muc) · deleted_at · deleted_by. Phieu da xoa van nam trong bang
(dong con / dinh kem giu nguyen); `core/scoping.apply_scope` / `get_scoped` tu giau.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp12"
down_revision: Union[str, None] = "grp11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("tab_purchase_order", "tab_payment_request", "tab_survey")


def _index_name(table: str) -> str:
    return f"ix_{table}_is_deleted"


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(), nullable=True))
        op.add_column(table, sa.Column("deleted_by", sa.BigInteger(), nullable=False, server_default=sa.text("0")))
        op.create_index(_index_name(table), table, ["is_deleted"])


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(_index_name(table), table_name=table)
        op.drop_column(table, "deleted_by")
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "is_deleted")
