"""Báo cáo Nghỉ phép — tình hình nghỉ (phase 04, `GET /api/leave-requests/summary`).

Gói B (review hiệu năng 01/10/2026): CỘNG chuyển hẳn vào SQL — xem docstring đầu
`report_sql_metrics.py` để biết VÌ SAO khung Python `report_aggregate.build_report()` không
đủ nhanh cho `group_by=employee` ở quy mô nhiều năm (14-23s đo được ở 60 nghìn đơn/3 năm, 79%
là vòng lặp Python). `build_summary()` dưới đây KHÔNG còn gọi `build_report()`/`aggregate()` —
tự dựng `totals`/`trend`/`groups`/`breakdowns` bằng 3 tệp `report_sql_*.py`, rồi tái dùng các
hàm GHÉP KỲ SO SÁNH của `report_compute.py` (`merge_trend_by_index`/`merge_groups_by_key`/
`compare_shift`) — những hàm đó chỉ cần dữ liệu đúng khuôn `{"key","label","values"}`, không
biết/không cần biết hàng gốc đi qua SQL hay Python trước đó.

`report_spec.build_spec()` GIỮ NGUYÊN hình dạng bản cũ — nay CHỈ còn phục vụ `meta_of()` (nhãn/kind/
helper cho FE) và validate `group_by` qua `spec.dimensions`. Các lambda `key_of`/`value_of`/
`distinct_of` bên trong KHÔNG còn được gọi (không còn hàng `LeaveRow` nào được nạp) — giữ lại
vì vẫn là tài liệu ĐÚNG của ý nghĩa từng chỉ số, và tách riêng `MetricSpec`/`DimensionSpec`
thành khuôn mới là việc không cần thiết (YAGNI) khi hai dataclass đó vẫn đúng khuôn cho
`meta_of()`. Công thức 2 chỉ số dẫn xuất (`reject_return_rate`/`avg_turnaround_hours`) nay
sống Ở MỘT CHỖ DUY NHẤT — `report_sql_metrics.DERIVED` — tái dùng lại đây, tránh hai công thức
lệch nhau.

duoc-CR-686 — CHIA NGÀY THEO KỲ: `days_approved`/`days_pending`/`days_unpaid` chỉ tính phần ngày
rơi vào kỳ / mốc (`report_day_split.py`); đơn vắt biên tính lại bằng Python rồi cộng CHÊNH LỆCH
vào số SQL (`report_day_split_apply.py`) — đơn gọn trong một mốc giữ đường SQL. Thêm lọc phòng
ban (`department_id`) và `meta.drilldown_metrics`; danh sách đơn ở `report_drill_rows.py`.

Phạm vi: `apply_scope(entity="leave_request")` — bậc `own` đã HỢP sẵn người LẬP
(`created_by`) và người NGHỈ (`employee_id`, xem `scoping._role_scope_cond` nhánh `own`),
KHÔNG nới thêm "đang có việc duyệt" (ngoại lệ đó chỉ dành cho đọc MỘT đơn lẻ —
`approval_bridge.can_read_request`).
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_compute import (compare_shift, compute_derived, merge_groups_by_key,
                                     merge_trend_by_index, meta_of)
from app.core.report_period import Period, bucket_axis, bucket_of
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.report_day_split import load_crossing_requests
from app.modules.leave.report_day_split_apply import (apply_to_groups, apply_to_totals,
                                                      leave_type_approved_deltas)
from app.modules.leave.report_rows import header_subquery, scoped_base, scoped_requests
from app.modules.leave.report_spec import (DRILLDOWN_METRICS, build_spec, label_lookups,
                                              load_type_info)
from app.modules.leave.report_sql_groups import (breakdown_by_status, breakdown_leave_type_by_days,
                                                 cap_groups, groups_for_dim)
from app.modules.leave.report_sql_metrics import DERIVED, header_aggregate, line_aggregate, totals_dict
from app.modules.leave.report_sql_trend import trend_for_period

NOTES = [
    "Đơn khai nhiều loại nghỉ góp mặt ở MỌI nhóm loại nghỉ có dòng tương ứng (Ngày nghỉ đã "
    "duyệt/đang chờ theo từng loại), nhưng chỉ tính 1 đơn cho Số đơn/Số người nghỉ/Tỷ lệ từ "
    "chối-trả về/Thời gian duyệt TB — nhóm theo loại CHÍNH của đơn (dòng chiếm nhiều ngày nhất).",
    "Ngày nghỉ (đã duyệt / chờ duyệt / không lương) chỉ tính phần ngày RƠI VÀO kỳ hoặc mốc xu "
    "hướng đang xem: đơn bắt đầu trước kỳ vẫn góp phần trong kỳ, đơn kéo qua cuối kỳ chỉ góp "
    "phần trong kỳ. Mỗi ngày nặng theo lịch làm việc của người nghỉ (trừ ngày lễ, nửa buổi tính "
    "0,5); đơn nhiều loại nghỉ chia theo tỷ lệ số ngày từng dòng.",
    "Số ĐƠN, số người nghỉ, tỷ lệ từ chối/trả về và thời gian duyệt vẫn tính theo NGÀY BẮT ĐẦU "
    "của đơn; phòng ban/công ty lấy theo lúc LẬP đơn. 'Ngày nghỉ TB/người' = ngày đã duyệt trong "
    "kỳ ÷ số người có đơn bắt đầu trong kỳ nên chỉ là số ước lượng khi có đơn vắt qua kỳ.",
]


def _totals_for_period(db: Session, scoped, header_subq) -> dict:
    values = totals_dict(header_aggregate(db, scoped, group_col=None),
                         line_aggregate(db, header_subq, group_col=None))
    values.update(compute_derived(values, DERIVED))
    return values


def build_summary(db: Session, user, prof: dict, period: Period, group_by: str | None,
                  company_id: int | None = None, department_id: int | None = None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/leave-requests/summary` (+ `/export`)."""
    spec = build_spec()
    if group_by and group_by != "none" and group_by not in spec.dimensions:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")

    type_name, unpaid_types, calendar_types = load_type_info(db)
    emp_name = ({e.id: e.full_name for e in db.query(Employee.id, Employee.full_name).all()}
               if group_by == "employee" else {})
    company_name = ({c.id: c.name for c in db.query(Company.id, Company.name).all()}
                    if group_by == "company" else {})
    department_name = ({d.id: d.name for d in db.query(Department.id, Department.name).all()}
                       if group_by == "department" else {})
    label_of = label_lookups(group_by, type_name, emp_name, company_name, department_name)
    gran = period.granularity

    def _fetch(d_from, d_to, need_breakdowns: bool, shift=None):
        scoped = scoped_requests(db, user, prof, d_from, d_to, company_id, department_id)
        header_subq = header_subquery(scoped)
        #  Đơn vắt biên kỳ/mốc: chia lại ngày (khóa mốc theo cùng luật dời của trục xu hướng).
        crossing = load_crossing_requests(
            db, scoped_base(db, user, prof, company_id, department_id), d_from, d_to,
            lambda d: bucket_of(shift(d) if shift else d, gran), calendar_types)
        groups = None
        if group_by and group_by != "none":
            groups = groups_for_dim(db, scoped, header_subq, group_by, label_of[group_by])
            #  Trần GROUP_LIMIT — gói A3 (01/10/2026) thêm cho `report_aggregate.aggregate()`;
            #  đường SQL này bỏ qua hàm đó nên phải tự cắt lại, xem docstring `cap_groups`.
            groups = cap_groups(db, scoped, header_subq, group_by, groups, spec.rank_key())
            groups = apply_to_groups(groups, crossing, group_by, d_from, d_to, unpaid_types,
                                     label_of[group_by], DERIVED)
        breakdowns = ({"status": breakdown_by_status(db, scoped, label_of["status"]),
                      "leave_type": breakdown_leave_type_by_days(
                          db, header_subq, type_name,
                          leave_type_approved_deltas(crossing, d_from, d_to))}
                     if need_breakdowns else {})
        totals = _totals_for_period(db, scoped, header_subq)
        apply_to_totals(totals, crossing, d_from, d_to, unpaid_types, DERIVED)
        return {"totals": totals, "groups": groups, "breakdowns": breakdowns, "scoped": scoped,
                "header_subq": header_subq, "split": (crossing, d_from, d_to, unpaid_types)}

    axis = bucket_axis(period.date_from, period.date_to, gran)
    cur = _fetch(period.date_from, period.date_to, need_breakdowns=True)
    cur_trend = trend_for_period(db, cur["scoped"], cur["header_subq"], axis, gran,
                                 split=cur["split"])

    cmp = None
    cmp_trend = None
    if period.compare != "none" and period.compare_from and period.compare_to:
        shift = compare_shift(period)
        cmp = _fetch(period.compare_from, period.compare_to, need_breakdowns=False, shift=shift)
        cmp_trend = trend_for_period(db, cmp["scoped"], cmp["header_subq"], axis, gran,
                                     shift=shift, split=cmp["split"])

    meta = meta_of(spec, group_by)
    meta["drilldown_metrics"] = list(DRILLDOWN_METRICS)
    result = {"period": period.as_dict(), "meta": meta,
             "totals": {"current": cur["totals"], "compare": cmp["totals"] if cmp else None},
             "trend": merge_trend_by_index(cur_trend, cmp_trend),
             "breakdowns": cur["breakdowns"], "notes": list(NOTES)}
    if cur["groups"] is not None:
        result["groups"] = merge_groups_by_key(cur["groups"], cmp["groups"] if cmp else None,
                                               spec, spec.rank_key())
    return result
