"""Khai báo `ReportSpec` (nhãn/kind/chiều) của báo cáo Tình hình nghỉ phép — tách khỏi
`report_service.py` (giữ < 200 dòng). Chỉ phục vụ `meta_of()` + validate `group_by`; giá trị
thật do `report_sql_*.py` tính, xem docstring `report_service.py`."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.report_aggregate import DimensionSpec, MetricSpec, ReportSpec
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LEAVE_REQUEST_STATUS_LABELS
from app.modules.leave.report_sql_metrics import DERIVED

#  Chỉ số bấm được ra danh sách đơn (`GET /api/leave-requests/summary/rows`).
DRILLDOWN_METRICS = {"requests": "Số đơn", "days_approved": "Ngày nghỉ đã duyệt",
                     "days_pending": "Ngày đang chờ duyệt",
                     "requests_pending_over_3d": "Đơn chờ duyệt quá 3 ngày"}


def build_spec() -> ReportSpec:
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
        MetricSpec("days_unpaid", "Ngày nghỉ không lương", kind="days", value_of=_unused),
        MetricSpec("requests_pending_over_3d", "Đơn chờ duyệt quá 3 ngày", kind="int", good="down",
                  distinct_of=_unused),
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


def label_lookups(group_by: str | None, type_name: dict, emp_name: dict, company_name: dict,
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


def load_type_info(db: Session) -> tuple[dict, set[int], set[int]]:
    """(tên loại nghỉ, loại KHÔNG lương, loại đếm ngày LỊCH) — 1 truy vấn, dùng cho cả nhãn lẫn
    chia ngày."""
    rows = db.query(LeaveType.id, LeaveType.name, LeaveType.is_paid, LeaveType.exclude_holiday).all()
    return ({t.id: t.name for t in rows}, {t.id for t in rows if t.is_paid is False},
            {t.id for t in rows if t.exclude_holiday is False})
