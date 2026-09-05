"""Danh mục Xe & Tài xế của phân hệ Đặt xe — CRUD đơn giản qua khung chung.

Cả hai là danh mục nền (entity `vehicle` / `driver`, khai PUBLIC ở scoping) nên dùng
`make_crud_router`: tự gác `require(entity, action)`, tự phân trang/sắp xếp/lọc, tự audit,
kèm xuất/nhập CSV. Không có migration — model đã đủ trường (xem model.py).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.crud import make_crud_router
from app.core.database import get_db
from app.core.response import success

from . import service
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


# Ô chọn tài xế khi ĐIỀU PHỐI — lọc theo vai trò (chỉ người thật sự là tài xế).
# Gác `vehicle_booking.write` (quyền của điều phối viên), không phải `driver`.
dispatch_router = APIRouter(prefix="/api/dispatch", tags=["vehicle-booking"])


@dispatch_router.get("/drivers")
def dispatch_driver_options(db: Session = Depends(get_db),
                            user=Depends(require("vehicle_booking", "write"))):
    """Tài xế để đổ vào ô chọn khi điều phối (xem `service.drivers_for_dispatch`)."""
    rows = service.drivers_for_dispatch(db)
    return success({"items": rows, "total": len(rows)})


@dispatch_router.get("/my-driver")
def my_driver(db: Session = Depends(get_db),
              user=Depends(require("vehicle_booking", "read"))):
    """Hồ sơ tài xế của chính người đăng nhập — để form TỰ LÁI tự điền GPLX. `null` nếu chưa là tài xế."""
    return success(service.my_driver_profile(db, user))
