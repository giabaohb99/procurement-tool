"""van thu / nhan su: xoa mem hop dong NCC, van ban, HDLD, ho so (ai-CR-177)

Revision ID: grp13
Revises: grp12

Ba cot cua `SoftDeleteMixin` (core/base_model.py) cho bon bang CHA:
tab_contract · tab_document · tab_labor_contract · tab_dossier —
is_deleted 0/1 (co chi muc) · deleted_at · deleted_by. Dong con / phien ban / tep / quan he
giu nguyen; `core/scoping.apply_scope` / `get_scoped` va `document/query.documents_query` tu giau.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp13"
down_revision: Union[str, None] = "grp12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("tab_contract", "tab_document", "tab_labor_contract", "tab_dossier")


def _index_name(table: str) -> str:
    return f"ix_{table}_is_deleted"


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column("is_deleted", sa.Boolean(), nullable=False,
                                       server_default=sa.text("0")))
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(), nullable=True))
        op.add_column(table, sa.Column("deleted_by", sa.BigInteger(), nullable=False,
                                       server_default=sa.text("0")))
        op.create_index(_index_name(table), table, ["is_deleted"])


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(_index_name(table), table_name=table)
        op.drop_column(table, "deleted_by")
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "is_deleted")
