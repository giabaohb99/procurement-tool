"""Báo cáo C3 "Có mặt theo ngày" (duoc-CR-689, khóa 26) — `GET /api/attendance-report/summary`.

Đơn vị là NGƯỜI-NGÀY: mỗi người × mỗi ngày họ phải làm (xem `attendance_report_data.py`).
Chỉ số cộng được: phải làm · nghỉ (đơn đã duyệt) · có mặt; tỷ lệ có mặt / vắng là chỉ số dẫn xuất.
Xu hướng theo ngày / tuần / tháng theo độ hạt của kỳ. Xem theo phòng ban · pháp nhân (hồ sơ HIỆN TẠI).
"""
from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.vn_time import vn_today
from app.modules.employee.model import Employee
from app.modules.employee.profile_gaps_report_data import load_group_names
from app.modules.leave.catalog_model import LeaveType

from .attendance_report_data import DayRow, check_period, load_day_rows

METRICS = {"on_leave": "Người-ngày nghỉ (đã duyệt)"}     # chỉ số có danh sách `/rows`
LEAVE_KEYS = ("on_leave", "present", "present_rate", "absence_rate")
NO_LEAVE_NOTE = ("Bạn chưa có quyền xem đơn nghỉ phép nên các chỉ số nghỉ, có mặt và tỷ lệ để trống; "
                 "chỉ còn \"Người-ngày phải làm\".")
COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("department", "Phòng ban"),
           Col("day", "Ngày", "date"), Col("leave_type", "Loại nghỉ"), Col("session", "Buổi")]


def _dims(company_name: dict, department_name: dict) -> dict[str, DimensionSpec]:
    return {
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "company": DimensionSpec("company", "Pháp nhân", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
    }


def _spec(dims: dict) -> ReportSpec:
    return ReportSpec(
        date_of=lambda r: r.day,
        metrics=[MetricSpec("scheduled", "Người-ngày phải làm", kind="days", value_of=lambda r: r.scheduled),
                 MetricSpec("on_leave", METRICS["on_leave"], kind="days", value_of=lambda r: r.on_leave),
                 MetricSpec("present", "Người-ngày có mặt", kind="days", good="up", value_of=lambda r: r.present)],
        derived=[DerivedSpec("present_rate", "Tỷ lệ có mặt", num="present", den="scheduled", good="up"),
                 DerivedSpec("absence_rate", "Tỷ lệ vắng", num="on_leave", den="scheduled", good="down")],
        dimensions=dims, rank_by="scheduled")


def _blank_leave(data: dict) -> None:
    """Thiếu quyền xem đơn nghỉ: GỠ hẳn các chỉ số liên quan nghỉ khỏi `meta` (màn hình và tệp Excel
    không có cột đó — để `None` thì Excel quy về 0, đọc nhầm thành "không ai nghỉ", E2E 28/10/2026) và
    bỏ giá trị ở Tổng · xu hướng · nhóm."""
    data["meta"]["metrics"] = [m for m in data["meta"]["metrics"] if m["key"] not in LEAVE_KEYS]

    def blank(values):
        if values:
            for k in LEAVE_KEYS:
                values.pop(k, None)
    cells = [data["totals"]] + list(data.get("trend") or []) + list(data.get("groups") or [])
    for cell in cells:
        blank(cell.get("current"))
        blank(cell.get("compare"))


def _load(db: Session, emp_q, leave_q, with_leave: bool, d_from: date, d_to: date) -> list[DayRow]:
    return load_day_rows(db, emp_q, leave_q, d_from, d_to, with_leave=with_leave)


def build_summary(db: Session, emp_q, leave_q, with_leave: bool, period: Period, group_by: str | None) -> dict:
    check_period(period.date_from, period.date_to)
    company_name, department_name = load_group_names(db, group_by)
    dims = _dims(company_name, department_name)
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    data = build_report(lambda f, t: _load(db, emp_q, leave_q, with_leave, f, t), _spec(dims), period,
                        group_by=group_by)
    data["meta"]["drilldown_metrics"] = list(METRICS) if with_leave else []
    data["notes"] = [
        "Người-ngày phải làm: mỗi người × mỗi ngày họ có lịch làm theo lịch làm việc RIÊNG của họ, trừ ngày "
        "lễ và những ngày chưa vào làm / đã nghỉ việc. Ngày làm nửa buổi tính 0,5.",
        "Nghỉ = đơn nghỉ phép ĐÃ DUYỆT phủ ngày đó (nửa buổi 0,5; nghỉ theo giờ tính theo tỉ lệ giờ). "
        "Có mặt = phải làm − nghỉ; chưa phải số chấm công thực tế (đi trễ, vắng không phép chưa có dữ liệu).",
        "Phòng ban / pháp nhân lấy theo hồ sơ HIỆN TẠI. Chỉ tính đến hết hôm nay; ngày chưa tới chưa tính.",
        "Nghỉ chỉ đếm đơn nằm trong phạm vi xem đơn nghỉ phép của bạn."]
    if period.date_to > vn_today():
        data["notes"].append("Kỳ đã chọn kéo dài sang tương lai nên chỉ tính tới hôm nay.")
    if not with_leave:
        data["notes"].append(NO_LEAVE_NOTE)
        _blank_leave(data)
    return data


def _row_dict(r: DayRow, department_name: dict, type_name: dict) -> list[dict]:
    base = {"employee_code": r.code, "employee_name": r.name, "department": department_name.get(r.department_id, ""),
            "day": r.day, "link": f"/hr/employees/{r.employee_id}"}
    return [{**base, "leave_type": type_name.get(t, ""), "session": s} for t, s in r.leaves] or \
        [{**base, "leave_type": "", "session": ""}]


def build_rows(db: Session, emp_q, leave_q, period: Period, metric: str, group_by: str | None,
               group_key: str | None) -> dict:
    check_period(period.date_from, period.date_to)
    company_name, department_name = load_group_names(db, None, always=True)
    dims = _dims(company_name, department_name)
    if group_by and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = [r for r in _load(db, emp_q, leave_q, True, period.date_from, period.date_to) if r.on_leave > 0]
    rows = filter_group(rows, dims.get(group_by) if group_by else None, group_key)
    rows.sort(key=lambda r: (r.day, r.code))
    type_name = {t.id: t.name for t in db.query(LeaveType.id, LeaveType.name).all()}
    flat = [x for r in rows for x in _row_dict(r, department_name, type_name)]
    return rows_response(metric, METRICS[metric], COLUMNS, flat)
