"""NỐI ĐẶT XE VÀO BỘ MÁY DUYỆT DÙNG CHUNG (PHA 6.1).

Trước đây phiếu đặt xe duyệt bằng ba nút cứng `approve / return / reject` — đúng
bằng "luồng một bước viết tay tạm thời". Ở đây nó được nối vào bộ máy nhiều bước
(`approval_flow`), **sau một cái cờ** (`ApprovalSwitch` cho entity `vehicle_booking`).

Giữ nguyên khi cờ TẮT hoặc chưa khai luồng nào:
  · gửi duyệt vẫn chạy đường cũ (đặt trạng thái Chờ duyệt + báo người duyệt);
  · trang chi tiết vẫn có ba nút cũ và chúng vẫn chạy;
  · không bảng nào của đặt xe đổi cấu trúc.

Cờ BẬT và có luồng khớp thì `submit_for_approval` mở một phiên nhiều bước; duyệt
xong bộ máy gọi ngược `_on_approved/...` ở dưới để đổi trạng thái phiếu. Khi đó
`block_legacy_path` khóa ba nút cũ để không có hai đường đổi trạng thái song song.

Mẫu: `app/modules/document/approval_bridge.py`.
"""
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.approval import entity_hooks, flow_service, instance_service

from .model import BK_APPROVED, BK_DRAFT, BK_REJECTED, BK_RETURNED, VehicleBooking

ENTITY = "vehicle_booking"


def entity_context(booking: VehicleBooking) -> dict:
    """Bối cảnh phiếu cho điều kiện rẽ nhánh + chọn người duyệt «lấy từ ô».

    Chỉ những ô thật sự có nghĩa để rẽ nhánh / định tuyến người duyệt.
    """
    return {
        #  `id` để khai được luồng riêng cho MỘT phiếu (bộ chọn "Áp dụng cho" sinh
        #  điều kiện `id in [...]`). Thiếu ô này lựa chọn đó không bao giờ khớp.
        "id": booking.id,
        "request_type": booking.request_type,
        "company_id": booking.company_id,
        "department_id": booking.department_id,
        "requester_id": booking.requester_id,
    }


def is_enabled(db: Session) -> bool:
    return flow_service.is_enabled(db, ENTITY)


def running_instance(db: Session, booking_id: int):
    """Phiên duyệt nhiều bước còn mở của phiếu này, `None` nếu không có."""
    return instance_service.running_instance(db, ENTITY, booking_id)


def block_legacy_path(db: Session, booking: VehicleBooking) -> None:
    """Khóa ba nút duyệt MỘT BƯỚC khi phiếu đang chạy trong bộ máy nhiều bước.

    Không có chốt này thì bất kỳ ai có `vehicle_booking.approve` cũng duyệt thẳng
    được một phiếu đang nằm ở chặng 1 của luồng — thành đường tắt đi vòng qua cả
    luồng, giống đúng ca đã bắt được ở Văn thư. Đặt ở controller: chính bộ máy gọi
    hàm đổi trạng thái khi duyệt xong, đặt ở service là nó tự chặn mình.
    """
    if running_instance(db, booking.id) is not None:
        raise HTTPException(
            400,
            "Phiếu này đang chạy trong luồng duyệt nhiều bước — xử lý ở màn "
            "«Việc của tôi», không duyệt thẳng ở đây.",
        )


def _employee_id_of_user(db: Session, actor: int) -> int | None:
    """Tài khoản đang bấm là nhân sự nào. `None` khi chưa gắn hồ sơ."""
    from app.modules.user.model import User

    if not actor:
        return None
    row = db.query(User.employee_id).filter(User.id == actor).first()
    return row[0] if row and row[0] else None


def submit_for_approval(db: Session, booking: VehicleBooking, actor: int):
    """Trình phiếu vào bộ máy. `None` = chưa khai luồng nào khớp → gọi đường cũ.

    **Người nộp = người BẤM GỬI DUYỆT** (lấy hồ sơ nhân sự của tài khoản), lùi về
    `requester_id` khi tài khoản chưa gắn hồ sơ — thà định tuyến theo phiếu còn hơn
    không định tuyến được.
    """
    return instance_service.start(
        db, ENTITY, booking.id, entity_context(booking),
        submitter_employee_id=(_employee_id_of_user(db, actor) or booking.requester_id or None),
        actor=actor,
        entity_code=booking.code or "",
        entity_title=booking.purpose or "",
    )


