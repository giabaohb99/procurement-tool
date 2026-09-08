"""API ĐẶT PHÒNG HỌP — `/api/room-bookings` và `/api/meeting-rooms`.

Gác hai trục như mọi module: `require("room_booking", action)` cho quyền hành
động, `apply_scope(...)` bó phạm vi. Lấy một phiếu theo id đi qua `get_scoped` —
`db.get()` bỏ qua sạch bộ lọc, gõ id lên URL là đọc được lịch họp của phòng ban
khác kèm nội dung cuộc họp.

Danh mục phòng dựng bằng `make_crud_router` (khóa `meeting_room`): nó là danh
mục thuần, không có chốt chặn nào ngoài "không xóa phòng đang có phiếu".
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_perm_profile, require
from app.core.base_controller import (apply_filters, apply_sort_from_request,
                                      pagination)
from app.core.crud import make_crud_router
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped

from . import approval_bridge, serializer, service
from .constants import RB_APPROVED, RB_CANCELLED, RB_PENDING
from .model import MeetingRoom, RoomBooking
from .schema import (LocalDateTime, MeetingRoomCreate, MeetingRoomResponse,
                     MeetingRoomUpdate, RoomBookingCreate, RoomBookingReschedule,
                     RoomBookingUpdate)

ENTITY = "room_booking"

router = APIRouter(prefix="/api/room-bookings", tags=["meeting-room"])


def _block_delete_room_in_use(db: Session, obj: MeetingRoom) -> None:
    """Chốt `before_delete`: phòng đang có phiếu thì không xóa.

    Xóa là để lại phiếu mồ côi trỏ vào một `room_id` không còn tồn tại — màn lịch
    sẽ hiện những cuộc họp không biết ở đâu. Muốn dẹp phòng thì bỏ tick «Đang
    dùng», phiếu cũ vẫn đọc được.
    """
    used = (db.query(RoomBooking)
            .filter(RoomBooking.room_id == obj.id,
                    RoomBooking.is_deleted.is_(False)).count())
    if used:
        raise HTTPException(
            400, f"«{obj.name}» đang có {used} phiếu đặt nên không xóa được. "
                 "Bỏ tick «Đang dùng» để ẩn khỏi ô chọn thay vì xóa.")


meeting_room_router = make_crud_router(
    "/api/meeting-rooms", "meeting_room", MeetingRoom,
    MeetingRoomCreate, MeetingRoomUpdate, MeetingRoomResponse,
    filterable=["code", "name", "company_id", "is_active"],
    unique_field="code",
    before_delete=_block_delete_room_in_use,
)


# ── Phiếu đặt ──────────────────────────────────────────────────────────────────

def _dump_many(db: Session, items: list[RoomBooking]) -> list[dict]:
    rooms = serializer.room_map(db, {i.room_id for i in items})
    names = serializer.names_of(db, {i.requester_employee_id for i in items})
    return [serializer.dump_booking(i, rooms, names) for i in items]


def _dump_one(db: Session, obj: RoomBooking) -> dict:
    return _dump_many(db, [obj])[0]


@router.get("")
def list_bookings(
    request: Request,
    pg: dict = Depends(pagination),
    search: str | None = None,
    from_time: LocalDateTime | None = Query(None, description="Lọc theo khoảng: họp TỪ lúc"),
    to_time: LocalDateTime | None = Query(None, description="Lọc theo khoảng: họp ĐẾN lúc"),
    db: Session = Depends(get_db),
    user=Depends(require(ENTITY, "read")),
):
    """Danh sách phiếu trong phạm vi người xem («Phiếu của tôi» khi phạm vi = own).

    `from_time`/`to_time` lọc theo GIAO NHAU của khoảng, không phải theo cột
    `start_at` đơn lẻ — màn Lịch hỏi "hôm nay phòng nào bận", và một cuộc họp
    bắt đầu từ hôm qua kéo sang hôm nay phải lọt vào.
    """
    query = db.query(RoomBooking).filter(RoomBooking.is_deleted.is_(False))
    query = apply_filters(query, RoomBooking, request, service.FILTERABLE)
    query = service.apply_keyword_search(query, search)
    if from_time:
        query = query.filter(RoomBooking.end_at >= from_time)
    if to_time:
        query = query.filter(RoomBooking.start_at <= to_time)
    query = apply_scope(query, RoomBooking, ENTITY, user, get_perm_profile(db, user))
    query = apply_sort_from_request(query, RoomBooking, request,
                                    default=RoomBooking.start_at.desc())
    total = query.count()
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": _dump_many(db, items)})


@router.get("/availability")
def check_availability(
    #  ⚠️ `LocalDateTime` chứ không phải `datetime` trần: hai ô này cũng đi vào
    #  `check_time_range`, nên nhận giờ kèm múi giờ là sập y hệt các đường ghi
    #  (xem `_reject_timezone`). Đường ĐỌC nên càng dễ bị gọi bằng tay.
    start_at: LocalDateTime,
    end_at: LocalDateTime,
    company_id: int = 0,
    db: Session = Depends(get_db),
    user=Depends(require(ENTITY, "read")),
):
    """Phòng nào trống trong khoảng này — **cảnh báo sớm**, không phải chốt chặn.

    ⚠️ Đường này đứng TRƯỚC `/{bid}` trong tệp: khai sau thì `/{bid}` nuốt mất
    chữ `availability` và trả 422 vì không ép được sang số (cùng bẫy đã gặp với
    `/api/leave-requests/inbox/...`, xem `main.py`).
    """
    return success(service.list_availability(db, start_at, end_at, company_id))


def _get_or_404(db: Session, bid: int, user, action: str = "read") -> RoomBooking:
    obj = get_scoped(db, RoomBooking, ENTITY, bid, user, get_perm_profile(db, user),
                     action)

    #  Người ĐANG được giao ký phiếu này đọc được nó, dù phạm vi dữ liệu không
    #  với tới. Chỉ mở cho `read` — được giao ký KHÔNG có nghĩa là được sửa hay
    #  xóa phiếu của người khác.
    if obj is None and action == "read" and approval_bridge.can_read_booking(db, bid, user):
        obj = db.get(RoomBooking, bid)

    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy phiếu đặt phòng")
    return obj


@router.get("/{bid}")
def get_booking(bid: int, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "read"))):
    obj = _get_or_404(db, bid, user)
    data = _dump_one(db, obj)
    data["attendees"] = serializer.dump_attendees(db, obj)
    return success(data)


@router.post("")
def create_booking(data: RoomBookingCreate, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "create"))):
    obj = service.create(db, data, user)
    audit_record(db, user.id, ENTITY, obj.id, "create", f"Lập phiếu đặt phòng {obj.code}")
    return success(_dump_one(db, obj), "Đã lưu phiếu đặt phòng")


@router.patch("/{bid}")
def update_booking(bid: int, data: RoomBookingUpdate, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "write"))):
    obj = _get_or_404(db, bid, user, "write")
    obj = service.update(db, obj, data, user)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Sửa phiếu đặt phòng {obj.code}")
    return success(_dump_one(db, obj), "Đã cập nhật")


@router.patch("/{bid}/reschedule")
def reschedule_booking(bid: int, data: RoomBookingReschedule,
                       db: Session = Depends(get_db),
                       user=Depends(require(ENTITY, "write"))):
    """Dời giờ / đổi phòng — đường phục vụ thao tác KÉO THẢ trên màn Lịch.

    Tách khỏi `PATCH /{bid}` vì hai đường khác nhau ở chốt sửa: `update` chỉ nhận
    phiếu chưa vào luồng, còn lịch thì chỉ vẽ phiếu ĐÃ vào luồng. Xem
    `service.reschedule` về vì sao trạng thái được giữ nguyên.
    """
    obj = _get_or_404(db, bid, user, "write")
    before = f"{obj.start_at:%H:%M %d/%m}"
    obj = service.reschedule(db, obj, data.room_id, data.start_at, data.end_at, user)
    audit_record(db, user.id, ENTITY, obj.id, "update",
                 f"Dời phiếu {obj.code} từ {before} sang "
                 f"{obj.start_at:%H:%M %d/%m}–{obj.end_at:%H:%M}")

    #  Chỉ báo lại khi phiếu ĐÃ DUYỆT: phiếu còn chờ duyệt thì chưa ai được mời
    #  (thư mời gửi ở nhịp duyệt xong), báo dời một cuộc họp chưa từng được báo
    #  là gửi thư về một việc người nhận chưa biết có tồn tại.
    if obj.status == RB_APPROVED:
        approval_bridge.notify_attendees(db, obj, moved=True)
        db.commit()
    return success(_dump_one(db, obj), "Đã dời lịch")


@router.delete("/{bid}")
def delete_booking(bid: int, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "delete"))):
    obj = _get_or_404(db, bid, user, "delete")
    code = obj.code
    service.soft_delete(db, obj, user)
    audit_record(db, user.id, ENTITY, bid, "delete", f"Xóa phiếu đặt phòng {code}")
    return success(None, "Đã xóa phiếu")


@router.post("/{bid}/submit")
def submit_booking(bid: int, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "write"))):
    """Gửi duyệt: kiểm phòng trống TRƯỚC, trình bộ máy SAU, rồi mới giữ phòng.

    Thứ tự đó là có chủ ý — trình phiếu xong mới phát hiện phòng đã có người thì
    phải đi rút phiếu, và người dùng đã kịp thấy một phiếu duyệt hiện ra rồi
    biến mất.
    """
    obj = _get_or_404(db, bid, user, "write")
    service.prepare_submit(db, obj, user)

    #  GIỮ CHỖ trước, trình bộ máy sau. Thứ tự này là chốt chặn đường đua: giữ
    #  chỗ đi qua khoá hàng phòng và commit ngay, nên hai người bấm cùng lúc thì
    #  người thứ hai đọc được trạng thái của người thứ nhất (xem `reserve_slot`).
    #
    #  Trình bộ máy hỏng thì phải NHẢ chỗ ra: phiếu kẹt ở «Chờ duyệt» mà không
    #  có phiên duyệt là phòng bị khóa vĩnh viễn và không ai ký được.
    obj = service.reserve_slot(db, obj, user)
    try:
        instance_id = approval_bridge.start_approval(db, obj, user)
    except Exception:
        service.rollback_to_draft(db, obj)
        raise
    obj = service.attach_instance(db, obj, instance_id)
    audit_record(db, user.id, ENTITY, obj.id, "update",
                 f"Gửi duyệt phiếu đặt phòng {obj.code}")
    return success(_dump_one(db, obj), "Đã gửi duyệt")


@router.post("/{bid}/approve")
def approve_booking(bid: int, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "approve"))):
    """Duyệt THẲNG — chỉ dùng khi môi trường chưa khai luồng nhiều bước."""
    obj = _get_or_404(db, bid, user, "approve")
    if obj.status != RB_PENDING:
        raise HTTPException(400, "Chỉ duyệt được phiếu đang ở trạng thái Chờ duyệt")
    approval_bridge.block_legacy_path(db, obj)

    #  Dùng lại đúng hook của bộ máy duyệt, không chép luật ra đây — chép là hai
    #  đường duyệt và một trong hai sẽ quên kiểm trùng hoặc quên báo người dự.
    class _DirectApproval:
        updated_by = user.id
        finish_reason = ""

    approval_bridge._on_approved(db, obj.id, _DirectApproval())
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "approve", f"Duyệt phiếu đặt phòng {obj.code}")
    return success(_dump_one(db, obj), "Đã duyệt phiếu")


@router.post("/{bid}/reject")
def reject_booking(bid: int, reason: str = Query("", max_length=500),
                   db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "approve"))):
    """Từ chối THẲNG — cùng điều kiện với `/approve`."""
    obj = _get_or_404(db, bid, user, "approve")
    if obj.status != RB_PENDING:
        raise HTTPException(400, "Chỉ từ chối được phiếu đang ở trạng thái Chờ duyệt")
    approval_bridge.block_legacy_path(db, obj)

    class _DirectRejection:
        updated_by = user.id
        finish_reason = reason

    approval_bridge._on_rejected(db, obj.id, _DirectRejection())
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Từ chối phiếu {obj.code}")
    return success(_dump_one(db, obj), "Đã từ chối phiếu")


@router.post("/{bid}/cancel")
def cancel_booking(bid: int, reason: str = Query("", max_length=500),
                   db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "cancel"))):
    """Hủy phiếu và NHẢ phòng — cả phiếu đang chờ lẫn phiếu đã duyệt.

    ⚠️ KHÔNG gọi `block_legacy_path` ở đây: hủy phiếu của chính mình không phải
    đi vòng qua luồng. Đường hủy tự rút phiên duyệt trước (xem `cancel_booking`
    của `approval_bridge`).
    """
    obj = _get_or_404(db, bid, user, "cancel")
    if obj.status in (RB_CANCELLED,):
        raise HTTPException(400, "Phiếu này đã hủy rồi")
    obj = approval_bridge.cancel_booking(db, obj, reason, user)
    audit_record(db, user.id, ENTITY, obj.id, "cancel", f"Hủy phiếu đặt phòng {obj.code}")
    return success(_dump_one(db, obj), "Đã hủy phiếu")


@router.get("/{bid}/attendees")
def list_attendees(bid: int, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "read"))):
    """Danh sách người được mời — tách khỏi `/{bid}` cho màn nào chỉ cần phần này."""
    obj = _get_or_404(db, bid, user)
    return success(serializer.dump_attendees(db, obj))


#  Phiếu ĐÃ DUYỆT không sửa được nữa: hằng số này để các màn khác đọc chung một
#  nguồn thay vì tự đoán.
FINAL_APPROVED = RB_APPROVED
