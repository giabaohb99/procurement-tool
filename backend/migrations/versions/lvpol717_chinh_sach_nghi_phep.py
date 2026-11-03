"""chinh sach nghi phep + phan bo chinh sach: 3 bang (duoc-CR-717)

Revision ID: lvpol717
Revises: lvcmp716

Tao tab_leave_policy, tab_leave_policy_line, tab_leave_policy_assignment. Chi tao bang con thieu (chay lai duoc).
Khong doi tab_leave_balance.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "lvpol717"
down_revision: Union[str, None] = "lvcmp716"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "tab_leave_policy" not in tables:
        op.create_table(
            "tab_leave_policy", *_audit_columns(),
            sa.Column("code", sa.String(30), nullable=False),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("note", sa.String(500), nullable=False, server_default=""),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.UniqueConstraint("code", name="uq_tab_leave_policy_code"),
        )
    if "tab_leave_policy_line" not in tables:
        op.create_table(
            "tab_leave_policy_line", *_audit_columns(),
            sa.Column("policy_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("leave_type_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("annual_days", sa.Float(), nullable=False, server_default="0"),
            sa.UniqueConstraint("policy_id", "leave_type_id", name="uq_leave_policy_line_type"),
        )
        op.create_index("ix_tab_leave_policy_line_policy_id", "tab_leave_policy_line", ["policy_id"])
    if "tab_leave_policy_assignment" not in tables:
        op.create_table(
            "tab_leave_policy_assignment", *_audit_columns(),
            sa.Column("employee_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("policy_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("effective_from", sa.Date(), nullable=False),
            sa.Column("effective_to", sa.Date(), nullable=True),
            sa.Column("note", sa.String(500), nullable=False, server_default=""),
            sa.UniqueConstraint("employee_id", "effective_from", name="uq_leave_policy_assign_emp_from"),
        )
        op.create_index("ix_tab_leave_policy_assignment_policy_id", "tab_leave_policy_assignment", ["policy_id"])
        op.create_index("ix_leave_policy_assign_emp_dates", "tab_leave_policy_assignment",
                        ["employee_id", "effective_from", "effective_to"])


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    for name in ("tab_leave_policy_assignment", "tab_leave_policy_line", "tab_leave_policy"):
        if name in tables:
            op.drop_table(name)
