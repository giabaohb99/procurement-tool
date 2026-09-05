"""API Đặt xe nội bộ — MVP lát dọc (tạo & theo dõi phiếu của người dùng).

Gác hai trục như mọi module: `require("vehicle_booking", action)` cho quyền hành động,
`apply_scope(...)` bó phạm vi theo công ty/phòng ban/người tạo. Lấy 1 phiếu theo id đi qua
`get_scoped` để không thể gõ id lên URL mà đọc phiếu ngoài phạm vi.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped

from . import approval_bridge, service
from .model import Driver, Vehicle, VehicleBooking
from .schema import (
    CompleteIn,
    DispatchIn,
    ReasonIn,
    VehicleBookingCreate,
    VehicleBookingUpdate,
)

router = APIRouter(prefix="/api/vehicle-bookings", tags=["vehicle-booking"])


def _with_reason(action: str, reason: str) -> str:
    """Ghép hành động + lý do cho nhật ký, vd 'Từ chối chuyến đi — Lý do: Trùng lịch'."""
    reason = (reason or "").strip()
    return f"{action} — Lý do: {reason}" if reason else action


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
    #  Màn "Chuyến của tôi" (tài xế): chỉ chuyến ĐƯỢC PHÂN cho chính người xem.
    if request.query_params.get("mine"):
        query = service.filter_my_trips(query, db, user)
    query = apply_sort_from_request(query, VehicleBooking, request,
                                    default=VehicleBooking.id.desc())
    total = query.count()
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({
        "total": total,
        "items": service.serialize_bookings(db, items),
    })


@router.get("/{bid}")
def get_booking(bid: int, db: Session = Depends(get_db),
                user=Depends(require("vehicle_booking", "read"))):
    obj = get_scoped(db, VehicleBooking, "vehicle_booking", bid,
                     user, get_perm_profile(db, user))
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy yêu cầu đặt xe")
    return success(service.serialize_booking(db, obj, viewer=user))


@router.post("")
def create_booking(
    data: VehicleBookingCreate,
    background_tasks: BackgroundTasks,
    submit: bool = Query(False, description="true = gửi duyệt luôn; false = lưu nháp"),
    db: Session = Depends(get_db),
    user=Depends(require("vehicle_booking", "create")),
):
    obj = service.create_booking(db, data, user, submit, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "create",
                 f"Tạo yêu cầu đặt xe {obj.code}")
    msg = "Đã gửi duyệt yêu cầu đặt xe" if submit else "Đã lưu nháp yêu cầu đặt xe"
    return success(service.serialize_booking(db, obj), msg, 201)


@router.patch("/{bid}")
def update_booking(
    bid: int,
    data: VehicleBookingUpdate,
    background_tasks: BackgroundTasks,
    submit: bool = Query(False, description="true = lưu rồi gửi duyệt"),
    db: Session = Depends(get_db),
    user=Depends(require("vehicle_booking", "write")),
):
    obj = get_scoped(db, VehicleBooking, "vehicle_booking", bid,
                     user, get_perm_profile(db, user), "write")
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy yêu cầu đặt xe")
    obj = service.update_booking(db, obj, data, user, submit, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "update",
                 f"Cập nhật yêu cầu đặt xe {obj.code}")
    return success(service.serialize_booking(db, obj), "Đã cập nhật")


@router.post("/{bid}/dispatch")
def dispatch_booking(
    bid: int,
    data: DispatchIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(require("vehicle_booking", "write")),
):
    """Điều phối: gán xe + tài xế cho phiếu (điều phối viên = quyền write)."""
    obj = get_scoped(db, VehicleBooking, "vehicle_booking", bid,
                     user, get_perm_profile(db, user), "write")
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy yêu cầu đặt xe")
    obj = service.dispatch_booking(db, obj, data, user, background_tasks)
    veh = db.get(Vehicle, obj.assigned_vehicle_id) if obj.assigned_vehicle_id else None
    drv = db.get(Driver, obj.assigned_driver_id) if obj.assigned_driver_id else None
    audit_record(db, user.id, "vehicle_booking", obj.id, "update",
                 f"Đã điều phối Xe {veh.license_plate if veh else '?'} "
                 f"và Tài xế {drv.name if drv else '?'}")
    return success(service.serialize_booking(db, obj, viewer=user), "Đã điều phối")


# --- Chuyển trạng thái theo vai trò ----------------------------------------
#  Người duyệt (quyền `approve`): duyệt / yêu cầu chỉnh sửa / từ chối.
#  Tài xế được phân (quyền `write`): chấp nhận / từ chối / bắt đầu / hoàn tất.

def _scoped_or_404(db: Session, bid: int, user, action: str) -> VehicleBooking:
    obj = get_scoped(db, VehicleBooking, "vehicle_booking", bid,
                     user, get_perm_profile(db, user), action)
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy yêu cầu đặt xe")
    return obj


@router.post("/{bid}/approve")
def approve_booking(bid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                    user=Depends(require("vehicle_booking", "approve"))):
    """Người duyệt CHẤP NHẬN phiếu (Chờ duyệt → Đã duyệt)."""
    obj = _scoped_or_404(db, bid, user, "approve")
    approval_bridge.block_legacy_path(db, obj)  # đang chạy luồng nhiều bước thì chặn đường tắt
    obj = service.approve_booking(db, obj, user, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "approve",
                 f"Duyệt yêu cầu đặt xe {obj.code}")
    return success(service.serialize_booking(db, obj, viewer=user), "Đã duyệt yêu cầu")


@router.post("/{bid}/return")
def return_booking(bid: int, data: ReasonIn, background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db),
                   user=Depends(require("vehicle_booking", "approve"))):
    """Người duyệt YÊU CẦU CHỈNH SỬA (Chờ duyệt → Yêu cầu chỉnh sửa)."""
    obj = _scoped_or_404(db, bid, user, "approve")
    approval_bridge.block_legacy_path(db, obj)
    obj = service.return_booking(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "update",
                 _with_reason("Yêu cầu chỉnh sửa", data.reason))
    return success(service.serialize_booking(db, obj, viewer=user), "Đã trả lại để chỉnh sửa")


@router.post("/{bid}/reject")
def reject_booking(bid: int, data: ReasonIn, background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db),
                   user=Depends(require("vehicle_booking", "approve"))):
    """Người duyệt TỪ CHỐI (Chờ duyệt → Từ chối)."""
    obj = _scoped_or_404(db, bid, user, "approve")
    approval_bridge.block_legacy_path(db, obj)
    obj = service.reject_booking(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "cancel",
                 _with_reason("Từ chối yêu cầu", data.reason))
    return success(service.serialize_booking(db, obj, viewer=user), "Đã từ chối yêu cầu")


@router.post("/{bid}/driver/accept")
def driver_accept(bid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                  user=Depends(require("vehicle_booking", "write"))):
    """Tài xế CHẤP NHẬN chuyến (Chờ tài xế → Đã nhận)."""
    obj = _scoped_or_404(db, bid, user, "write")
    obj = service.driver_accept(db, obj, user, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "update", "Chấp nhận chuyến")
    return success(service.serialize_booking(db, obj, viewer=user), "Đã nhận chuyến")


@router.post("/{bid}/driver/reject")
def driver_reject(bid: int, data: ReasonIn, background_tasks: BackgroundTasks,
                  db: Session = Depends(get_db),
                  user=Depends(require("vehicle_booking", "write"))):
    """Tài xế TỪ CHỐI chuyến → quay về điều phối phân lại."""
    obj = _scoped_or_404(db, bid, user, "write")
    obj = service.driver_reject(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "update",
                 _with_reason("Từ chối chuyến đi", data.reason))
    return success(service.serialize_booking(db, obj, viewer=user), "Đã từ chối chuyến — chờ điều phối lại")


@router.post("/{bid}/driver/start")
def driver_start(bid: int, db: Session = Depends(get_db),
                 user=Depends(require("vehicle_booking", "write"))):
    """Tài xế BẮT ĐẦU chuyến (Đã nhận → Đang đi)."""
    obj = _scoped_or_404(db, bid, user, "write")
    obj = service.driver_start(db, obj, user)
    audit_record(db, user.id, "vehicle_booking", obj.id, "update",
                 f"Bắt đầu chuyến {obj.code}")
    return success(service.serialize_booking(db, obj, viewer=user), "Đã bắt đầu chuyến")


@router.post("/{bid}/driver/complete")
def driver_complete(bid: int, data: CompleteIn, background_tasks: BackgroundTasks,
                    db: Session = Depends(get_db),
                    user=Depends(require("vehicle_booking", "write"))):
    """Tài xế HOÀN TẤT chuyến (Đang đi → Hoàn thành)."""
    obj = _scoped_or_404(db, bid, user, "write")
    obj = service.driver_complete(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "update",
                 f"Hoàn tất chuyến {obj.code}")
    return success(service.serialize_booking(db, obj, viewer=user), "Đã hoàn tất chuyến")


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
