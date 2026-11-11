"""Đặt xe — biểu thức SQL xếp các cột danh sách KHÔNG xếp thẳng theo cột lưu (duoc-CR-744 lượt d).

- `route` ("Lộ trình"): bảng hiện "điểm đi → điểm dừng → điểm đến" -> xếp theo điểm đi rồi điểm đến.
- `assigned` ("Xe / Tài xế"): bảng hiện biển số xe trước, không có xe thì tên tài xế, tự lái thì
  tên người tạo (`service.booking_out`) -> xếp theo đúng chữ đứng đầu ô đó.
"""
from sqlalchemy import case, func, select

from .model import Driver, Vehicle, VehicleBooking


def list_sort_allow() -> dict:
    plate = (select(Vehicle.license_plate).where(Vehicle.id == VehicleBooking.assigned_vehicle_id)
             .correlate(VehicleBooking).scalar_subquery())
    driver = (select(Driver.name).where(Driver.id == VehicleBooking.assigned_driver_id)
              .correlate(VehicleBooking).scalar_subquery())
    self_drive = case((VehicleBooking.is_self_drive == True, VehicleBooking.requester))  # noqa: E712
    route = (func.coalesce(VehicleBooking.start_location, "") + " "
             + func.coalesce(VehicleBooking.end_location, ""))
    return {
        "route": route,
        "assigned": func.coalesce(func.nullif(plate, ""), func.nullif(driver, ""), func.nullif(self_drive, "")),
    }
