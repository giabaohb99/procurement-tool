"""API Đặt xe nội bộ — MVP lát dọc (tạo & theo dõi phiếu của người dùng).

Gác hai trục như mọi module: `require("vehicle_booking", action)` cho quyền hành động,
`apply_scope(...)` bó phạm vi theo công ty/phòng ban/người tạo. Lấy 1 phiếu theo id đi qua
`get_scoped` để không thể gõ id lên URL mà đọc phiếu ngoài phạm vi.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped

from . import service
from .model import VehicleBooking
from .schema import VehicleBookingCreate, VehicleBookingResponse, VehicleBookingUpdate

router = APIRouter(prefix="/api/vehicle-bookings", tags=["vehicle-booking"])


def _dump(obj: VehicleBooking) -> dict:
    return VehicleBookingResponse.model_validate(obj).model_dump()


@router.get("")
def list_bookings(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("vehicle_booking", "read")),
):
    """Danh sách phiếu trong phạm vi người xem ("Yêu cầu của tôi" khi phạm vi = own)."""
    query = db.query(VehicleBooking).filter(VehicleBooking.is_deleted == False)  # noqa: E712
    query = apply_filters(query, VehicleBooking, request, service.FILTERABLE)
    query = service.apply_keyword_search(query, request.query_params.get("search"))
    query = apply_scope(query, VehicleBooking, "vehicle_booking", user, get_perm_profile(db, user))
    query = apply_sort_from_request(query, VehicleBooking, request,
                                    default=VehicleBooking.id.desc())
    total = query.count()
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({
        "total": total,
        "items": [_dump(i) for i in items],
    })


@router.get("/{bid}")
def get_booking(bid: int, db: Session = Depends(get_db),
                user=Depends(require("vehicle_booking", "read"))):
    obj = get_scoped(db, VehicleBooking, "vehicle_booking", bid,
                     user, get_perm_profile(db, user))
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy yêu cầu đặt xe")
    return success(_dump(obj))


@router.post("")
def create_booking(
    data: VehicleBookingCreate,
    submit: bool = Query(False, description="true = gửi duyệt luôn; false = lưu nháp"),
    db: Session = Depends(get_db),
    user=Depends(require("vehicle_booking", "create")),
):
    obj = service.create_booking(db, data, user, submit)
    audit_record(db, user.id, "vehicle_booking", obj.id, "create",
                 f"Tạo yêu cầu đặt xe {obj.code}")
    msg = "Đã gửi duyệt yêu cầu đặt xe" if submit else "Đã lưu nháp yêu cầu đặt xe"
    return success(_dump(obj), msg, 201)


@router.patch("/{bid}")
def update_booking(
    bid: int,
    data: VehicleBookingUpdate,
    submit: bool = Query(False, description="true = lưu rồi gửi duyệt"),
    db: Session = Depends(get_db),
    user=Depends(require("vehicle_booking", "write")),
):
    obj = get_scoped(db, VehicleBooking, "vehicle_booking", bid,
                     user, get_perm_profile(db, user), "write")
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy yêu cầu đặt xe")
    obj = service.update_booking(db, obj, data, user, submit)
    audit_record(db, user.id, "vehicle_booking", obj.id, "update",
                 f"Cập nhật yêu cầu đặt xe {obj.code}")
    return success(_dump(obj), "Đã cập nhật")


@router.delete("/{bid}")
def delete_booking(bid: int, db: Session = Depends(get_db),
                   user=Depends(require("vehicle_booking", "delete"))):
    """Xóa mềm — giữ lại để không phá timeline/thống kê."""
    obj = get_scoped(db, VehicleBooking, "vehicle_booking", bid,
                     user, get_perm_profile(db, user), "delete")
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy yêu cầu đặt xe")
    obj.is_deleted = True
    obj.updated_by = user.id
    db.commit()
    audit_record(db, user.id, "vehicle_booking", obj.id, "delete",
                 f"Xóa yêu cầu đặt xe {obj.code}")
    return success(None, "Đã xóa")
