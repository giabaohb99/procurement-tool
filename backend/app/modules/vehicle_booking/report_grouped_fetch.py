"""GOM Ở SQL cho `/api/vehicle-bookings/summary` (+ `/summary/export`) — review hiệu năng
01/10/2026, thay bản per-row cũ (nạp MỖI PHIẾU một hàng rồi tra `turnaround_hours()` chia lô
900 id — 105 lượt hỏi ở mốc 3 năm/50k phiếu, xem
`fullstack-developer-261001-1103-load-test-8-bao-cao-moi.md` §2).

Bản này GROUP BY (ngày đi, trạng thái, loại yêu cầu[, ĐÚNG MỘT chiều group_by đang dùng]) ngay
ở SQL — cùng khuôn "chỉ tra nhãn của chiều ĐANG dùng" của bản cũ, chỉ khác là bây giờ chính
CHIỀU GOM cũng chỉ thêm vào GROUP BY khi cần, chứ không chỉ riêng việc tra nhãn. Giờ duyệt
(`turnaround_hours_subquery`) JOIN một lượt — không chunk.

Một "hàng" đầu ra không còn là MỘT PHIẾU mà là MỘT NHÓM phiếu cùng khóa, mang theo `cnt` (số
phiếu thật trong nhóm) — `report_service.build_spec()` đọc `r["cnt"]` làm trọng số thay vì
ngầm định 1 cho mỗi hàng (cùng ý tưởng "cnt" của `survey/report_grouped_fetch.py`).

`distance_km` làm tròn TỪNG PHIẾU rồi mới cộng (`SUM(ROUND(distance_km,0))`, KHÔNG phải
`ROUND(SUM(distance_km),0)`) — giữ đúng quyết định "làm tròn trước khi cộng" của bản cũ. ⚠️
SQLite/MySQL `ROUND()` làm tròn NỬA RA XA 0, Python `round()` làm tròn NỬA VỀ CHẴN — hai bên
CHỈ lệch khi `distance_km` đúng bằng số nguyên + 0.5 (vd `42.5`), biên gần như không xảy ra
với số liệu GPS/công-tơ-mét thực tế (kiểm tay 01/10/2026) — chấp nhận, không xử lý thêm
(YAGNI cho một biên gần như không chạm tới trên dữ liệu thật).
"""
from __future__ import annotations

from sqlalchemy import case, func
from sqlalchemy.orm import Query

from .model import VehicleBooking
from .report_turnaround_sql import turnaround_hours_subquery

#  Chiều group_by nào cần MỘT cột id riêng trong GROUP BY — `status`/`request_type` đã có sẵn
#  trong khóa gốc (phục vụ breakdowns, luôn gom bất kể `group_by`) nên không liệt ở đây.
#  `requester` không cần tra bảng khác (tên đã chụp sẵn trên chính dòng Đặt xe) nên kèm cột
#  nhãn để lấy qua `MAX()` ngay trong câu gom, không cần hỏi thêm; bốn chiều còn lại nhãn nằm
#  ở bảng khác (Công ty/Phòng ban/Xe/Tài xế) nên chỉ cần ĐÚNG id, nhãn tra sau ở `decorate()`.
GROUPABLE_DIMS: dict[str, tuple] = {
    "company": (VehicleBooking.company_id, None),
    "department": (VehicleBooking.department_id, None),
    "vehicle": (VehicleBooking.assigned_vehicle_id, None),
    "driver": (VehicleBooking.assigned_driver_id, None),
    "requester": (VehicleBooking.requester_id, VehicleBooking.requester),
}


def fetch_grouped_rows(db, scoped_query: Query, group_by: str | None) -> list:
    """`scoped_query` = `db.query(VehicleBooking)` ĐÃ qua `apply_scope` + mọi `filter()` (kỳ
    theo `start_time`, `is_deleted=False`, bỏ `BK_DRAFT`, lọc công ty nếu có) — y hệt điều
    kiện của bản per-row cũ, chỉ khác bước cuối là GROUP BY thay vì `with_entities(...).all()`.

    Trả `Row` với cột `date·status·request_type·[extra_id·[extra_label]]·cnt·sum_distance·
    sum_cost·sum_passengers·sum_hours·hours_count` — MỘT dòng mỗi NHÓM, không phải mỗi phiếu.
    """
    turn = turnaround_hours_subquery(db, "vehicle_booking")
    #  `start_time` là chuỗi ISO giờ VN (Q5.1) — cắt 10 ký tự đầu PORTABLE trên cả hai dialect,
    #  khớp CHÍNH XÁC `to_local_date(str)` (`s[:10]`) của bản Python cũ.
    day_expr = func.substr(VehicleBooking.start_time, 1, 10).label("date")
    select_cols = [day_expr, VehicleBooking.status.label("status"),
                  VehicleBooking.request_type.label("request_type")]
    group_cols = [day_expr, VehicleBooking.status, VehicleBooking.request_type]

    dim = GROUPABLE_DIMS.get(group_by or "")
    if dim is not None:
        id_col, label_col = dim
        select_cols.append(id_col.label("extra_id"))
        group_cols.append(id_col)
        if label_col is not None:
            select_cols.append(func.max(label_col).label("extra_label"))

    q = (scoped_query
         .outerjoin(turn, VehicleBooking.id == turn.c.booking_id)
         .with_entities(
             *select_cols,
             func.count(VehicleBooking.id).label("cnt"),
             func.sum(func.round(func.coalesce(VehicleBooking.distance_km, 0), 0))
                 .label("sum_distance"),
             func.sum(func.coalesce(VehicleBooking.cost, 0)).label("sum_cost"),
             func.sum(func.coalesce(VehicleBooking.passenger_count, 0)).label("sum_passengers"),
             func.sum(func.coalesce(turn.c.hours, 0.0)).label("sum_hours"),
             func.sum(case((turn.c.hours.isnot(None), 1), else_=0)).label("hours_count"))
         .group_by(*group_cols))
    return q.all()
