"""API Đặt xe nội bộ — MVP lát dọc (tạo & theo dõi phiếu của người dùng).

Gác hai trục như mọi module: `require("vehicle_booking", action)` cho quyền hành động,
`apply_scope(...)` bó phạm vi theo công ty/phòng ban/người tạo. Lấy 1 phiếu theo id đi qua
`get_scoped` để không thể gõ id lên URL mà đọc phiếu ngoài phạm vi.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.base_controller import (
    apply_datetime_range,
    apply_filters,
    apply_sort_from_request,
    pagination,
)
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


#  Nhãn tiếng Việt của các trường người dùng SỬA — để nhật ký ghi CỤ THỂ đã đổi gì
#  ("Chỉnh sửa: Thời gian giao (dự kiến), Điểm đến") thay vì "Cập nhật" chung chung.
_EDIT_LABELS = {
    "request_type": "Loại yêu cầu", "purpose": "Mục đích", "is_self_drive": "Hình thức tự lái",
    "license_number": "Số GPLX", "license_class": "Hạng GPLX",
    "start_location": "Điểm đi / lấy hàng", "end_location": "Điểm đến / giao hàng",
    "stops": "Điểm dừng", "start_time": "Thời gian đi / lấy hàng",
    "end_time": "Thời gian về / giao", "passenger_count": "Số hành khách",
    "attendees": "Người tham gia", "contact_phone": "SĐT liên hệ", "is_round_trip": "Khứ hồi",
    "goods_name": "Tên hàng hóa", "goods_size": "Kích thước / KL",
    "sender_name": "Người gửi", "sender_phone": "SĐT người gửi",
    "receiver_name": "Người nhận", "receiver_phone": "SĐT người nhận",
    "special_instructions": "Chỉ dẫn đặc biệt", "note": "Ghi chú",
}


def _snapshot(obj) -> dict:
    """Chụp giá trị các trường theo dõi trước khi sửa (so sánh dạng chuỗi cho gọn)."""
    return {k: str(getattr(obj, k, "")) for k in _EDIT_LABELS}


def _changed_labels(before: dict, obj) -> list[str]:
    """Danh sách NHÃN các trường đã đổi giá trị so với ảnh chụp trước khi sửa."""
    return [lbl for k, lbl in _EDIT_LABELS.items() if before.get(k) != str(getattr(obj, k, ""))]


def _booking_query(request: Request, db: Session, user):
    """Query danh sách phiếu theo ĐÚNG bộ lọc đang đặt (lọc + tìm + phạm vi + mine).

    Dùng CHUNG cho danh sách và Xuất Excel — xuất ra phải khớp cái đang xem."""
    query = db.query(VehicleBooking).filter(VehicleBooking.is_deleted == False)  # noqa: E712
    query = apply_filters(query, VehicleBooking, request, service.FILTERABLE)
    query = apply_datetime_range(query, VehicleBooking, request)  # bộ lọc "Ngày tạo"
    query = service.apply_keyword_search(query, request.query_params.get("search"))
    query = apply_scope(query, VehicleBooking, "vehicle_booking", user, get_perm_profile(db, user))
    #  Màn "Chuyến của tôi" (tài xế): chỉ chuyến ĐƯỢC PHÂN cho chính người xem.
    if request.query_params.get("mine"):
        query = service.filter_my_trips(query, db, user)
    return apply_sort_from_request(query, VehicleBooking, request,
                                   default=VehicleBooking.id.desc())


@router.get("")
def list_bookings(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("vehicle_booking", "read")),
):
    """Danh sách phiếu trong phạm vi người xem ("Yêu cầu của tôi" khi phạm vi = own)."""
    query = _booking_query(request, db, user)
    total = query.count()
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({
        "total": total,
        "items": service.serialize_bookings(db, items),
    })


@router.get("/export/xlsx")
def export_bookings_xlsx(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require("vehicle_booking", "read")),
):
    """Xuất Excel danh sách phiếu theo ĐÚNG bộ lọc đang hiển thị (danh sách + Chuyến của tôi).

    Khai TRƯỚC `/{bid}` để 'export' không bị bắt làm id phiếu."""
    from app.core.export_xlsx import Col, check_row_limit, xlsx_response

    objs = _booking_query(request, db, user).all()
    check_row_limit(len(objs))
    rows = service.serialize_bookings(db, objs)
    columns = [
        Col("code", "Mã phiếu", width=14),
        Col("request_type_label", "Loại", width=18),
        Col("status_label", "Trạng thái", width=16),
        Col("driver_status_label", "Trạng thái tài xế", width=18),
        Col("purpose", "Mục đích", width=30),
        Col("start_location", "Điểm đi", width=22),
        Col("end_location", "Điểm đến", width=22),
        Col("start_time", "Thời gian đi", width=18),
        Col("end_time", "Thời gian về", width=18),
        Col("requester", "Người tạo", width=18),
        Col("assigned_vehicle_label", "Xe", width=16),
        Col("assigned_driver_label", "Tài xế", width=16),
        Col("distance_km", "Số km", kind="qty", width=10),
        Col("cost", "Chi phí", kind="money", width=14),
    ]
    return xlsx_response("yeu-cau-dat-xe.xlsx", columns, rows, "Yêu cầu đặt xe")


@router.get("/overview")
def booking_overview(
    date_from: str = Query("", description="Lọc khối tổng hợp từ ngày tạo (yyyy-mm-dd)"),
    date_to: str = Query("", description="Lọc khối tổng hợp đến ngày tạo (yyyy-mm-dd)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Tổng quan Đặt xe theo vai trò — gác từng khối bằng quyền, lọc theo phạm vi.

    `date_from`/`date_to` lọc khối tổng hợp `company` (theo tháng/loại/trạng thái/bộ
    phận); mặc định 30 ngày do giao diện truyền, bỏ trống = tất cả.

    ⚠️ Phải khai TRƯỚC `/{bid}` để "overview" không bị bắt làm id phiếu.
    """
    from . import dashboard_service

    return success(dashboard_service.build_overview(db, user, date_from or None, date_to or None))


