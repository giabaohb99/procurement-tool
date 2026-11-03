"""nghi phep cap quy kieu ERPNext: 3 cot luat tren tab_leave_type + bang tab_leave_type_quota (duoc-CR-715)

Revision ID: lvacc715
Revises: jobrun01

Mac dinh cua ba cot moi (accrual_mode=1, applicable_after_days=0, max_negative_days=0) giu NGUYEN hanh vi cu.
Chi tao khi thieu (chay lai duoc).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "lvacc715"
down_revision: Union[str, None] = "jobrun01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TYPE_TABLE = "tab_leave_type"
QUOTA_TABLE = "tab_leave_type_quota"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    cols = {c["name"] for c in inspector.get_columns(TYPE_TABLE)}
    if "accrual_mode" not in cols:
        op.add_column(TYPE_TABLE, sa.Column("accrual_mode", sa.SmallInteger(), nullable=False,
                                            server_default="1"))
    if "applicable_after_days" not in cols:
        op.add_column(TYPE_TABLE, sa.Column("applicable_after_days", sa.Integer(), nullable=False,
                                            server_default="0"))
    if "max_negative_days" not in cols:
        op.add_column(TYPE_TABLE, sa.Column("max_negative_days", sa.Float(), nullable=False,
                                            server_default="0"))

    if QUOTA_TABLE in inspector.get_table_names():
        return
    op.create_table(
        QUOTA_TABLE,
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("leave_type_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("basis", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("basis_value", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("quota_days", sa.Float(), nullable=False, server_default="0"),
        sa.UniqueConstraint("leave_type_id", "basis", "basis_value", name="uq_leave_quota_type_basis"),
    )
    op.create_index("ix_tab_leave_type_quota_leave_type_id", QUOTA_TABLE, ["leave_type_id"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if QUOTA_TABLE in inspector.get_table_names():
        op.drop_table(QUOTA_TABLE)
    cols = {c["name"] for c in inspector.get_columns(TYPE_TABLE)}
    for name in ("max_negative_days", "applicable_after_days", "accrual_mode"):
        if name in cols:
            op.drop_column(TYPE_TABLE, name)
