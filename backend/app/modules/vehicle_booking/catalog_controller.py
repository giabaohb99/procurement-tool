"""Danh mục Xe & Tài xế của phân hệ Đặt xe — CRUD đơn giản qua khung chung.

Cả hai là danh mục nền (entity `vehicle` / `driver`, khai PUBLIC ở scoping) nên dùng
`make_crud_router`: tự gác `require(entity, action)`, tự phân trang/sắp xếp/lọc, tự audit,
kèm xuất/nhập CSV. Không có migration — model đã đủ trường (xem model.py).
"""

from app.core.crud import make_crud_router

from .model import Driver, Vehicle
from .schema import (
    DriverCreate,
    DriverResponse,
    DriverUpdate,
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)

# Xe: khóa tự nhiên là BIỂN SỐ (unique) — chặn trùng khi tạo.
vehicle_router = make_crud_router(
    "/api/vehicles", "vehicle", Vehicle,
    VehicleCreate, VehicleUpdate, VehicleResponse,
    ["license_plate", "type", "status", "is_external"],
    unique_field="license_plate", code_prefix=None,
    csv_headers={
        "id": "ID", "license_plate": "Biển số", "model": "Mẫu xe",
        "type": "Loại xe", "capacity": "Tải (người/tấn)", "status": "Trạng thái",
    },
)

# Tài xế: không có cột duy nhất — tắt chặn trùng.
driver_router = make_crud_router(
    "/api/drivers", "driver", Driver,
    DriverCreate, DriverUpdate, DriverResponse,
    ["name", "phone", "status", "is_external"],
    unique_field=None, code_prefix=None,
    csv_headers={
        "id": "ID", "name": "Họ tên", "phone": "Điện thoại",
        "license_number": "Số GPLX", "status": "Trạng thái",
    },
)
