"""Báo cáo B4 "Đối tượng cần chú ý theo luật" kiểu Haravan (khóa 29, duoc-CR-689) — `/api/legal-watch/summary`.

Tình trạng tại mốc `as_of = min(cuối kỳ, hôm nay)`; không có xu hướng, không có kỳ so sánh. Dữ liệu dùng
ngày sinh và con nhỏ nên controller đòi `employee_sensitive.read`. "Đang nghỉ thai sản" = đơn đã duyệt (theo phạm
vi đơn nghỉ phép, `leave_q`) HỢP hồ sơ ở trạng thái nghỉ thai sản (chỉ khi mốc là hôm nay); thiếu quyền xem đơn
thì chỉ còn nhánh hồ sơ. `/rows` không in ngày sinh — chỉ MỐC.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.vn_time import vn_today

from . import legal_watch_report_data as data_mod
from .legal_watch_report_data import KINDS, WatchRow
from .profile_gaps_report_data import load_group_names

LABELS = {
    "retire_12m": "Đến tuổi nghỉ hưu trong 12 tháng", "past_retirement": "Đã quá tuổi nghỉ hưu, vẫn đang làm",
    "maternity_now": "Đang nghỉ thai sản",
    "child_under_12m": "Lao động nữ nuôi con dưới 12 tháng", "people": "Số người cần chú ý",
}
MILESTONE_LABELS = {"retire_12m": "Thời điểm nghỉ hưu", "past_retirement": "Thời điểm nghỉ hưu",
                    "maternity_now": "Ngày đi làm lại",
                    "child_under_12m": "Ngày con đủ 12 tháng"}
_COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("department", "Phòng ban"),
            Col("kind", "Loại"), Col("milestone", "Mốc", "date")]


def visible_kinds() -> tuple[str, ...]:
    """Mọi loại đều hiện: thai sản còn đếm theo hồ sơ nhân sự nên không còn phụ thuộc quyền xem đơn nghỉ phép."""
    return KINDS


def as_of_of(period: Period, today: date | None = None) -> date:
    return min(period.date_to, today or vn_today())


def _build_spec(kinds: tuple[str, ...], company_name: dict, department_name: dict
                ) -> tuple[ReportSpec, dict[str, DimensionSpec]]:
    metrics = [MetricSpec(k, LABELS[k], value_of=(lambda r, k=k: int(r.kind == k))) for k in kinds]
    metrics.append(MetricSpec("people", LABELS["people"], helper=True, distinct_of=lambda r: r.employee_id))
    dims = {
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "kind": DimensionSpec("kind", "Loại đối tượng", key_of=lambda r: [(r.kind, LABELS[r.kind])]),
    }
    return ReportSpec(date_of=lambda r: None, metrics=metrics, dimensions=dims, rank_by="people"), dims


def build_summary(db: Session, employees_q, period: Period, group_by: str | None, *, leave_q=None,
                  company_id: int | None = None, department_id: int | None = None) -> dict:
    kinds = visible_kinds()
    as_of = as_of_of(period)
    spec, _ = _build_spec(kinds, *load_group_names(db, group_by))
    rows = data_mod.load_rows(db, employees_q, as_of, leave_q=leave_q, company_id=company_id,
                              department_id=department_id)
    flat = replace(period, compare="none", compare_from=None, compare_to=None)
    data = build_report(lambda _f, _t: rows, spec, flat, group_by=group_by)
    data["period"] = period.as_dict()
    data["trend"] = []
    data["meta"]["drilldown_metrics"] = list(kinds)
    data["notes"] = [
        f"Tình trạng tại ngày {as_of.strftime('%d/%m/%Y')} (cuối kỳ đang chọn hoặc hôm nay, lấy ngày sớm hơn).",
        "Tuổi nghỉ hưu theo lộ trình Nghị định 135/2020/NĐ-CP, điều kiện lao động bình thường; thời điểm nghỉ hưu là cuối tháng đủ tuổi "
        "(nam 60 tuổi 3 tháng năm 2021, tăng 3 tháng mỗi năm tới 62 tuổi năm 2028; nữ 55 tuổi 4 tháng, "
        "tăng 4 tháng mỗi năm tới 60 tuổi năm 2035). Chỉ tính người đã có ngày sinh và giới tính; "
        "không xét nghề nặng nhọc, độc hại được nghỉ sớm. \"Đã quá tuổi nghỉ hưu\" là người qua thời điểm đó mà vẫn đang làm.",
        "\"Nuôi con dưới 12 tháng\" tính từ danh sách hộ gia đình: nhân sự nữ có con trai / con gái sinh trong 12 tháng gần nhất."]
    data["notes"].append(
        "\"Đang nghỉ thai sản\" đếm cả người có đơn nghỉ thai sản đã duyệt phủ ngày tính (theo phạm vi đơn nghỉ phép của bạn) "
        "lẫn người có hồ sơ nhân sự ở trạng thái \"Nghỉ thai sản\"; một người chỉ đếm một lần, người không có đơn thì "
        "\"Ngày đi làm lại\" để trống.")
    if as_of < vn_today():
        data["notes"].append("Trạng thái hồ sơ nhân sự là trạng thái hiện tại nên không dùng cho kỳ đã qua: "
                             "\"Đang nghỉ thai sản\" của kỳ này chỉ theo đơn nghỉ thai sản đã duyệt.")
    return data


def build_rows(db: Session, employees_q, period: Period, metric: str, group_by: str | None,
               group_key: str | None, *, leave_q=None, company_id: int | None = None,
               department_id: int | None = None) -> dict:
    company_name, department_name = load_group_names(db, group_by, always=True)
    _, dims = _build_spec(visible_kinds(), company_name, department_name)
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = data_mod.load_rows(db, employees_q, as_of_of(period), leave_q=leave_q,
                              company_id=company_id, department_id=department_id)
    rows = filter_group([r for r in rows if r.kind == metric], dims.get(group_by) if group_by else None, group_key)
    rows.sort(key=lambda r: (r.milestone is None, r.milestone or date.min, r.employee_code))
    return rows_response(metric, LABELS[metric], _COLUMNS, [{
        "employee_code": r.employee_code, "employee_name": r.employee_name,
        "department": department_name.get(r.department_id, ""), "kind": LABELS[r.kind],
        "milestone": r.milestone, "milestone_label": MILESTONE_LABELS[r.kind],
        "link": f"/hr/employees/{r.employee_id}"} for r in rows])
