"""bo_ke_hoach_nhan_su: bo han «Ke hoach nhan su» (duoc-CR-689/690)

Revision ID: hcplan05
Revises: hcplan04
Create Date: 2026-10-29

duoc-CR-692: dai ca chot BO «Ke hoach nhan su». Quy luong chi tinh tu luong tren HDLD.
Upgrade:
- DROP 7 bang (kiem ton tai): tab_headcount_plan_document, _line, _cost_item, tab_headcount_plan, tab_hr_cost_template_item,
  tab_hr_cost_template, tab_hr_cost_group;
- xoa tab_permission entity = 'headcount_plan'; xoa tab_report_access report_key = 25 (bao cao A4 da bo; so 25 KHONG tai cap);
- xoa tab_file_link entity = 'headcount_plan' (tep dinh kem ke hoach; hang tab_file giu nguyen);
- loai van ban CCKHNS: chua co van ban nao thi XOA, da co thi `is_active = 0` (van ban da tao giu nguyen).
Downgrade: dung lai cac bang RONG (DDL chep tu hcplan01-03) va bat lai loai CCKHNS neu con; quyen / dong gan bao cao /
tep khong khoi phuc.

VIET TAY (khong autogenerate): repo nay autogenerate troi ~650 dong moi lan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "hcplan05"
down_revision: Union[str, None] = "hcplan04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DOC_TYPE_CODE = "CCKHNS"
REPORT_KEY_RETIRED = 25
ENTITY = "headcount_plan"
#  Thu tu DROP: bang con truoc, bang cha sau (khong co FK cung nhung giu cho dung nghia).
DROP_ORDER = ("tab_headcount_plan_document", "tab_headcount_plan_line", "tab_headcount_plan_cost_item",
              "tab_headcount_plan", "tab_hr_cost_template_item", "tab_hr_cost_template", "tab_hr_cost_group")


def doc_type_action(document_count: int) -> str:
    """Ham thuan: loai van ban CCKHNS chua co van ban nao -> «delete»; da co -> «deactivate» (giu van ban da tao)."""
    return "delete" if document_count <= 0 else "deactivate"


def _audit() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def _item_columns() -> list[sa.Column]:
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


def _doc_type_table() -> sa.Table:
    return sa.table("tab_doc_type", sa.column("id", sa.BigInteger), sa.column("code", sa.String),
                    sa.column("is_active", sa.Boolean))


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    for table in DROP_ORDER:
        if table in existing:
            op.drop_table(table)

    tables = set(sa.inspect(bind).get_table_names())
    if "tab_permission" in tables:
        bind.execute(sa.text("DELETE FROM tab_permission WHERE entity = :e"), {"e": ENTITY})
    if "tab_report_access" in tables:
        bind.execute(sa.text("DELETE FROM tab_report_access WHERE report_key = :k"), {"k": REPORT_KEY_RETIRED})
    if "tab_file_link" in tables:
        bind.execute(sa.text("DELETE FROM tab_file_link WHERE entity = :e"), {"e": ENTITY})

    if "tab_doc_type" in tables:
        t = _doc_type_table()
        type_id = bind.execute(sa.select(t.c.id).where(sa.func.upper(t.c.code) == DOC_TYPE_CODE)).scalar()
        if type_id is not None:
            n = 0
            if "tab_document" in tables:
                n = bind.execute(sa.text("SELECT COUNT(*) FROM tab_document WHERE doc_type_id = :t"),
                                 {"t": type_id}).scalar() or 0
            if doc_type_action(int(n)) == "delete":
                bind.execute(sa.delete(t).where(t.c.id == type_id))
            else:
                bind.execute(sa.update(t).where(t.c.id == type_id).values(is_active=False))


def downgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if "tab_hr_cost_group" not in existing:
        op.create_table("tab_hr_cost_group",
                        sa.Column("name", sa.String(100), nullable=False),
                        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
                        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
                        *_audit(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"))
    if "tab_hr_cost_template" not in existing:
        op.create_table("tab_hr_cost_template",
                        sa.Column("name", sa.String(150), nullable=False),
                        sa.Column("note", sa.String(500), nullable=False, server_default=""),
                        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
                        *_audit(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"))
    if "tab_hr_cost_template_item" not in existing:
        op.create_table("tab_hr_cost_template_item",
                        sa.Column("template_id", sa.BigInteger(), nullable=False), *_item_columns(), *_audit(),
                        sa.PrimaryKeyConstraint("id"),
                        sa.UniqueConstraint("template_id", "code", name="uq_hr_cost_template_item"))
        op.create_index("ix_tab_hr_cost_template_item_template_id", "tab_hr_cost_template_item", ["template_id"])
    if "tab_headcount_plan" not in existing:
        op.create_table("tab_headcount_plan",
                        sa.Column("year", sa.SmallInteger(), nullable=False),
                        sa.Column("period_type", sa.SmallInteger(), nullable=False, server_default="1"),
                        sa.Column("period_no", sa.SmallInteger(), nullable=False, server_default="1"),
                        sa.Column("company_id", sa.BigInteger(), nullable=False),
                        sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
                        sa.Column("basis_no", sa.String(100), nullable=False, server_default=""),
                        sa.Column("basis_date", sa.Date(), nullable=True),
                        sa.Column("approver_employee_id", sa.BigInteger(), nullable=False, server_default="0"),
                        sa.Column("template_id", sa.BigInteger(), nullable=False, server_default="0"),
                        sa.Column("note", sa.String(500), nullable=False, server_default=""),
                        *_audit(), sa.PrimaryKeyConstraint("id"),
                        sa.UniqueConstraint("year", "period_type", "period_no", "company_id", "department_id",
                                            name="uq_headcount_plan_period"))
        op.create_index("ix_headcount_plan_company_year", "tab_headcount_plan", ["company_id", "year"])
    if "tab_headcount_plan_cost_item" not in existing:
        op.create_table("tab_headcount_plan_cost_item",
                        sa.Column("plan_id", sa.BigInteger(), nullable=False), *_item_columns(), *_audit(),
                        sa.PrimaryKeyConstraint("id"),
                        sa.UniqueConstraint("plan_id", "code", name="uq_headcount_plan_cost_item"))
        op.create_index("ix_tab_headcount_plan_cost_item_plan_id", "tab_headcount_plan_cost_item", ["plan_id"])
    if "tab_headcount_plan_line" not in existing:
        op.create_table("tab_headcount_plan_line",
                        sa.Column("plan_id", sa.BigInteger(), nullable=False),
                        sa.Column("position_id", sa.BigInteger(), nullable=False, server_default="0"),
                        sa.Column("headcounts", sa.JSON(), nullable=False),
                        sa.Column("amounts", sa.JSON(), nullable=False),
                        sa.Column("note", sa.String(500), nullable=False, server_default=""),
                        *_audit(), sa.PrimaryKeyConstraint("id"),
                        sa.UniqueConstraint("plan_id", "position_id", name="uq_headcount_plan_line"))
        op.create_index("ix_tab_headcount_plan_line_plan_id", "tab_headcount_plan_line", ["plan_id"])
    if "tab_headcount_plan_document" not in existing:
        op.create_table("tab_headcount_plan_document",
                        sa.Column("plan_id", sa.BigInteger(), nullable=False),
                        sa.Column("document_id", sa.BigInteger(), nullable=False),
                        *_audit(), sa.PrimaryKeyConstraint("id"),
                        sa.UniqueConstraint("plan_id", "document_id", name="uq_headcount_plan_document"))
        op.create_index("ix_tab_headcount_plan_document_plan_id", "tab_headcount_plan_document", ["plan_id"])

    if "tab_doc_type" in set(sa.inspect(bind).get_table_names()):
        t = _doc_type_table()
        bind.execute(sa.update(t).where(sa.func.upper(t.c.code) == DOC_TYPE_CODE).values(is_active=True))
