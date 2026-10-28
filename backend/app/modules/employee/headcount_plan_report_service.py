"""Báo cáo A4 «Định biên kế hoạch so với thực tế» (khóa 25, duoc-CR-689) — `GET /api/headcount-plan-report/summary`.

Định biên kế hoạch = định biên của kế hoạch CÓ HIỆU LỰC ở THÁNG CUỐI KỲ báo cáo (kỳ hẹp thay kỳ rộng, `headcount_plan/effective`);
thực tế = người đang làm tại `as_of = min(cuối kỳ, hôm nay)` (luật A1). Ảnh chụp một mốc: không xu hướng, không kỳ so sánh
(như A3). Dòng dữ liệu + luật chống cộng đôi ở `headcount_plan_report_data.py`; chiều Vị trí ở `headcount_plan_report_positions.py`;
`/summary/rows` dùng đúng `key_of` của chiều gom nên danh sách khớp bảng.
"""
from __future__ import annotations

from dataclasses import replace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.vn_time import vn_today
from app.modules.employee.headcount_plan_report_data import (
    PlanRow, build_plan_rows, counts_of, dept_counts, load_counts, load_people, load_plan_entries)
from app.modules.employee.headcount_plan_report_positions import (
    PositionUnits, load_position_names)
from app.modules.employee.profile_gaps_report_data import load_group_names

METRICS = {"actual": "Đang có", "unplanned": "Đang làm ở phòng chưa có kế hoạch"}   # chỉ số có danh sách /rows
COLUMNS = [Col("code", "Mã NV"), Col("name", "Họ tên"), Col("department", "Phòng ban"),
           Col("position", "Chức vụ"), Col("hire_date", "Ngày vào làm", "date")]
NO_PLAN = " (chưa có kế hoạch)"