# ── Hàm chạy khi phiên duyệt kết thúc (bộ máy gọi ngược) ─────────────────────

def _write_log(db: Session, booking_id: int, instance, action: str, message: str) -> None:
    """Ghi kết cục vào NHẬT KÝ THAO TÁC của chính phiếu (đường bộ máy không đi qua
    controller nào của đặt xe nên phải tự ghi)."""
    from app.core.audit import record

    record(db, instance.updated_by or 0, ENTITY, booking_id, action, message)


def _reason(instance, default: str) -> str:
    return (instance.finish_reason or "").strip() or default


def _actor(instance) -> SimpleNamespace:
    return SimpleNamespace(id=instance.updated_by or 0)


def _append_note(booking: VehicleBooking, label: str, reason: str) -> None:
    from .service import _append_note as append

    append(booking, label, reason)


def _on_approved(db: Session, booking_id: int, instance) -> None:
    """Ký hết các bước → phiếu Đã duyệt (chờ điều phối). Báo Điều phối viên + Người tạo."""
    from .notify import notify_approved

    booking = db.get(VehicleBooking, booking_id)
    if booking is None:
        return
    booking.status = BK_APPROVED
    booking.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, booking_id, instance, "approve", "Xong hết các bước của luồng — đã duyệt")
    notify_approved(db, booking, None, actor=_actor(instance))


def _on_rejected(db: Session, booking_id: int, instance) -> None:
    """Từ chối ở một bước → phiếu Từ chối (khóa)."""
    from .notify import notify

    booking = db.get(VehicleBooking, booking_id)
    if booking is None:
        return
    reason = _reason(instance, "Bị từ chối")
    booking.status = BK_REJECTED
    _append_note(booking, "Từ chối", reason)
    booking.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, booking_id, instance, "cancel", reason)
    notify(db, "dx_rejected", booking, None, actor=_actor(instance), reason=reason)


def _on_returned(db: Session, booking_id: int, instance) -> None:
    """Trả lại tận người nộp → phiếu Yêu cầu chỉnh sửa (sửa & gửi lại được)."""
    from .notify import notify

    booking = db.get(VehicleBooking, booking_id)
    if booking is None:
        return
    reason = _reason(instance, "Bị trả về")
    booking.status = BK_RETURNED
    _append_note(booking, "Yêu cầu chỉnh sửa", reason)
    booking.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, booking_id, instance, "update", reason)
    notify(db, "dx_returned", booking, None, actor=_actor(instance), reason=reason)


def _on_withdrawn(db: Session, booking_id: int, instance) -> None:
    """Người nộp tự rút → phiếu VỀ NHÁP, sửa rồi gửi duyệt lại từ đầu.

    Phải có nhịp này, không thì rút xong phiếu kẹt ở Chờ duyệt: gửi lại không được
    (đường gửi chỉ nhận nháp/bị trả) mà `block_legacy_path` chỉ khóa khi phiên còn
    chạy — thành đường tắt duyệt không ai ký (đúng cảnh báo ở `entity_hooks`).
    """
    booking = db.get(VehicleBooking, booking_id)
    if booking is None:
        return
    booking.status = BK_DRAFT
    booking.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, booking_id, instance, "update", _reason(instance, "Người nộp tự rút"))


entity_hooks.register(
    ENTITY,
    on_approved=_on_approved,
    on_rejected=_on_rejected,
    on_returned=_on_returned,
    on_withdrawn=_on_withdrawn,
)


def _context_by_id(db: Session, booking_id: int) -> dict:
    """Dựng lại bối cảnh từ id — cho lúc SỬA LUỒNG phải tính lại người duyệt."""
    booking = db.get(VehicleBooking, booking_id)
    return entity_context(booking) if booking else {}


entity_hooks.register_subject(ENTITY, _context_by_id)


def _can_read_booking(db: Session, booking_id: int, user) -> bool:
    """Người này có đọc được phiếu của phiên duyệt đó không — bám đúng phạm vi
    `vehicle_booking` (dùng lại `get_scoped`, không chép luật lần hai)."""
    from app.core.auth import get_perm_profile
    from app.core.scoping import get_scoped

    obj = get_scoped(db, VehicleBooking, ENTITY, booking_id, user, get_perm_profile(db, user))
    return obj is not None and not obj.is_deleted


entity_hooks.register_reader(ENTITY, _can_read_booking)
