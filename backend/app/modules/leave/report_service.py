"""Báo cáo Nghỉ phép — tình hình nghỉ (phase 04, `GET /api/leave-requests/summary`).

Gói B (review hiệu năng 01/10/2026): CỘNG chuyển hẳn vào SQL — xem docstring đầu
`report_sql_metrics.py` để biết VÌ SAO khung Python `report_aggregate.build_report()` không
đủ nhanh cho `group_by=employee` ở quy mô nhiều năm (14-23s đo được ở 60 nghìn đơn/3 năm, 79%
là vòng lặp Python). `build_summary()` dưới đây KHÔNG còn gọi `build_report()`/`aggregate()` —
tự dựng `totals`/`trend`/`groups`/`breakdowns` bằng 3 tệp `report_sql_*.py`, rồi tái dùng các
hàm GHÉP KỲ SO SÁNH của `report_compute.py` (`merge_trend_by_index`/`merge_groups_by_key`/
`compare_shift`) — những hàm đó chỉ cần dữ liệu đúng khuôn `{"key","label","values"}`, không
biết/không cần biết hàng gốc đi qua SQL hay Python trước đó.

`_build_spec()` GIỮ NGUYÊN hình dạng bản cũ — nay CHỈ còn phục vụ `meta_of()` (nhãn/kind/
helper cho FE) và validate `group_by` qua `spec.dimensions`. Các lambda `key_of`/`value_of`/
`distinct_of` bên trong KHÔNG còn được gọi (không còn hàng `LeaveRow` nào được nạp) — giữ lại
vì vẫn là tài liệu ĐÚNG của ý nghĩa từng chỉ số, và tách riêng `MetricSpec`/`DimensionSpec`
thành khuôn mới là việc không cần thiết (YAGNI) khi hai dataclass đó vẫn đúng khuôn cho
`meta_of()`. Công thức 2 chỉ số dẫn xuất (`reject_return_rate`/`avg_turnaround_hours`) nay
sống Ở MỘT CHỖ DUY NHẤT — `report_sql_metrics.DERIVED` — tái dùng lại đây, tránh hai công thức
lệch nhau.

Phạm vi: `apply_scope(entity="leave_request")` — bậc `own` đã HỢP sẵn người LẬP
(`created_by`) và người NGHỈ (`employee_id`, xem `scoping._role_scope_cond` nhánh `own`),
KHÔNG nới thêm "đang có việc duyệt" (ngoại lệ đó chỉ dành cho đọc MỘT đơn lẻ —
`approval_bridge.can_read_request`).
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DimensionSpec, MetricSpec, ReportSpec
from app.core.report_compute import (compare_shift, compute_derived, merge_groups_by_key,
                                     merge_trend_by_index, meta_of)
from app.core.report_period import Period, bucket_axis
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LEAVE_REQUEST_STATUS_LABELS
from app.modules.leave.report_rows import header_subquery, scoped_requests
from app.modules.leave.report_sql_groups import (breakdown_by_status, breakdown_leave_type_by_days,
                                                 cap_groups, groups_for_dim)
from app.modules.leave.report_sql_metrics import DERIVED, header_aggregate, line_aggregate, totals_dict
from app.modules.leave.report_sql_trend import trend_for_period


def _build_spec() -> ReportSpec:
    """CHỈ còn phục vụ `meta_of()` (nhãn/kind/helper cho FE) + validate tên `group_by` qua
    `spec.dimensions` — KHÔNG hàng nào còn được gom bằng `key_of`/`value_of`/`distinct_of` của
    hai dataclass này nữa (gói B chuyển hết việc CỘNG sang SQL). `_unused` dưới đây CHỈ để thỏa
    ràng buộc kiểu của `MetricSpec.__post_init__` (đòi đúng 1 trong `value_of`/`distinct_of`) —
    đọc Ý NGHĨA THẬT của từng chỉ số ở docstring `report_sql_metrics.py`/`report_sql_groups.py`/
    `report_sql_trend.py`; sửa logic ở ĐÂY không đổi được hành vi báo cáo.
    """
    def _unused(*_a):
        return None

    metrics = [
        MetricSpec("requests", "Số đơn", kind="int", distinct_of=_unused),
        MetricSpec("days_approved", "Ngày nghỉ đã duyệt", kind="days", value_of=_unused),
        MetricSpec("days_pending", "Ngày đang chờ duyệt", kind="days", value_of=_unused),
        MetricSpec("people_on_leave", "Số người nghỉ", kind="int", distinct_of=_unused),
        MetricSpec("requests_reject_return", "Đơn từ chối/trả về", kind="int", helper=True,
                  distinct_of=_unused),
        MetricSpec("turnaround_hours_sum", "Tổng giờ xử lý", kind="hours", helper=True,
                  value_of=_unused),
        MetricSpec("turnaround_hours_count", "Số đơn có thời gian xử lý", kind="int", helper=True,
                  value_of=_unused),
    ]
    dimensions = {
        "leave_type": DimensionSpec("leave_type", "Loại nghỉ", key_of=_unused),
        "department": DimensionSpec("department", "Phòng ban", key_of=_unused),
        "company": DimensionSpec("company", "Công ty", key_of=_unused),
        "employee": DimensionSpec("employee", "Nhân sự", key_of=_unused),
        "status": DimensionSpec("status", "Trạng thái", key_of=_unused),
    }
    return ReportSpec(date_of=_unused, metrics=metrics, derived=DERIVED, dimensions=dimensions,
                      breakdowns={"leave_type": dimensions["leave_type"], "status": dimensions["status"]},
                      rank_by="requests")


def _label_lookups(group_by: str | None, type_name: dict, emp_name: dict, company_name: dict,
                   department_name: dict) -> dict:
    """Hàm tra NHÃN theo khóa số, một hàm cho mỗi chiều — dùng cho cả `groups` lẫn
    `breakdowns`. `status`/`leave_type` LUÔN có (breakdown dùng mọi lúc); công ty/phòng
    ban/nhân sự chỉ tra khi CHÍNH chiều đó được chọn "Xem theo" (như bản cũ)."""
    return {
        "status": lambda v: LEAVE_REQUEST_STATUS_LABELS.get(v, ""),
        "leave_type": lambda v: type_name.get(v, ""),
        "company": lambda v: company_name.get(v, ""),
        "department": lambda v: department_name.get(v, ""),
        "employee": lambda v: emp_name.get(v, ""),
    }


def _totals_for_period(db: Session, scoped, header_subq) -> dict:
    values = totals_dict(header_aggregate(db, scoped, group_col=None),
                         line_aggregate(db, header_subq, group_col=None))
    values.update(compute_derived(values, DERIVED))
    return values


def build_summary(db: Session, user, prof: dict, period: Period, group_by: str | None,
                  company_id: int | None = None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/leave-requests/summary` (+ `/export`)."""
    spec = _build_spec()
    if group_by and group_by != "none" and group_by not in spec.dimensions:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")

    type_name = {t.id: t.name for t in db.query(LeaveType.id, LeaveType.name).all()}
    emp_name = ({e.id: e.full_name for e in db.query(Employee.id, Employee.full_name).all()}
               if group_by == "employee" else {})
    company_name = ({c.id: c.name for c in db.query(Company.id, Company.name).all()}
                    if group_by == "company" else {})
    department_name = ({d.id: d.name for d in db.query(Department.id, Department.name).all()}
                       if group_by == "department" else {})
    label_of = _label_lookups(group_by, type_name, emp_name, company_name, department_name)

    def _fetch(d_from, d_to, need_breakdowns: bool):
        scoped = scoped_requests(db, user, prof, d_from, d_to, company_id)
        header_subq = header_subquery(scoped)
        groups = None
        if group_by and group_by != "none":
            groups = groups_for_dim(db, scoped, header_subq, group_by, label_of[group_by])
            #  Trần GROUP_LIMIT — gói A3 (01/10/2026) thêm cho `report_aggregate.aggregate()`;
            #  đường SQL này bỏ qua hàm đó nên phải tự cắt lại, xem docstring `cap_groups`.
            groups = cap_groups(db, scoped, header_subq, group_by, groups, spec.rank_key())
        breakdowns = ({"status": breakdown_by_status(db, scoped, label_of["status"]),
                      "leave_type": breakdown_leave_type_by_days(db, header_subq, type_name)}
                     if need_breakdowns else {})
        return {"totals": _totals_for_period(db, scoped, header_subq), "groups": groups,
               "breakdowns": breakdowns, "scoped": scoped, "header_subq": header_subq}

    axis = bucket_axis(period.date_from, period.date_to, period.granularity)
    cur = _fetch(period.date_from, period.date_to, need_breakdowns=True)
    cur_trend = trend_for_period(db, cur["scoped"], cur["header_subq"], axis, period.granularity)

    cmp = None
    cmp_trend = None
    if period.compare != "none" and period.compare_from and period.compare_to:
        cmp = _fetch(period.compare_from, period.compare_to, need_breakdowns=False)
        cmp_trend = trend_for_period(db, cmp["scoped"], cmp["header_subq"], axis,
                                     period.granularity, shift=compare_shift(period))

    result = {"period": period.as_dict(), "meta": meta_of(spec, group_by),
             "totals": {"current": cur["totals"], "compare": cmp["totals"] if cmp else None},
             "trend": merge_trend_by_index(cur_trend, cmp_trend),
             "breakdowns": cur["breakdowns"], "notes": []}
    if cur["groups"] is not None:
        result["groups"] = merge_groups_by_key(cur["groups"], cmp["groups"] if cmp else None,
                                               spec, spec.rank_key())
    result["notes"] = [
        "Đơn khai nhiều loại nghỉ góp mặt ở MỌI nhóm loại nghỉ có dòng tương ứng (Ngày nghỉ đã "
        "duyệt/đang chờ theo từng loại), nhưng chỉ tính 1 đơn cho Số đơn/Số người nghỉ/Tỷ lệ từ "
        "chối-trả về/Thời gian duyệt TB — nhóm theo loại CHÍNH của đơn (dòng chiếm nhiều ngày nhất).",
        "Đơn vắt qua kỳ tính theo NGÀY BẮT ĐẦU; phòng ban/công ty lấy theo lúc LẬP đơn.",
    ]
    return result
