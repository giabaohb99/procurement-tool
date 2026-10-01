"""Bản THEO KỲ của Báo cáo Đặt xe (phase 05, 5.1) — `GET /api/vehicle-bookings/summary`.

Kỳ tính theo NGÀY ĐI (`start_time`, chuỗi ISO — Q5.1), không phải ngày tạo phiếu.

Review hiệu năng 01/10/2026 (thay bản per-row 01/10/2026 trước đó — load test đo 6.5-7.5s,
105 lượt hỏi IN(...) chia lô của `turnaround_hours()` chiếm 70% thời gian, xem
`fullstack-developer-261001-1103-load-test-8-bao-cao-moi.md` §2 mục vehicle-bookings):

- `report_grouped_fetch.fetch_grouped_rows()` GOM Ở SQL — GROUP BY (ngày, trạng thái, loại
  yêu cầu[, chiều group_by đang dùng]) + SUM/COUNT (km, chi phí, hành khách, giờ duyệt) ngay
  trong câu lệnh, JOIN `turnaround_hours_subquery` MỘT LƯỢT thay vì chunk 900 id/lượt. Một
  "hàng" ở tầng `build_spec()` giờ là MỘT NHÓM phiếu, không phải một phiếu — `MetricSpec`
  đọc trọng số `r["cnt"]` thay vì ngầm định 1 (cùng ý tưởng `survey/report_grouped_fetch.py`).
- `decorate()` CHỈ tra nhãn công ty/phòng ban/xe/tài xế khi `group_by` ĐANG DÙNG đúng chiều đó
  (giữ nguyên từ bản cũ) — khác biệt duy nhất là giờ tra trên DANH SÁCH NHÓM (ít hơn nhiều so
  với danh sách phiếu), không đổi về SỐ LƯỢT HỎI so với bản trước (vẫn O(số giá trị khác nhau),
  không O(số phiếu)).
- Số truy vấn CỐ ĐỊNH theo số CHIỀU GIÁ TRỊ KHÁC NHAU xuất hiện (1 câu GOM + tối đa 1 câu tra
  nhãn), không theo số DÒNG — test đếm truy vấn ở `test_bao_cao_hanh_chinh.py`.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec
from app.core.report_period import to_local_date
from app.modules.company.model import Company
from app.modules.department.model import Department

from .model import (BK_CANCELLED, BK_COMPLETED, BK_REJECTED, BOOKING_STATUS_LABELS,
                    REQUEST_TYPE_LABELS, Driver, Vehicle)
from .report_grouped_fetch import GROUPABLE_DIMS

#  Hai mốc "xấu" của chuỗi trạng thái — góp vào tử số của "Tỷ lệ từ chối + hủy".
_BAD_STATUSES = (BK_REJECTED, BK_CANCELLED)


def _id_name_map(db: Session, id_col, name_col, ids: set[int]) -> dict[int, str]:
    """`{id: tên}` tra MỘT lượt cho cả lô — rỗng thì KHÔNG hỏi gì (tránh `IN ()` vô nghĩa)."""
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return dict(db.query(id_col, name_col).filter(id_col.in_(ids)).all())


def decorate(db: Session, rows: list, group_by: str | None = None) -> list[dict]:
    """Ghép nhãn công ty/phòng ban/xe/tài xế cho các NHÓM đã gộp sẵn ở SQL
    (`report_grouped_fetch.fetch_grouped_rows`) — `rows` giờ là `Row` của câu `GROUP BY`,
    KHÔNG phải một phiếu mỗi dòng. Chỉ tra nhãn của ĐÚNG chiều `group_by` đang dùng (xem
    docstring đầu tệp); các chiều khác giữ nhãn rỗng vì `key_of` của chúng không được gọi tới.
    """
    extra_ids = ({r.extra_id for r in rows if getattr(r, "extra_id", None)}
                if group_by in GROUPABLE_DIMS else set())
    companies = (_id_name_map(db, Company.id, Company.name, extra_ids)
                if group_by == "company" else {})
    depts = (_id_name_map(db, Department.id, Department.name, extra_ids)
            if group_by == "department" else {})
    vehicles = {}
    if group_by == "vehicle" and extra_ids:
        vehicles = {v.id: (f"{v.license_plate} — {v.model}" if v.model else v.license_plate)
                   for v in db.query(Vehicle).filter(Vehicle.id.in_(extra_ids)).all()}
    drivers = (_id_name_map(db, Driver.id, Driver.name, extra_ids) if group_by == "driver" else {})

    out = []
    for r in rows:
        eid = getattr(r, "extra_id", None) or 0
        out.append({
            "date": r.date, "status": r.status, "request_type": r.request_type,
            "company_id": eid if group_by == "company" else 0,
            "company_name": companies.get(eid, "") if group_by == "company" else "",
            "department_id": eid if group_by == "department" else 0,
            "department_name": depts.get(eid, "") if group_by == "department" else "",
            "vehicle_id": eid if group_by == "vehicle" else 0,
            "vehicle_label": vehicles.get(eid, "") if group_by == "vehicle" else "",
            "driver_id": eid if group_by == "driver" else 0,
            "driver_label": drivers.get(eid, "") if group_by == "driver" else "",
            "requester_id": eid if group_by == "requester" else 0,
            "requester": (getattr(r, "extra_label", "") or "") if group_by == "requester" else "",
            "cnt": r.cnt,
            "sum_distance_km": r.sum_distance or 0,
            "sum_cost": r.sum_cost or 0,
            "sum_passengers": r.sum_passengers or 0,
            "sum_approval_hours": r.sum_hours or 0,
            "hours_count": r.hours_count or 0,
        })
    return out


def build_spec() -> ReportSpec:
    metrics = [
        MetricSpec("requests", "Yêu cầu", kind="int", value_of=lambda r: r["cnt"]),
        MetricSpec("completed", "Chuyến hoàn thành", kind="int",
                  value_of=lambda r: r["cnt"] if r["status"] == BK_COMPLETED else 0),
        #  Chỉ số PHỤ — chỉ làm tử số của `reject_cancel_rate`, không đứng riêng.
        MetricSpec("rejected_cancelled", "Từ chối + hủy", kind="int", helper=True,
                  value_of=lambda r: r["cnt"] if r["status"] in _BAD_STATUSES else 0),
        #  Đã làm tròn TỪNG PHIẾU rồi cộng ngay ở SQL (`report_grouped_fetch`) — giữ đúng
        #  quyết định cũ "int hiểu ngầm là số nguyên", chỉ dời chỗ tính xuống SQL.
        MetricSpec("distance_km", "Tổng km", kind="int", value_of=lambda r: r["sum_distance_km"]),
        MetricSpec("cost", "Chi phí", kind="money", value_of=lambda r: r["sum_cost"]),
        MetricSpec("passengers", "Hành khách", kind="int", value_of=lambda r: r["sum_passengers"]),
        MetricSpec("approval_hours_sum", "Tổng giờ duyệt", kind="hours", helper=True,
                  value_of=lambda r: r["sum_approval_hours"]),
        MetricSpec("approval_hours_count", "Số phiếu có giờ duyệt", kind="int", helper=True,
                  value_of=lambda r: r["hours_count"]),
    ]
    derived = [
        DerivedSpec("reject_cancel_rate", "Tỷ lệ từ chối + hủy", num="rejected_cancelled",
                   den="requests", kind="percent", good="down"),
        #  `scale=1`: TRUNG BÌNH giờ, không phải tỷ lệ % — mặc định ×100 sẽ sai 100 lần.
        DerivedSpec("avg_approval_hours", "Thời gian duyệt TB", num="approval_hours_sum",
                   den="approval_hours_count", kind="hours", good="down", scale=1),
    ]
    dimensions = {
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r["company_id"], r["company_name"])] if r["company_id"] else [])),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r["department_id"], r["department_name"])] if r["department_id"] else [])),
        "request_type": DimensionSpec("request_type", "Loại yêu cầu", key_of=lambda r: (
            [(r["request_type"], REQUEST_TYPE_LABELS.get(r["request_type"], ""))])),
        "status": DimensionSpec("status", "Trạng thái", key_of=lambda r: (
            [(r["status"], BOOKING_STATUS_LABELS.get(r["status"], ""))])),
        "vehicle": DimensionSpec("vehicle", "Xe", key_of=lambda r: (
            [(r["vehicle_id"], r["vehicle_label"])] if r["vehicle_id"] else [])),
        "driver": DimensionSpec("driver", "Tài xế", key_of=lambda r: (
            [(r["driver_id"], r["driver_label"])] if r["driver_id"] else [])),
        "requester": DimensionSpec("requester", "Người yêu cầu", key_of=lambda r: (
            [(r["requester_id"], r["requester"])] if r["requester_id"] else [])),
    }
    breakdowns = {"status": dimensions["status"], "request_type": dimensions["request_type"]}
    return ReportSpec(date_of=lambda r: to_local_date(r["date"]), metrics=metrics,
                      derived=derived, dimensions=dimensions, breakdowns=breakdowns)
