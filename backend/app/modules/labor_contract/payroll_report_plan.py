"""Cột KẾ HOẠCH của báo cáo A5 (duoc-CR-690, phase 24): chi phí nhân sự kế hoạch, phần so được với thực tế, còn dư, % dùng.

Kế hoạch lấy từ `headcount_plan.effective` THEO THÁNG của kỳ báo cáo (kỳ hẹp thay kỳ rộng; «Toàn pháp nhân» thay các phòng),
chỉ cộng pháp nhân người xem `can_see_payroll`. Năm chỉ số (xem `PLAN_METRICS`):
- Chi phí nhân sự kế hoạch = Σ MỌI khoản của MỌI tháng trong kỳ;
- Kế hoạch phần so được = Σ khoản có nguồn thực tế (`actual_source ≠ NONE`), chỉ các tháng ĐÃ BẮT ĐẦU (tháng tương lai chưa có thực tế);
- Thực tế phần so được = HĐLĐ cộng ĐÚNG nguồn của các khoản đó (`headcount_plan.actual_cost`), cùng các tháng, cùng pháp nhân / phòng
  với kế hoạch;
- Còn dư = so được kế hoạch − thực tế; % dùng = thực tế ÷ kế hoạch so được. Không có gì so được (không khoản nào có nguồn, hoặc kỳ
  toàn tương lai) → ba chỉ số sau là `None` («—»), không phải 0.
Ghi vào `data` TRƯỚC `suppress_small_groups`: nhóm dưới 3 người bị che luôn cả năm cột (thực tế phần so được và còn dư suy ngược
được lương). Chỉ gắn theo nhóm khi «Xem theo» là Pháp nhân hoặc Phòng ban; nhóm Pháp nhân chỉ cộng mục `top` (chống cộng đôi),
nhóm Phòng ban cộng mọi kế hoạch phòng.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.core.report_period import Period
from app.modules.headcount_plan.constants import ActualSource
from app.modules.headcount_plan.actual_cost import ActualIndex, actual_by_item, covered_codes, months_between
from app.modules.headcount_plan.effective import EffectiveEntry, load_effective_monthly
from app.modules.headcount_plan.serializer import can_see_payroll
from app.modules.labor_contract.access import has_perm

from .payroll_report_data import PayRecord, rows_at

PLAN_METRICS = (("planned_cost", "Chi phí nhân sự kế hoạch", "money", None),
                ("planned_comparable", "Kế hoạch phần so được", "money", None),
                ("actual_comparable", "Thực tế phần so được", "money", None),
                ("payroll_remaining", "Còn dư so với kế hoạch", "money", "up"),
                ("payroll_use_rate", "% dùng", "percent", None))


@dataclass
class PlanSide:
    """Kế hoạch có hiệu lực của MỘT bên kỳ (kỳ này / kỳ so sánh) và ngày cuối kỳ đó."""
    entries: list[EffectiveEntry]
    hi: date


def load_plan_sets(db, user, prof: dict, period: Period, company_id: int | None, department_id: int | None,
                   action: str = "read") -> dict[str, PlanSide] | None:
    """Kế hoạch theo từng bên kỳ; `None` khi người xem không có quyền xem / xuất kế hoạch (cột không hiện).
    Chỉ giữ mục của pháp nhân người xem đọc được HĐLĐ ở phạm vi Tất cả / Công ty (cùng luật màn Kế hoạch nhân sự)."""
    if not has_perm(prof, "headcount_plan", "export" if action == "export" else "read"):
        return None

    def side(d_from: date, d_to: date) -> PlanSide:
        eff = load_effective_monthly(db, user, prof, months_between(d_from, d_to), company_id, department_id, action,
                                     with_costs=True)
        return PlanSide([e for e in eff.values() if can_see_payroll(prof, e.company_id, e.department_id)], d_to)

    sets = {"current": side(period.date_from, period.date_to)}
    if period.compare != "none" and period.compare_from and period.compare_to:
        sets["compare"] = side(period.compare_from, period.compare_to)
    return sets


@dataclass
class _Acc:
    cost: int = 0
    comp_plan: int = 0
    comp_actual: int = 0
    has_comp: bool = False


def _accumulate(side: PlanSide, records: list[PayRecord], today: date,
                group_by: str | None) -> tuple[_Acc | None, dict[str, _Acc]]:
    """(Tổng, {khóa nhóm: cộng dồn}); Tổng `None` khi không có kế hoạch nào."""
    index = ActualIndex(records, today, side.hi)
    total, groups = _Acc(), {}
    for e in side.entries:
        acc = _Acc(cost=sum(e.items.values()))
        covered = covered_codes(e.metas)
        if covered and index.is_elapsed(e.year, e.month):
            acc.has_comp = True
            acc.comp_plan = sum(e.items.get(c, 0) for c in covered)
            acc.comp_actual = sum(actual_by_item(index.rows(e.year, e.month, e.company_id, e.department_id),
                                                 e.metas).values())
        keys = []
        if e.top:
            keys.append(("total", None))
            if group_by == "company":
                keys.append(("group", str(e.company_id)))
        if group_by == "department" and e.department_id:
            keys.append(("group", str(e.department_id)))
        for kind, key in keys:
            target = total if kind == "total" else groups.setdefault(key, _Acc())
            target.cost += acc.cost
            target.comp_plan += acc.comp_plan
            target.comp_actual += acc.comp_actual
            target.has_comp = target.has_comp or acc.has_comp
    return (total if any(e.top for e in side.entries) else None), groups


def _put(values: dict | None, acc: _Acc | None) -> None:
    if values is None:
        return
    if acc is None:
        values.update({k: None for k, *_ in PLAN_METRICS})
        return
    values["planned_cost"] = acc.cost
    comparable = acc.has_comp
    values["planned_comparable"] = acc.comp_plan if comparable else None
    values["actual_comparable"] = acc.comp_actual if comparable else None
    values["payroll_remaining"] = acc.comp_plan - acc.comp_actual if comparable else None
    values["payroll_use_rate"] = round(acc.comp_actual * 100 / acc.comp_plan, 1) if comparable and acc.comp_plan else None


#  Ba chỉ số của dòng TỔNG suy ngược được lương (Tổng lương cơ bản − thực tế phần so được = lương nơi chưa có kế hoạch)
HIDEABLE_TOTAL_KEYS = ("actual_comparable", "payroll_remaining", "payroll_use_rate")
NOTE_TOTAL_HIDDEN = "Tổng phần so được không hiện vì có nơi chưa có kế hoạch hoặc nhóm nhỏ bị che"


def _has_unplanned_place(side: PlanSide | None, records: list[PayRecord], today: date) -> bool:
    """Có nơi (pháp nhân × phòng) CÓ NGƯỜI hưởng lương ở cuối kỳ mà không kế hoạch nào phủ (kế hoạch phòng đó hoặc «Toàn
    pháp nhân» của pháp nhân đó)? Khi có, «Tổng lương − thực tế phần so được» chính là lương của nơi đó."""
    if side is None:
        return False
    planned = {(e.company_id, e.department_id) for e in side.entries}
    return any((r.company_id, r.department_id) not in planned and (r.company_id, 0) not in planned
               for r in rows_at(records, min(side.hi, today)))


def hide_total_comparable(values: dict | None) -> None:
    if values is not None:
        for k in HIDEABLE_TOTAL_KEYS:
            values[k] = None


def hide_total_after_suppression(data: dict) -> None:
    """GỌI SAU `suppress_small_groups`: có nhóm nào bị che thì dòng Tổng không được hiện phần so được (nhóm bị che mà Tổng
    còn thực tế so được thì suy ngược được lương nhóm < 3 người). Chỉ khi báo cáo có cột kế hoạch."""
    if not any(m["key"] == "payroll_use_rate" for m in data["meta"]["metrics"]):
        return
    if any(g.get("suppressed") for g in data.get("groups") or []):
        for side in ("current", "compare"):
            hide_total_comparable(data["totals"].get(side))
        if NOTE_TOTAL_HIDDEN not in data["notes"]:
            data["notes"].append(NOTE_TOTAL_HIDDEN)


#  Chỉ số «tiền / số người» của nhóm không có HĐ: 0. Các chỉ số còn lại (bình quân, min, max) không có người để tính → None.
_ZERO_KEYS = ("people_paid", "base_total", "allowance_total", "payroll_total", "insurance_total")


def _empty_values(template: dict | None) -> dict | None:
    """Giá trị của một nhóm không có HĐ nào, cùng bộ khóa với dòng Tổng; `None` nếu kỳ đó không có cột."""
    if template is None:
        return None
    return {k: (0 if k in _ZERO_KEYS else None) for k in template}


def _add_planned_only_groups(data: dict, planned: dict[str, dict[str, _Acc]], names: dict) -> None:
    """Pháp nhân / phòng có kế hoạch nhưng KHÔNG có HĐ nào trong kỳ → thêm dòng riêng (lương thực tế 0), để cộng kế hoạch
    các dòng nhóm khớp dòng Tổng. Không làm lộ lương: dòng này không có người nên không có lương thật; số đếm người = 0
    nên luật che nhóm nhỏ (chỉ che nhóm 1–2 người) không đụng tới nó."""
    groups = data.get("groups")
    if groups is None:
        return
    existing = {str(g["key"]) for g in groups}
    missing = sorted({k for by_group in planned.values() for k in by_group} - existing)
    for key in missing:
        groups.append({"key": key, "label": names.get(int(key), "") if key.isdigit() else "",
                       "current": _empty_values(data["totals"].get("current")),
                       "compare": _empty_values(data["totals"].get("compare"))})


def add_plan_columns(data: dict, plan_sets: dict[str, PlanSide] | None, group_by: str | None,
                     group_names: dict | None, records: list[PayRecord], today: date) -> list[str]:
    """Khai năm chỉ số vào `meta`, ghi giá trị vào Tổng + từng nhóm, trả các ghi chú cần thêm.
    `plan_sets=None` → không thêm gì. `records` = HĐ đã nạp (cùng lần nạp với bảng chính)."""
    if plan_sets is None:
        return []
    for key, label, kind, good in PLAN_METRICS:
        data["meta"]["metrics"].append({"key": key, "label": label, "kind": kind, "good": good, "helper": False,
                                        "snapshot": False, "additive": False})
    totals, by_side = {}, {}
    for side_name in ("current", "compare"):
        side = plan_sets.get(side_name)
        totals[side_name], by_side[side_name] = _accumulate(side, records, today, group_by) if side else (None, {})
    _add_planned_only_groups(data, by_side, group_names or {})
    notes = _notes(plan_sets.get("current"))
    for side_name in ("current", "compare"):
        _put(data["totals"].get(side_name), totals[side_name])
        if _has_unplanned_place(plan_sets.get(side_name), records, today):
            hide_total_comparable(data["totals"].get(side_name))
            if NOTE_TOTAL_HIDDEN not in notes:
                notes.append(NOTE_TOTAL_HIDDEN)
        for g in data.get("groups") or []:
            if g.get(side_name) is not None:
                _put(g[side_name], by_side[side_name].get(str(g["key"])))
    return notes


def _notes(side: PlanSide | None) -> list[str]:
    notes = ["Chi phí nhân sự kế hoạch lấy từ «Kế hoạch nhân sự» theo từng tháng trong kỳ (kỳ hẹp thay kỳ rộng; pháp nhân có "
             "kế hoạch «Toàn pháp nhân» thì không cộng thêm các phòng) và chỉ gồm pháp nhân bạn được xem hợp đồng lao động. "
             "«Kế hoạch / thực tế phần so được» chỉ tính các khoản có nguồn thực tế trên hợp đồng và các tháng đã bắt đầu; "
             "«Còn dư» và «% dùng» so đúng phần đó. «—» = chưa có kế hoạch hoặc chưa có gì để so."]
    if side is None:
        return notes
    missing = sorted({m.name or m.code for e in side.entries for m in e.metas.values() if m.source == ActualSource.NONE})
    if missing:
        notes.append("Thực tế chưa gồm các khoản không có nguồn trên hợp đồng: " + ", ".join(missing[:15])
                     + (f" và {len(missing) - 15} khoản khác" if len(missing) > 15 else "") + ".")
    return notes