def _spec(company_name: dict, department_name: dict, position_name: dict | None = None,
          units: PositionUnits | None = None) -> tuple[ReportSpec, dict[str, DimensionSpec]]:
    metrics = [
        MetricSpec("planned", "Định biên kế hoạch", value_of=lambda r: r.planned),
        MetricSpec("actual", METRICS["actual"], value_of=lambda r: r.actual),
        MetricSpec("gap", "Chênh (thực tế − kế hoạch)", value_of=lambda r: r.actual - r.planned),
        MetricSpec("vacancies", "Còn thiếu", good="down", value_of=lambda r: r.vacancies),
        MetricSpec("over", "Vượt", good="down", value_of=lambda r: r.over),
        MetricSpec("unplanned", METRICS["unplanned"], good="down", value_of=lambda r: r.unplanned),
        MetricSpec("filled", "Vị trí kế hoạch đã có người", value_of=lambda r: r.filled, helper=True),
    ]
    derived = [DerivedSpec("fill_rate", "Tỷ lệ lấp đầy", num="filled", den="planned")]

    def company_key(r):
        return [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else []

    def department_key(r):
        co = company_name.get(r.company_id, "")
        if r.level == "company":      # dòng «toàn pháp nhân»: nhóm riêng theo pháp nhân, khóa `c<id>`
            return [(f"c{r.company_id}", f"{co} — Toàn pháp nhân")]
        keys = [(r.department_id, department_name.get(r.department_id, "")
                 + (NO_PLAN if getattr(r, "has_plan", True) is False else ""))] if r.department_id else []
        if r.level == "person":       # người thuộc cả nhóm phòng LẪN nhóm «toàn pháp nhân» của pháp nhân mình
            keys = keys or [("", "")]
            keys.append((f"c{r.company_id}", f"{co} — Toàn pháp nhân"))
        return keys

    def position_key(r):
        """Dòng kế hoạch mang `position_id`; người thì xếp theo `PositionUnits` để cùng khóa với bảng."""
        pos = units.key_of_person(r) if getattr(r, "level", "") == "person" and units else r.position_id
        return [(pos or "", (position_name or {}).get(pos, ""))]      # khóa "" hiện «(Chưa gắn)» như mọi chiều

    dims = {"company": DimensionSpec("company", "Pháp nhân", key_of=company_key),
            "department": DimensionSpec("department", "Phòng ban", key_of=department_key),
            "position": DimensionSpec("position", "Vị trí", key_of=position_key)}
    return ReportSpec(date_of=lambda r: None, metrics=metrics, derived=derived, dimensions=dims,
                      rank_by="planned"), dims


def _context(period: Period):
    """(năm, tháng) của kế hoạch có hiệu lực = tháng cuối kỳ báo cáo; mốc đếm người thực tế."""
    as_of = min(period.date_to, vn_today())
    return period.date_to.year, period.date_to.month, as_of


def _notes(rows: list[PlanRow], year: int, month: int, as_of, department_name: dict, company_name: dict) -> list[str]:
    notes = [
        f"Định biên kế hoạch lấy ở tháng {month:02d}/{year} (tháng cuối kỳ báo cáo) từ «Kế hoạch nhân sự»; kỳ hẹp "
        f"(tháng, quý) thay kỳ rộng (bán niên, năm) cho đúng các tháng nó phủ. Thực tế tại {as_of:%d/%m/%Y} "
        "(cuối kỳ hoặc hôm nay nếu kỳ chưa kết thúc). Không có xu hướng và không so sánh kỳ trước.",
        "Pháp nhân có dòng kế hoạch «Toàn pháp nhân» thì dòng đó so với TỔNG người của pháp nhân và là số duy nhất "
        "tính vào Tổng cộng và nhóm Pháp nhân; các dòng phòng của pháp nhân đó chỉ hiện khi Xem theo Phòng ban "
        "(không cộng dồn thêm). Xem theo Vị trí: dòng vị trí so với người giữ đúng vị trí; người ở vị trí kế hoạch không "
        "liệt kê gộp vào nhóm «(Chưa gắn)».",
        "Tỷ lệ lấp đầy = số vị trí kế hoạch đã có người (không tính phần vượt) ÷ định biên kế hoạch. "
        "«Còn thiếu» / «Vượt» cộng theo từng dòng kế hoạch nên thiếu ở phòng này không bù được bằng thừa ở phòng khác.",
    ]
    unplanned = [r for r in rows if not r.has_plan]
    if unplanned:
        names = [f"{department_name.get(r.department_id) or '(chưa gắn phòng)'} — {company_name.get(r.company_id, '')} "
                 f"({r.actual})" for r in unplanned[:10]]
        more = f" và {len(unplanned) - 10} nơi khác" if len(unplanned) > 10 else ""
        notes.append(f"Có {len(unplanned)} nơi có người nhưng chưa có kế hoạch hiệu lực ở tháng {month:02d}/{year}: "
                     + "; ".join(names) + more + ". Số người này nằm trong «Đang có» và «Đang làm ở phòng chưa có kế hoạch».")
    return notes


def build_summary(db: Session, user, prof: dict, period: Period, group_by: str | None,
                  company_id: int | None = None, department_id: int | None = None,
                  action: str = "read") -> dict:
    year, month, as_of = _context(period)
    company_name, department_name = load_group_names(db, group_by, always=True)
    entries = load_plan_entries(db, user, prof, year, month, company_id, department_id, action)
    position_counts = load_counts(db, user, prof, as_of, company_id, department_id, action)
    rows = build_plan_rows(entries, dept_counts(position_counts))
    top = [r for r in rows if r.top]
    units = PositionUnits(entries)
    spec, _ = _spec(company_name, department_name, load_position_names(db, group_by), units)
    flat = replace(period, compare="none", compare_from=None, compare_to=None)
    shown = rows if group_by == "department" else units.build_rows(position_counts) if group_by == "position" else top
    data = build_report(lambda _f, _t: shown, spec, flat, group_by=group_by)
    if shown is not top:      # Xem theo Phòng ban / Vị trí liệt kê dòng khác tập `top` -> Tổng tính riêng, không cộng đôi
        data["totals"] = build_report(lambda _f, _t: top, spec, flat)["totals"]
    data["period"] = period.as_dict()
    data["trend"] = []
    data["meta"]["drilldown_metrics"] = list(METRICS)
    data["notes"] = _notes(rows, year, month, as_of, department_name, company_name)
    return data


def build_rows(db: Session, user, prof: dict, period: Period, metric: str, group_by: str | None,
               group_key: str | None, company_id: int | None, department_id: int | None) -> dict:
    year, month, as_of = _context(period)
    company_name, department_name = load_group_names(db, group_by, always=True)
    entries = load_plan_entries(db, user, prof, year, month, company_id, department_id)
    units = PositionUnits(entries)
    _, dims = _spec(company_name, department_name, load_position_names(db, group_by), units)
    if group_by and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    people = load_people(db, user, prof, as_of, company_id, department_id)
    picked = people
    if metric == "unplanned":
        rows = build_plan_rows(entries, counts_of(people))
        #  KHỚP KPI: Tổng / nhóm Pháp nhân chỉ đếm dòng `top` — phòng chưa kế hoạch của pháp nhân đã có dòng
        #  «Toàn pháp nhân» KHÔNG tính. Chỉ khi bấm vào MỘT nhóm Phòng ban (không phải nhóm `c<id>`) mới liệt kê cả
        #  những phòng đó, vì bảng «Xem theo Phòng ban» có hiện chúng.
        covered = {r.company_id for r in rows if r.level == "company"}
        one_dept_group = group_by == "department" and bool(group_key) and not str(group_key).startswith("c")
        no_plan = {(r.company_id, r.department_id) for r in rows
                   if not r.has_plan and (one_dept_group or r.company_id not in covered)}
        picked = [p for p in people if (p.company_id, p.department_id) in no_plan]
    picked = filter_group(picked, dims.get(group_by) if group_by else None, group_key)
    picked.sort(key=lambda p: (p.code, p.employee_id))
    out = [{"code": p.code, "name": p.name, "department": department_name.get(p.department_id, ""),
            "position": p.position, "hire_date": p.hire_date, "link": f"/hr/employees/{p.employee_id}"}
           for p in picked]
    return rows_response(metric, METRICS[metric], COLUMNS, out)
