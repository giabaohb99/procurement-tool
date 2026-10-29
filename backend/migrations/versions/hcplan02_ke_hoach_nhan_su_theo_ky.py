"""ke_hoach_nhan_su_theo_ky: ke hoach theo ky (nam/ban nien/quy/thang) + khoan chi phi tu dinh nghia + van ban lien ket

Revision ID: hcplan02
Revises: hcplan01
Create Date: 2026-10-28

duoc-CR-690 (phase 22). Thay bang mot-dong cua dot 4 bang: tab_hr_cost_group, tab_hr_cost_template(+_item),
tab_headcount_plan (mo rong: loai ky, ky, can cu), tab_headcount_plan_cost_item, tab_headcount_plan_line,
tab_headcount_plan_document. Doi khoa duy nhat sang (year, period_type, period_no, company_id, department_id).
GIU cot planned_headcount / planned_payroll_monthly (bao cao A4/A5 con doc; DROP o migration cua phase 24).
Doi du lieu cu + gieo nhom / mau goi y: DA BO khoi migration nay (duoc-CR-692 xoa module `headcount_plan`; `hcplan05` DROP het cac bang nay
nen khong con y nghia). Chuoi migration van chay duoc tu DB trong.

VIET TAY (tuong duong autogenerate da got): repo nay autogenerate troi ~650 dong moi lan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "hcplan02"
down_revision: Union[str, None] = "hcplan01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def _item_columns() -> list[sa.Column]:
    """Cot chung cua khoan chi phi (mau / ke hoach) — khop `cost_model.CostItemColumns`."""
    return [
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("calc_method", sa.SmallInteger(), nullable=False),
        sa.Column("rate", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.Column("factor", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("cap_amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("base_codes", sa.JSON(), nullable=False),
        sa.Column("applies_to", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("position_ids", sa.JSON(), nullable=False),
        sa.Column("months", sa.JSON(), nullable=False),
        sa.Column("actual_source", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    op.create_table("tab_hr_cost_group",
                    sa.Column("name", sa.String(100), nullable=False),
                    sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
                    sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
                    *_audit(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"))
    op.create_table("tab_hr_cost_template",
                    sa.Column("name", sa.String(150), nullable=False),
                    sa.Column("note", sa.String(500), nullable=False, server_default=""),
                    sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
                    *_audit(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"))
    op.create_table("tab_hr_cost_template_item",
                    sa.Column("template_id", sa.BigInteger(), nullable=False), *_item_columns(), *_audit(),
                    sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("template_id", "code", name="uq_hr_cost_template_item"))
    op.create_index("ix_tab_hr_cost_template_item_template_id", "tab_hr_cost_template_item", ["template_id"])

    #  tab_headcount_plan: cot moi + khoa duy nhat moi (hang cu mac dinh loai Nam, ky 1)
    op.add_column("tab_headcount_plan", sa.Column("period_type", sa.SmallInteger(), nullable=False, server_default="1"))
    op.add_column("tab_headcount_plan", sa.Column("period_no", sa.SmallInteger(), nullable=False, server_default="1"))
    op.add_column("tab_headcount_plan", sa.Column("basis_no", sa.String(100), nullable=False, server_default=""))
    op.add_column("tab_headcount_plan", sa.Column("basis_date", sa.Date(), nullable=True))
    op.add_column("tab_headcount_plan", sa.Column("approver_employee_id", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("tab_headcount_plan", sa.Column("template_id", sa.BigInteger(), nullable=False, server_default="0"))
    op.drop_constraint("uq_headcount_plan_scope", "tab_headcount_plan", type_="unique")
    op.create_unique_constraint("uq_headcount_plan_period", "tab_headcount_plan",
                                ["year", "period_type", "period_no", "company_id", "department_id"])

    op.create_table("tab_headcount_plan_cost_item",
                    sa.Column("plan_id", sa.BigInteger(), nullable=False), *_item_columns(), *_audit(),
                    sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("plan_id", "code", name="uq_headcount_plan_cost_item"))
    op.create_index("ix_tab_headcount_plan_cost_item_plan_id", "tab_headcount_plan_cost_item", ["plan_id"])
    op.create_table("tab_headcount_plan_line",
                    sa.Column("plan_id", sa.BigInteger(), nullable=False),
                    sa.Column("position_id", sa.BigInteger(), nullable=False, server_default="0"),
                    sa.Column("headcounts", sa.JSON(), nullable=False),
                    sa.Column("amounts", sa.JSON(), nullable=False),
                    sa.Column("note", sa.String(500), nullable=False, server_default=""),
                    *_audit(), sa.PrimaryKeyConstraint("id"),
                    sa.UniqueConstraint("plan_id", "position_id", name="uq_headcount_plan_line"))
    op.create_index("ix_tab_headcount_plan_line_plan_id", "tab_headcount_plan_line", ["plan_id"])
    op.create_table("tab_headcount_plan_document",
                    sa.Column("plan_id", sa.BigInteger(), nullable=False),
                    sa.Column("document_id", sa.BigInteger(), nullable=False),
                    *_audit(), sa.PrimaryKeyConstraint("id"),
                    sa.UniqueConstraint("plan_id", "document_id", name="uq_headcount_plan_document"))
    op.create_index("ix_tab_headcount_plan_document_plan_id", "tab_headcount_plan_document", ["plan_id"])


def downgrade() -> None:
    #  Bang cu chi con (nam, phap nhan, phong) duy nhat: ke hoach nhieu ky cung phap nhan x phong khong the dung lai —
    #  giu ke hoach loai Nam, ky 1 (hang khac bi bo). Cot planned_* da duoc dong bo moi lan luu nen khong mat so.
    op.execute("DELETE FROM tab_headcount_plan WHERE NOT (period_type = 1 AND period_no = 1)")
    for table in ("tab_headcount_plan_document", "tab_headcount_plan_line", "tab_headcount_plan_cost_item",
                  "tab_hr_cost_template_item", "tab_hr_cost_template", "tab_hr_cost_group"):
        op.drop_table(table)
    op.drop_constraint("uq_headcount_plan_period", "tab_headcount_plan", type_="unique")
    op.create_unique_constraint("uq_headcount_plan_scope", "tab_headcount_plan", ["year", "company_id", "department_id"])
    for col in ("template_id", "approver_employee_id", "basis_date", "basis_no", "period_no", "period_type"):
        op.drop_column("tab_headcount_plan", col)