@router.get("/timeline")
def booking_timeline(
    date_from: str = Query("", description="Khoảng hiển thị của lịch (yyyy-mm-dd)"),
    date_to: str = Query("", description="Khoảng hiển thị của lịch (yyyy-mm-dd)"),
    db: Session = Depends(get_db),
    user=Depends(require("vehicle_booking", "read")),
):
    """Các chuyến xe theo DÒNG THỜI GIAN cho trang Timeline (lịch tháng).

    Trả các phiếu có ngày khởi hành nằm trong [date_from, date_to] (đã bó phạm vi
    theo người xem). ⚠️ Khai TRƯỚC `/{bid}` để "timeline" không bị bắt làm id phiếu.
    """
    items = service.timeline_events(db, user, date_from or None, date_to or None)
    return success({"items": items})


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
    #  Gửi duyệt = một dòng nhật ký riêng ("Ai — Gửi duyệt") để đọc rõ luồng.
    if submit:
        audit_record(db, user.id, "vehicle_booking", obj.id, "submitted", "Gửi duyệt yêu cầu")
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
    before = _snapshot(obj)
    obj = service.update_booking(db, obj, data, user, submit, background_tasks)
    #  Ghi CỤ THỂ đã sửa trường nào (vd "Chỉnh sửa: Thời gian giao (dự kiến), Điểm đến").
    #  KHÔNG đổi gì thì KHÔNG ghi lịch sử — tránh dòng "Cập nhật (không đổi nội dung)" vô nghĩa.
    changed = _changed_labels(before, obj)
    if changed:
        audit_record(db, user.id, "vehicle_booking", obj.id, "update",
                     f"Chỉnh sửa: {', '.join(changed)}")
    if submit:
        audit_record(db, user.id, "vehicle_booking", obj.id, "submitted", "Gửi duyệt yêu cầu")
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


@router.post("/{bid}/dispatch/return")
def dispatch_return_booking(bid: int, data: ReasonIn, background_tasks: BackgroundTasks,
                            db: Session = Depends(get_db),
                            user=Depends(require("vehicle_booking", "write"))):
    """Điều phối viên YÊU CẦU CHỈNH SỬA phiếu ĐANG Đã điều phối → trả về người tạo (gỡ điều phối)."""
    obj = _scoped_or_404(db, bid, user, "write")
    obj = service.return_booking(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "update",
                 _with_reason("Yêu cầu chỉnh sửa (điều phối)", data.reason))
    return success(service.serialize_booking(db, obj, viewer=user), "Đã trả lại để chỉnh sửa")


@router.post("/{bid}/dispatch/reject")
def dispatch_reject_booking(bid: int, data: ReasonIn, background_tasks: BackgroundTasks,
                            db: Session = Depends(get_db),
                            user=Depends(require("vehicle_booking", "write"))):
    """Điều phối viên TỪ CHỐI phiếu ĐANG Đã điều phối → khóa phiếu (gỡ điều phối)."""
    obj = _scoped_or_404(db, bid, user, "write")
    obj = service.reject_booking(db, obj, data, user, background_tasks)
    audit_record(db, user.id, "vehicle_booking", obj.id, "cancel",
                 _with_reason("Từ chối yêu cầu (điều phối)", data.reason))
    return success(service.serialize_booking(db, obj, viewer=user), "Đã từ chối yêu cầu")


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
