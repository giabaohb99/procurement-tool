"""Kế hoạch nhân sự CÓ HIỆU LỰC theo từng THÁNG (duoc-CR-690, phase 24) — nguồn số kế hoạch của báo cáo A4 / A5.

Luật (`doc/erp/hrm/06-ke-hoach-nhan-su.md` §3):
- Với (pháp nhân, phòng, tháng): lấy kế hoạch phủ tháng đó có loại kỳ HẸP nhất (Tháng > Quý > Bán niên > Năm).
  Kế hoạch Q3 thay kế hoạch Năm cho tháng 7–9; các tháng còn lại vẫn theo kế hoạch Năm.
- Chống cộng đôi theo pháp nhân × tháng: có kế hoạch «Toàn pháp nhân» (phòng 0) hiệu lực thì CHỈ nó là `top`
  (tính vào Tổng / nhóm Pháp nhân); không thì các kế hoạch phòng là `top`.

Số truy vấn CỐ ĐỊNH, không theo số tháng hay số kế hoạch: kế hoạch (qua `apply_scope`) + dòng vị trí, thêm khoản chi phí
và tên nhóm khi `with_costs`. Phần tính chạy trong bộ nhớ bằng `costing`. Hàm KHÔNG che tiền: bên gọi tự lọc theo
`can_see_payroll(profile, company_id, department_id)`.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Sequence

from sqlalchemy.orm import Session

from app.core.scoping import apply_scope

from .cost_model import HeadcountPlanCostItem, HrCostGroup
from .constants import ActualSource
from .costing import PlanCalcError, compute_plan, period_layout, period_months
from .model import HeadcountPlan, HeadcountPlanLine
from .serializer import to_cost_item, to_plan_line

log = logging.getLogger("app.headcount_plan.effective")

Month = tuple[int, int]   # (năm, tháng 1–12)


@dataclass(frozen=True)
class ItemMeta:
    """Phần của khoản chi phí cần để tính SỐ THỰC TẾ cùng nguồn (`actual_cost`)."""
    code: str
    name: str
    source: int            # ActualSource
    rate: Decimal
    cap_amount: int


def meta_of(item) -> ItemMeta:
    """ORM khoản của kế hoạch → `ItemMeta`."""
    return ItemMeta(item.code, item.name or "", int(item.actual_source or ActualSource.NONE),
                    Decimal(str(item.rate or 0)), int(item.cap_amount or 0))


@dataclass
class EffectiveEntry:
    plan_id: int
    company_id: int
    department_id: int     # 0 = «Toàn pháp nhân»
    year: int
    month: int
    headcount: int
    by_position: dict[int, int]                              # {position_id (0 = không theo vị trí): định biên}
    top: bool = False
    items: dict[str, int] = field(default_factory=dict)      # {mã khoản: đồng} — chỉ khi `with_costs`
    metas: dict[str, ItemMeta] = field(default_factory=dict)


def _query_plans(db: Session, user, prof: dict, years: set[int], company_id, department_id, action: str):
    q = apply_scope(db.query(HeadcountPlan), HeadcountPlan, "headcount_plan", user, prof, action)
    q = q.filter(HeadcountPlan.year.in_(years))
    if company_id is not None:
        q = q.filter(HeadcountPlan.company_id == company_id)
    if department_id is not None:
        q = q.filter(HeadcountPlan.department_id == department_id)
    return q.order_by(HeadcountPlan.company_id, HeadcountPlan.department_id, HeadcountPlan.id).all()


def _candidates(plans: list[HeadcountPlan], wanted: set[Month]) -> dict[tuple, list[HeadcountPlan]]:
    """{(pháp nhân, phòng, năm, tháng): các kế hoạch phủ tháng đó, HẸP nhất trước}. Kế hoạch kỳ sai bị bỏ qua.
    Giữ cả kế hoạch rộng hơn để lùi về khi kế hoạch hẹp sai luật tính (xem `load_effective_monthly`)."""
    found: dict[tuple, list[HeadcountPlan]] = {}
    for p in plans:
        try:
            covered = period_months(p.period_type, p.period_no)
        except PlanCalcError:
            log.warning("Bo qua ke hoach id=%s: loai ky/so ky khong hop le", p.id)
            continue
        for m in covered:
            if (p.year, m) in wanted:
                found.setdefault((p.company_id, p.department_id or 0, p.year, m), []).append(p)
    for lst in found.values():
        lst.sort(key=lambda p: (-int(p.period_type), p.id))   # loại kỳ càng lớn số càng hẹp
    return found


def _plan_months(plan: HeadcountPlan, lines: list, items: list | None, groups: dict) -> dict[int, dict] | None:
    """{tháng: {"headcount", "by_position", "items"}} của MỘT kế hoạch; `None` nếu dữ liệu sai luật (bỏ qua kế hoạch)."""
    try:
        layout = period_layout(plan.period_type, plan.period_no)
        plan_lines = [to_plan_line(ln) for ln in lines]
        if any(len(ln.headcounts) != len(layout) for ln in plan_lines):
            raise PlanCalcError("Số cột định biên không khớp số kỳ con")
        monthly = (compute_plan(plan.period_type, plan.period_no, plan.year, [to_cost_item(i) for i in items],
                                plan_lines, groups)["monthly"] if items is not None else None)
    except PlanCalcError as e:
        log.warning("Bo qua ke hoach id=%s: %s", plan.id, e)
        return None
    out: dict[int, dict] = {}
    for i, sub in enumerate(layout):
        by_pos: dict[int, int] = {}
        for ln in plan_lines:
            by_pos[ln.position_id] = by_pos.get(ln.position_id, 0) + ln.headcounts[i]
        for m in sub["months"]:
            out[m] = {"headcount": sum(by_pos.values()), "by_position": by_pos,
                      "items": monthly[m]["items"] if monthly is not None else {}}
    return out


def load_effective_monthly(db: Session, user, prof: dict, months: Sequence[Month], company_id: int | None = None,
                           department_id: int | None = None, action: str = "read",
                           with_costs: bool = False) -> dict[tuple, EffectiveEntry]:
    """{(pháp nhân, phòng, năm, tháng): EffectiveEntry} của các tháng yêu cầu.

    `with_costs=False` (A4) bỏ qua khoản chi phí và bộ tính — chỉ định biên. Định biên theo vị trí nằm trong
    `by_position` (key cuối của đặc tả «(pháp nhân, phòng, vị trí, tháng)» được gộp vào giá trị để khỏi nhân số khóa)."""
    wanted = set(months)
    if not wanted:
        return {}
    candidates = _candidates(_query_plans(db, user, prof, {y for y, _ in wanted}, company_id, department_id, action),
                             wanted)
    plan_by_id = {p.id: p for lst in candidates.values() for p in lst}
    if not plan_by_id:
        return {}
    ids = list(plan_by_id)
    lines_by: dict[int, list] = {}
    for ln in db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id.in_(ids)).all():
        lines_by.setdefault(ln.plan_id, []).append(ln)
    items_by: dict[int, list] = {}
    groups: dict = {}
    if with_costs:
        groups = dict(db.query(HrCostGroup.id, HrCostGroup.name).all())
        for it in (db.query(HeadcountPlanCostItem).filter(HeadcountPlanCostItem.plan_id.in_(ids))
                   .order_by(HeadcountPlanCostItem.sort_order, HeadcountPlanCostItem.id).all()):
            items_by.setdefault(it.plan_id, []).append(it)
    computed: dict[int, dict | None] = {}

    def months_of(p: HeadcountPlan) -> dict | None:   # tính LƯỜI từng kế hoạch, mỗi kế hoạch một lần (không thêm truy vấn)
        if p.id not in computed:
            computed[p.id] = _plan_months(p, lines_by.get(p.id, []), items_by.get(p.id, []) if with_costs else None,
                                          groups)
        return computed[p.id]

    metas = {pid: {i.code: meta_of(i) for i in its} for pid, its in items_by.items()}
    out: dict[tuple, EffectiveEntry] = {}
    for (co, dept, year, month), lst in candidates.items():
        #  Kế hoạch hẹp nhất sai luật tính thì lùi về kế hoạch rộng hơn kế tiếp (đã log cảnh báo ở `_plan_months`)
        p = per_month = None
        for cand in lst:
            per_month = months_of(cand)
            if per_month is not None:
                p = cand
                break
        if p is None:
            continue
        d = per_month[month]
        out[(co, dept, year, month)] = EffectiveEntry(
            plan_id=p.id, company_id=co, department_id=dept, year=year, month=month, headcount=d["headcount"],
            by_position=dict(d["by_position"]), items=dict(d["items"]), metas=metas.get(p.id, {}))
    company_level = {(co, y, m) for (co, dept, y, m) in out if dept == 0}
    for (co, dept, y, m), e in out.items():
        e.top = dept == 0 or (co, y, m) not in company_level
    return out
