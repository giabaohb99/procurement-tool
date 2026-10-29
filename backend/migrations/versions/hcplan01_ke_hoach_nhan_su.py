"""ke_hoach_nhan_su: bang tab_headcount_plan (dinh bien + quy luong ke hoach theo nam x phap nhan x phong)

Revision ID: hcplan01
Revises: cr683nghiphep01
Create Date: 2026-10-28

duoc-CR-689 (phase 17). Nguon cua bao cao A4 «Dinh bien ke hoach so voi thuc te» va cac cot ke hoach cua A5.
`department_id = 0` = ca phap nhan. FK mem (khong ForeignKey thuc) theo quy uoc repo.

VIET TAY (tuong duong autogenerate da got): repo nay autogenerate troi ~650 dong moi lan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "hcplan01"
down_revision: Union[str, None] = "cr683nghiphep01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_headcount_plan",
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("planned_headcount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("planned_payroll_monthly", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "company_id", "department_id", name="uq_headcount_plan_scope"),
    )
    op.create_index("ix_headcount_plan_company_year", "tab_headcount_plan", ["company_id", "year"])


def downgrade() -> None:
    op.drop_index("ix_headcount_plan_company_year", table_name="tab_headcount_plan")
    op.drop_table("tab_headcount_plan")
