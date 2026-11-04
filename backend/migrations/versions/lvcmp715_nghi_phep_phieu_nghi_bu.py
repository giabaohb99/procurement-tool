"""nghi phep phieu nghi bu: tab_leave_comp_request + is_compensatory + comp_days (duoc-CR-715 C)

Revision ID: lvcmp715
Revises: lvblk715

Chi them khi thieu (chay lai duoc).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "lvcmp715"
down_revision: Union[str, None] = "lvblk715"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_leave_comp_request"
INDEX = "ix_leave_comp_emp_date"


def _has_column(inspector, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_column(inspector, "tab_leave_type", "is_compensatory"):
        op.add_column("tab_leave_type", sa.Column(
            "is_compensatory", sa.Boolean(), nullable=False, server_default=sa.false()))
    if not _has_column(inspector, "tab_leave_balance", "comp_days"):
        op.add_column("tab_leave_balance", sa.Column(
            "comp_days", sa.Float(), nullable=False, server_default="0"))
    if TABLE in inspector.get_table_names():
        return
    op.create_table(
        TABLE,
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("code", sa.String(30), nullable=False, unique=True),
        sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("employee_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("days", sa.Float(), nullable=False, server_default="1"),
        sa.Column("reason", sa.String(1000), nullable=False, server_default=""),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("approval_instance_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decision_note", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(INDEX, TABLE, ["employee_id", "work_date"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if TABLE in inspector.get_table_names():
        op.drop_table(TABLE)
    if _has_column(inspector, "tab_leave_balance", "comp_days"):
        op.drop_column("tab_leave_balance", "comp_days")
    if _has_column(inspector, "tab_leave_type", "is_compensatory"):
        op.drop_column("tab_leave_type", "is_compensatory")
