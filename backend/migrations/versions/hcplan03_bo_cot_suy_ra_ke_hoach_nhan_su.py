"""bo_cot_suy_ra_ke_hoach_nhan_su: DROP planned_headcount / planned_payroll_monthly

Revision ID: hcplan03
Revises: hcplan02
Create Date: 2026-10-28

duoc-CR-690 (phase 24). Bao cao A4 / A5 doc ke hoach co hieu luc theo thang (`headcount_plan.effective`) nen hai cot suy ra
cua dot 4 khong con ai doc / ghi. Downgrade dung lai hai cot va SUY lai gia tri tu dong ke hoach: dinh bien = tong dinh bien
ky con cuoi; quy luong / thang = tong chi phi (bo tinh `costing`) / so thang cua ky. Ke hoach sai luat tinh -> 0.

VIET TAY (tuong duong autogenerate da got): repo nay autogenerate troi ~650 dong moi lan.
"""
import logging
from decimal import Decimal
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "hcplan03"
down_revision: Union[str, None] = "hcplan02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

log = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    op.drop_column("tab_headcount_plan", "planned_payroll_monthly")
    op.drop_column("tab_headcount_plan", "planned_headcount")


def _derive(conn, plan) -> tuple[int, int]:
    """(định biên cuối kỳ, quỹ lương / tháng) của một kế hoạch từ dòng + khoản đang lưu."""
    from app.modules.headcount_plan.costing import CostItem, PlanLine, compute_plan, period_months

    lines = conn.execute(sa.text("SELECT position_id, headcounts, amounts FROM tab_headcount_plan_line "
                                 "WHERE plan_id = :p"), {"p": plan.id}).fetchall()
    items = conn.execute(sa.text(
        "SELECT code, name, group_id, calc_method, rate, factor, cap_amount, amount, base_codes, applies_to, "
        "position_ids, months, sort_order FROM tab_headcount_plan_cost_item WHERE plan_id = :p"), {"p": plan.id}).fetchall()
    import json

    def js(v):
        return json.loads(v) if isinstance(v, (str, bytes)) else (v or [])

    plan_lines = [PlanLine(int(r.position_id), tuple(int(h) for h in js(r.headcounts)),
                           {k: int(v) for k, v in (js(r.amounts) or {}).items()} if isinstance(js(r.amounts), dict) else {})
                  for r in lines]
    cost_items = [CostItem(r.code, r.name, int(r.group_id), int(r.calc_method), Decimal(str(r.rate or 0)),
                           Decimal(str(r.factor or 0)), int(r.cap_amount or 0), int(r.amount or 0),
                           tuple(js(r.base_codes)), int(r.applies_to), tuple(int(x) for x in js(r.position_ids)),
                           tuple(int(x) for x in js(r.months)), int(r.sort_order or 0)) for r in items]
    computed = compute_plan(plan.period_type, plan.period_no, plan.year, cost_items, plan_lines)
    months = max(1, len(period_months(plan.period_type, plan.period_no)))
    return int(computed["headcount"][-1]), int(round(computed["total"]["total"] / months))


def downgrade() -> None:
    op.add_column("tab_headcount_plan", sa.Column("planned_headcount", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tab_headcount_plan", sa.Column("planned_payroll_monthly", sa.BigInteger(), nullable=False,
                                                  server_default="0"))
    conn = op.get_bind()
    for plan in conn.execute(sa.text("SELECT id, year, period_type, period_no FROM tab_headcount_plan")).fetchall():
        try:
            heads, pay = _derive(conn, plan)
        except Exception as e:   # dữ liệu sai luật tính: để 0, không chặn hạ cấp
            log.warning("Khong suy lai duoc ke hoach id=%s: %s", plan.id, e)
            continue
        conn.execute(sa.text("UPDATE tab_headcount_plan SET planned_headcount = :h, planned_payroll_monthly = :m "
                             "WHERE id = :p"), {"h": heads, "m": pay, "p": plan.id})
