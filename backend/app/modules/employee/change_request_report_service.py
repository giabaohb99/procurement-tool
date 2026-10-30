"""Báo cáo E2 "Yêu cầu sửa hồ sơ" kiểu Haravan (khóa 27, duoc-CR-689) — `/api/profile-change-report`.

Trục thời gian = NGÀY GỬI yêu cầu (giờ VN). "Chờ quá 2 ngày" tính tới hôm nay. Một yêu cầu xin sửa
nhiều trường thì xuất hiện ở nhiều nhóm khi xem theo "Trường bị xin sửa" (tổng vẫn đếm một lần).
`/summary/rows` dùng đúng `load_rows` + đúng `key_of` của chiều gom nên danh sách khớp con số, và
KHÔNG trả giá trị cũ / mới của trường.
"""
from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.hr_change_request_codes import EmployeeChangeRequestStatus as Status
from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.vn_time import vn_today

from . import change_request_report_data as data_mod
from . import change_request_view
from .change_request_report_data import FIELD_LABELS, STATUS_LABELS, ChangeRow
from .profile_gaps_report_data import load_group_names

_PENDING, _APPROVED, _REJECTED = (int(Status.PENDING), int(Status.APPROVED), int(Status.REJECTED))
#  Chỉ số -> điều kiện hàng thuộc chỉ số (dùng cho cả đếm lẫn danh sách bấm số).
PREDICATES = {
    "requests": lambda r: True,
    "pending": lambda r: r.status == _PENDING,
    "pending_over_2d": lambda r: r.pending_over,
    "approved": lambda r: r.status == _APPROVED,
    "rejected": lambda r: r.status == _REJECTED,
}
LABELS = {"requests": "Số yêu cầu", "pending": "Đang chờ", "pending_over_2d": "Chờ quá 2 ngày",
          "approved": "Đã duyệt", "rejected": "Từ chối"}
_GOOD = {"pending": "down", "pending_over_2d": "down", "rejected": "down"}


def _build_spec(company_name: dict, department_name: dict) -> tuple[ReportSpec, dict[str, DimensionSpec]]:
    metrics = [MetricSpec(k, LABELS[k], good=_GOOD.get(k), value_of=(lambda r, k=k: int(PREDICATES[k](r))))
               for k in PREDICATES]
    metrics += [MetricSpec("decided", "Đã xử lý", helper=True, value_of=lambda r: int(r.status in (_APPROVED, _REJECTED))),
                MetricSpec("decided_hours", "Tổng giờ xử lý", kind="hours", helper=True,
                           value_of=lambda r: r.hours or 0.0)]
    derived = [DerivedSpec("reject_rate", "Tỷ lệ từ chối", num="rejected", den="decided", good="down"),
               DerivedSpec("turnaround_hours", "Giờ xử lý bình quân", num="decided_hours", den="decided",
                           kind="hours", scale=1.0, good="down")]
    dims = {
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "field": DimensionSpec("field", "Trường bị xin sửa", key_of=lambda r: [
            (f, FIELD_LABELS.get(f, f)) for f in r.fields]),
        "status": DimensionSpec("status", "Trạng thái", key_of=lambda r: [(r.status, STATUS_LABELS.get(r.status, ""))]),
    }
    spec = ReportSpec(date_of=lambda r: r.created_date, metrics=metrics, derived=derived,
                      dimensions=dims, rank_by="requests")
    return spec, dims


def build_summary(db: Session, employees_q, period: Period, group_by: str | None, *,
                  company_id: int | None = None, department_id: int | None = None) -> dict:
    today = vn_today()
    company_name, department_name = load_group_names(db, group_by)
    spec, _ = _build_spec(company_name, department_name)
    data = build_report(lambda d_from, d_to: data_mod.load_rows(
        db, employees_q, d_from, d_to, today, company_id=company_id, department_id=department_id),
        spec, period, group_by=group_by)
    data["meta"]["drilldown_metrics"] = list(PREDICATES)
    data["notes"] = list(data.get("notes") or []) + [
        "Tính theo NGÀY GỬI yêu cầu. \"Chờ quá 2 ngày\" tính tới hôm nay, không phụ thuộc kỳ đang chọn.",
        "Giờ xử lý bình quân chỉ tính yêu cầu đã duyệt hoặc từ chối (không tính yêu cầu bị rút lại).",
        "Một yêu cầu xin sửa nhiều trường sẽ hiện ở nhiều dòng khi xem theo \"Trường bị xin sửa\".",
        "Báo cáo không hiển thị nội dung cũ / mới của các trường được xin sửa."]
    return data


COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("department", "Phòng ban"),
           Col("created_date", "Ngày gửi", "date"), Col("status", "Trạng thái"),
           Col("field_count", "Số trường", "int"), Col("decided_by_name", "Người duyệt"),
           Col("decided_date", "Ngày duyệt", "date")]


def build_rows(db: Session, employees_q, period: Period, metric: str, group_by: str | None,
               group_key: str | None, *, company_id: int | None = None, department_id: int | None = None) -> dict:
    company_name, department_name = load_group_names(db, group_by, always=True)
    _, dims = _build_spec(company_name, department_name)
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = data_mod.load_rows(db, employees_q, period.date_from, period.date_to, vn_today(),
                              company_id=company_id, department_id=department_id)
    rows = filter_group([r for r in rows if PREDICATES[metric](r)], dims.get(group_by) if group_by else None, group_key)
    rows.sort(key=lambda r: (r.created_date or date.min, r.request_id), reverse=True)
    names = change_request_view.user_names(db, rows) if any(r.decided_by for r in rows) else {}
    return rows_response(metric, LABELS[metric], COLUMNS, [{
        "employee_code": r.employee_code, "employee_name": r.employee_name,
        "department": department_name.get(r.department_id, ""), "created_date": r.created_date,
        "status": STATUS_LABELS.get(r.status, ""), "field_count": len(r.fields),
        "decided_by_name": names.get(r.decided_by, ""), "decided_date": r.decided_date,
        "link": f"/hr/employees/{r.employee_id}"} for r in rows])
