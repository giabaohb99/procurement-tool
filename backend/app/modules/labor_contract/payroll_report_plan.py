"""Cột KẾ HOẠCH của báo cáo A5 (duoc-CR-689, phase 17): quỹ lương kế hoạch / tháng, còn dư, % dùng.

Nguồn: `tab_headcount_plan.planned_payroll_monthly` của NĂM cuối kỳ (kỳ so sánh: năm cuối kỳ so sánh).
Chống cộng đôi cùng luật A4: pháp nhân có dòng «toàn pháp nhân» thì lấy dòng đó, không thì cộng các dòng phòng.
Dòng để 0 = chưa khai quỹ lương → bỏ qua; không dòng nào khai thì cả ba chỉ số là `None` («—»), không phải 0.
Ghi vào `data` TRƯỚC `suppress_small_groups` nên nhóm dưới 3 người bị che luôn cả ba cột (còn dư = kế hoạch − lương
thật, để lộ là suy ngược được lương). Chỉ gắn theo nhóm khi «Xem theo» là Pháp nhân hoặc Phòng ban.
"""
from __future__ import annotations

from app.core.report_period import Period
from app.modules.employee.headcount_plan_report_data import load_plans
from app.modules.headcount_plan.model import HeadcountPlan
from app.modules.headcount_plan.serializer import can_see_payroll
from app.modules.labor_contract.access import has_perm

PLAN_METRICS = (("planned_payroll", "Quỹ lương kế hoạch / tháng", "money", None),
                ("payroll_remaining", "Còn dư so với kế hoạch", "money", "up"),
                ("payroll_use_rate", "% dùng", "percent", None))


def load_plan_sets(db, user, prof: dict, period: Period, company_id: int | None, department_id: int | None,
                   action: str = "read") -> dict[str, list[HeadcountPlan]] | None:
    """Dòng kế hoạch theo từng bên kỳ; `None` khi người xem không có quyền xem / xuất kế hoạch (cột không hiện)."""
    if not has_perm(prof, "headcount_plan", "export" if action == "export" else "read"):
        return None
    def visible(year: int) -> list[HeadcountPlan]:
        #  Cùng luật màn Kế hoạch nhân sự: quỹ lương kế hoạch chỉ tính dòng của pháp nhân mà người xem đọc được
        #  HĐLĐ ở phạm vi Tất cả / Công ty — HĐLĐ phạm vi phòng / bản thân không được thấy quỹ cả pháp nhân.
        plans = load_plans(db, user, prof, year, company_id, department_id, action)
        return [p for p in plans if can_see_payroll(prof, p.company_id)]

    sets = {"current": visible(period.date_to.year)}
    if period.compare != "none" and period.compare_to:
        sets["compare"] = visible(period.compare_to.year)
    return sets


def _planned(plans: list[HeadcountPlan], group_by: str | None) -> tuple[int | None, dict[str, int]]:
    """(tổng quỹ lương kế hoạch, {khóa nhóm: quỹ lương kế hoạch}) — chỉ tính dòng đã khai quỹ lương."""
    company_level = {p.company_id: int(p.planned_payroll_monthly or 0) for p in plans if not p.department_id}
    dept_lines = [p for p in plans if p.department_id and p.planned_payroll_monthly]
    by_company: dict[int, int] = {c: v for c, v in company_level.items() if v}
    for p in dept_lines:
        if p.company_id not in company_level:        # pháp nhân có dòng «toàn pháp nhân» thì bỏ dòng phòng
            by_company[p.company_id] = by_company.get(p.company_id, 0) + int(p.planned_payroll_monthly)
    total = sum(by_company.values()) if by_company else None
    if group_by == "company":
        return total, {str(c): v for c, v in by_company.items()}
    if group_by == "department":
        #  Phòng dùng chung nhiều pháp nhân: nhóm Phòng ban gộp cùng phòng của mọi pháp nhân → CỘNG, không ghi đè.
        by_dept: dict[str, int] = {}
        for p in dept_lines:
            by_dept[str(p.department_id)] = by_dept.get(str(p.department_id), 0) + int(p.planned_payroll_monthly)
        return total, by_dept
    return total, {}


def _put(values: dict | None, planned: int | None) -> None:
    if values is None:
        return
    paid = values.get("payroll_total")
    values["planned_payroll"] = planned
    values["payroll_remaining"] = planned - paid if planned is not None and paid is not None else None
    values["payroll_use_rate"] = round(paid * 100 / planned, 1) if planned and paid is not None else None


#  Chỉ số «tiền / số người» của nhóm không có HĐ: 0. Các chỉ số còn lại (bình quân, min, max) không có người để tính → None.
_ZERO_KEYS = ("people_paid", "base_total", "allowance_total", "payroll_total", "insurance_total")


def _empty_values(template: dict | None) -> dict | None:
    """Giá trị của một nhóm không có HĐ nào, cùng bộ khóa với dòng Tổng; `None` nếu kỳ đó không có cột."""
    if template is None:
        return None
    return {k: (0 if k in _ZERO_KEYS else None) for k in template}


def _add_planned_only_groups(data: dict, planned: dict[str, dict[str, int]], names: dict) -> None:
    """Pháp nhân / phòng có quỹ lương kế hoạch nhưng KHÔNG có HĐ nào trong kỳ → thêm dòng riêng (lương thực tế 0),
    để cộng kế hoạch các dòng nhóm khớp dòng Tổng. Không làm lộ lương: dòng này không có người nên không có
    lương thật; số đếm người = 0 nên luật che nhóm nhỏ (chỉ che nhóm 1–2 người) không đụng tới nó."""
    groups = data.get("groups")
    if groups is None:
        return
    existing = {str(g["key"]) for g in groups}
    missing = sorted({k for by_group in planned.values() for k in by_group} - existing)
    for key in missing:
        groups.append({"key": key, "label": names.get(int(key), "") if key.isdigit() else "",
                       "current": _empty_values(data["totals"].get("current")),
                       "compare": _empty_values(data["totals"].get("compare"))})


def add_plan_columns(data: dict, plan_sets: dict[str, list[HeadcountPlan]] | None, group_by: str | None,
                     group_names: dict | None = None) -> None:
    """Khai ba chỉ số vào `meta` và ghi giá trị vào Tổng + từng nhóm. `plan_sets=None` → không thêm gì.
    `group_names` = {id: tên} của chiều «Xem theo» (cùng nguồn tên với các nhóm khác)."""
    if plan_sets is None:
        return
    for key, label, kind, good in PLAN_METRICS:
        data["meta"]["metrics"].append({"key": key, "label": label, "kind": kind, "good": good, "helper": False,
                                        "snapshot": False, "additive": False})
    totals_planned, by_side = {}, {}
    for side in ("current", "compare"):
        totals_planned[side], by_side[side] = _planned(plan_sets.get(side) or [], group_by)
    _add_planned_only_groups(data, by_side, group_names or {})
    for side in ("current", "compare"):
        _put(data["totals"].get(side), totals_planned[side])
        for g in data.get("groups") or []:
            if g.get(side) is not None:
                _put(g[side], by_side[side].get(str(g["key"])))
