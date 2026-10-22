"""ai-CR-191 — sổ tham chiếu của hai danh mục Đặt xe: XE (`vehicle`) và TÀI XẾ (`driver`).

Chuyến xe ghi `assigned_vehicle_id` / `assigned_driver_id` khi điều phối (không FK). Còn chuyến nào trỏ
tới — kể cả đã hoàn tất / hủy / xóa mềm, vì báo cáo đặt xe còn đọc biển số, tên tài xế — thì không xóa.

⚠️ Hai bảng này CHƯA có cờ `is_active`, chỉ có `status` (available / on_trip / maintenance) — «ngưng
dùng» đúng nghĩa phải thêm cột ở đợt sau (ghi ở `doc/erp/nen-tang/20-ra-soat-xoa-cung.md` §4). Chặn xóa vẫn áp.
"""
from app.core.reference_guard import Reference, register

from .model import VehicleBooking

register("vehicle", "Xe", [
    Reference(VehicleBooking, "assigned_vehicle_id", "chuyến xe"),
])

register("driver", "Tài xế", [
    Reference(VehicleBooking, "assigned_driver_id", "chuyến xe"),
])
