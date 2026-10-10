"""yeu cau bao gia: xoa mem (ai-CR-170)

Revision ID: grp11
Revises: grp10

Ba cot cua `SoftDeleteMixin` (core/base_model.py) cho `tab_survey_request`:
is_deleted 0/1 (co chi muc) · deleted_at · deleted_by. Phieu da xoa van nam trong bang;
`core/scoping.apply_scope` / `get_scoped` tu giau.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp11"
down_revision: Union[str, None] = "grp10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_survey_request"
INDEX = "ix_tab_survey_request_is_deleted"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.add_column(TABLE, sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column(TABLE, sa.Column("deleted_by", sa.BigInteger(), nullable=False, server_default=sa.text("0")))
    op.create_index(INDEX, TABLE, ["is_deleted"])


def downgrade() -> None:
    op.drop_index(INDEX, table_name=TABLE)
    op.drop_column(TABLE, "deleted_by")
    op.drop_column(TABLE, "deleted_at")
    op.drop_column(TABLE, "is_deleted")
