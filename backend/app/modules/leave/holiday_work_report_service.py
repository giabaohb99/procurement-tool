"""Báo cáo "Làm việc vào ngày lễ, ngày nghỉ" (duoc-CR-717, khóa 30) — khung `build_report` + danh sách `/rows`.

Đơn vị là NGƯỜI-NGÀY có phiếu nghỉ bù (xem `holiday_work_report_data.py`). Mặc định chỉ phiếu Đã duyệt;
`include_pending` thêm phiếu Chờ duyệt (chỉ số "Đang chờ duyệt" chỉ hiện khi bật).
"""
from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session

from app.core.report_aggregate import DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.modules.employee.profile_gaps_report_data import load_group_names

from .constants import LEAVE_COMP_STATUS_LABELS, LeaveCompStatus
from .holiday_work_report_data import (DAY_KIND_LABELS, WEEKDAYS, HolidayWorkRow, check_period, load_rows)

METRICS = {"lines": "Lượt đi làm"}     # chỉ số có danh sách `/rows`
_APPROVED, _PENDING = int(LeaveCompStatus.APPROVED), int(LeaveCompStatus.PENDING)
COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("department", "Phòng ban"),
           Col("work_date", "Ngày", "date"), Col("weekday", "Thứ"), Col("day_kind", "Loại ngày"),
           Col("holiday_name", "Tên ngày lễ"), Col("days", "Số ngày bù", "days"),
           Col("status", "Trạng thái phiếu"), Col("code", "Mã phiếu")]
NOTES = ["Không có chấm công — chỉ thấy người đã lập phiếu nghỉ bù; dữ liệu có từ 02/11/2026.",
         "Loại ngày tính theo lịch ngày lễ hiện hành: trùng ngày lễ → \"Ngày lễ\", còn lại → \"Ngày nghỉ theo lịch\".",
         "Phòng ban là phòng ghi trên phiếu (phòng lúc đi làm). Mặc định chỉ tính phiếu Đã duyệt."]


def _dims(company_name: dict, department_name: dict) -> dict[str, DimensionSpec]:
    return {
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "company": DimensionSpec("company", "Pháp nhân", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "employee": DimensionSpec("employee", "Nhân sự", key_of=lambda r: (
            [(r.employee_id, r.employee_name)] if r.employee_id else [])),
        "day_kind": DimensionSpec("day_kind", "Loại ngày", key_of=lambda r: [(r.day_kind, DAY_KIND_LABELS[r.day_kind])]),
        "holiday_name": DimensionSpec("holiday_name", "Tên ngày lễ", key_of=lambda r: (
            [(r.holiday_name, r.holiday_name)] if r.holiday_name else [])),
    }


def _spec(dims: dict, include_pending: bool) -> ReportSpec:
    metrics = [
        MetricSpec("lines", METRICS["lines"], kind="int", value_of=lambda r: 1),
        MetricSpec("holiday_lines", "Trong đó ngày lễ", kind="int", value_of=lambda r: 1 if r.day_kind == 1 else 0),
        MetricSpec("offday_lines", "Ngày nghỉ theo lịch", kind="int", value_of=lambda r: 1 if r.day_kind == 2 else 0),
        MetricSpec("people", "Số người", kind="int", distinct_of=lambda r: r.employee_id),
        MetricSpec("comp_days", "Ngày nghỉ bù được duyệt", kind="days",
                   value_of=lambda r: r.days if r.status == _APPROVED else 0.0)]
    if include_pending:
        metrics.append(MetricSpec("pending_lines", "Đang chờ duyệt", kind="int", good="down",
                                  value_of=lambda r: 1 if r.status == _PENDING else 0))
    return ReportSpec(date_of=lambda r: r.work_date, metrics=metrics, dimensions=dims, rank_by="lines")


def _check_group(group_by: str | None, dims: dict) -> None:
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")


def build_summary(db: Session, comp_q: Query, period: Period, group_by: str | None,
                  include_pending: bool, day_kind: int) -> dict:
    check_period(period.date_from, period.date_to)
    company_name, department_name = load_group_names(db, group_by)
    dims = _dims(company_name, department_name)
    _check_group(group_by, dims)

    def fetch(d_from: date, d_to: date) -> list[HolidayWorkRow]:
        return load_rows(db, comp_q, d_from, d_to, include_pending, day_kind)

    data = build_report(fetch, _spec(dims, include_pending), period, group_by=group_by)
    data["meta"]["drilldown_metrics"] = list(METRICS)
    data["notes"] = list(NOTES) + (["Đang gồm cả phiếu Chờ duyệt (chưa cộng quỹ nghỉ bù)."] if include_pending else [])
    return data


def _row_dict(r: HolidayWorkRow, department_name: dict) -> dict:
    return {"employee_code": r.employee_code, "employee_name": r.employee_name,
            "department": department_name.get(r.department_id, ""), "work_date": r.work_date,
            "weekday": WEEKDAYS[r.work_date.weekday()], "day_kind": DAY_KIND_LABELS[r.day_kind],
            "holiday_name": r.holiday_name, "days": r.days,
            "status": LEAVE_COMP_STATUS_LABELS.get(LeaveCompStatus(r.status), ""), "code": r.code,
            "link": f"/hr/employees/{r.employee_id}"}


def build_rows(db: Session, comp_q: Query, period: Period, metric: str, group_by: str | None,
               group_key: str | None, include_pending: bool, day_kind: int) -> dict:
    company_name, department_name = load_group_names(db, None, always=True)
    dims = _dims(company_name, department_name)
    if group_by and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = load_rows(db, comp_q, period.date_from, period.date_to, include_pending, day_kind)
    rows = filter_group(rows, dims.get(group_by) if group_by else None, group_key)
    rows.sort(key=lambda r: (r.work_date, r.employee_code, r.code))
    return rows_response(metric, METRICS[metric], COLUMNS, [_row_dict(r, department_name) for r in rows])
