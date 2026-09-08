"""NỐI PHIẾU ĐẶT PHÒNG VÀO BỘ MÁY DUYỆT DÙNG CHUNG — duoc-CR-279.

Bốn kết cục của bộ máy đều phải có mặt ở đây, đúng như Nghỉ phép:

    approved  →  phòng thuộc về phiếu này, báo cho người được mời
    rejected  →  nhả phòng, phiếu khóa
    returned  →  nhả phòng, phiếu về «Trả về» để sửa rồi gửi lại
    withdrawn →  nhả phòng, phiếu về «Nháp»

⚠️ Ở đây "nhả phòng" **chỉ là đổi trạng thái** chứ không phải cộng trừ một con số
như quỹ phép — nhưng hậu quả của việc quên thì giống hệt: phòng bị khóa vĩnh viễn
trong khung giờ đó và không ai hiểu vì sao. Vì thế ba kết cục không-duyệt gộp
chung một hàm `_release_and_set`, đừng tách ba bản chép.

**Chưa khai luồng thì vẫn chạy được.** `instance_service.start()` trả `None` khi
không luồng nào áp; lúc đó phiếu vẫn vào *Chờ duyệt* với `approval_instance_id = 0`
và người có quyền `room_booking.approve` bấm duyệt thẳng. Không có đường lùi này
thì cài mới xong là không ai đặt nổi phòng cho tới khi quản trị khai xong luồng.

**Và cả cái cờ nữa** (`ApprovalSwitch` cho entity `room_booking`, màn «Bật bộ máy
duyệt»). Trước đây đặt phòng trình thẳng vào bộ máy không hỏi cờ, nên dòng công
tắc của nó bày ra cũng chỉ là nút giả. Nay `start_approval` hỏi cờ trước: TẮT thì
đi đúng đường lùi ở đoạn trên. Đó là điểm khác biệt so với "chưa khai luồng" —
đường lùi kia là *tình cờ chưa có luồng*, còn cái này là *cố ý tắt để quay về*.
"""
import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.approval import entity_hooks, flow_service, instance_service

from . import service
from .constants import (RB_APPROVED, RB_DRAFT, RB_PENDING, RB_REJECTED,
                        RB_RETURNED)
from .model import MeetingRoom, RoomBooking, RoomBookingAttendee

ENTITY = "room_booking"


def entity_context(obj: RoomBooking) -> dict:
    """Bối cảnh để chọn người duyệt và xét điều kiện rẽ nhánh.

    Chỉ những ô THẬT SỰ dùng để rẽ nhánh — đổ cả bản ghi vào đây thì người khai
    luồng thấy hai chục tên cột và không biết chọn cái nào.

    `department_id` là của NGƯỜI ĐẶT (chép lúc lập phiếu), nên bước «trưởng bộ
    phận của phòng chủ trì» trỏ đúng vào sếp của họ chứ không phải sếp của thư ký
    đặt hộ.
    """
    return {
        "id": obj.id,
        "room_id": obj.room_id,
        "requester_employee_id": obj.requester_employee_id,
        "company_id": obj.company_id,
        "department_id": obj.department_id,
        "attendee_count": obj.attendee_count,
    }


def is_enabled(db: Session) -> bool:
    """Bộ máy duyệt nhiều bước có đang bật cho đặt phòng họp không (màn «Bật bộ máy duyệt»)."""
    return flow_service.is_enabled(db, ENTITY)


def running_instance(db: Session, booking_id: int):
    return instance_service.running_instance(db, ENTITY, booking_id)


def block_legacy_path(db: Session, obj: RoomBooking) -> None:
    """Phiếu đang có phiên duyệt chạy thì KHÔNG cho bấm duyệt thẳng.

    Không có chốt này thì nút duyệt một bước thành đường tắt đi vòng qua cả
    luồng — lỗ hổng đã phải vá cho Văn thư rồi cho Nghỉ phép.

    ⚠️ CHỈ áp cho *duyệt* và *từ chối*. **Đừng gọi ở đường HỦY** — hủy phiếu của
    chính mình không phải đi vòng qua luồng (bài học 03/09/2026 của Nghỉ phép).
    """
    if running_instance(db, obj.id) is not None:
        raise HTTPException(
            400, "Phiếu này đang chạy trong luồng phê duyệt nhiều bước. "
                 "Duyệt ở màn Phê duyệt, đừng bấm duyệt thẳng ở đây.")


def withdraw_running_approval(db: Session, obj: RoomBooking, user,
                              reason: str = "") -> None:
    """RÚT phiên duyệt đang chạy, để phiếu hủy được. Không có phiên thì không làm gì.

    Không rút thì hủy phiếu xong phiên duyệt vẫn chạy: người duyệt vẫn thấy việc
    chờ mình, ký xong là hook `on_approved` chốt phòng cho một cuộc họp đã hoãn.

    Dùng lại `action_service.withdraw` chứ không tự đặt trạng thái phiên — hai
    luật "chỉ người trình mới rút được" và "đã có người ký thì không rút" nằm ở
    đó, và cả hai đều đúng với đặt phòng.
    """
    instance = running_instance(db, obj.id)
    if instance is None:
        return

    from app.modules.approval import action_service

    note = (reason or "").strip()
    action_service.withdraw(
        db, instance, getattr(user, "employee_id", 0) or 0, user.id,
        f"Hủy phiếu đặt phòng: {note}" if note else "Người đặt hủy phiếu")


def cancel_booking(db: Session, obj: RoomBooking, reason: str, user) -> RoomBooking:
    """HỦY phiếu: rút phiên duyệt (nếu còn chạy) rồi hủy và nhả phòng.

    Đặt ở đây chứ không ở controller: đây là nghiệp vụ HAI BƯỚC phải đi liền
    nhau, và đúng thứ tự hai bước này là chỗ Nghỉ phép đã sai một lần.
    """
    withdraw_running_approval(db, obj, user, reason)
    db.refresh(obj)
    return service.cancel(db, obj, reason, user.id)


def start_approval(db: Session, obj: RoomBooking, user) -> int:
    """Trình phiếu vào bộ máy. Trả id phiên, hoặc `0` khi cờ TẮT / không luồng nào áp.

    Hỏi cờ TRƯỚC khi mở phiên, không phải sau: `instance_service.start()` đã ghi
    bản chụp luồng và sinh việc cho người duyệt rồi thì hủy đi là vứt luôn mấy
    dòng dấu vết vừa tạo.
    """
    if not is_enabled(db):
        return 0

    instance = instance_service.start(
        db, ENTITY, obj.id, entity_context(obj),
        submitter_employee_id=obj.requester_employee_id, actor=user.id,
        entity_code=obj.code,
        entity_title=f"Đặt phòng họp {obj.code} — {obj.title}",
    )
    return instance.id if instance is not None else 0


# ── Bốn kết cục ────────────────────────────────────────────────────────────────

def _get(db: Session, booking_id: int) -> RoomBooking | None:
    obj = db.get(RoomBooking, booking_id)
    return obj if obj is not None and not obj.is_deleted else None


def _reason(instance, default: str) -> str:
    return (getattr(instance, "finish_reason", "") or default)[:500]


def _on_approved(db: Session, booking_id: int, instance) -> None:
    """Ký hết các bước: chốt phòng rồi báo cho người được mời.

    ⚠️ **Kiểm trùng LẦN NỮA ngay trước khi chốt.** Bình thường không thể trùng —
    phiếu đã giữ phòng từ lúc gửi duyệt. Nhưng phiếu nằm chờ ký có thể hàng tuần,
    và trong quãng đó dữ liệu còn bị sửa tay, phiếu cũ còn được khôi phục. Chốt
    một phòng cho hai cuộc họp là lỗi người dùng gánh bằng cả buổi sáng đứng ngoài
    cửa, nên rẻ hơn nhiều là hỏi lại một câu truy vấn.
    """
    obj = _get(db, booking_id)
    if obj is None or obj.status == RB_APPROVED:
        return

    room = db.get(MeetingRoom, obj.room_id)
    if room is not None:
        service.check_conflict(db, room, obj.start_at, obj.end_at, exclude_id=obj.id)

    obj.status = RB_APPROVED
    obj.decided_at = datetime.now()
    obj.decision_note = ""
    obj.updated_by = instance.updated_by or 0
    db.flush()

    notify_attendees(db, obj)


def _release_and_set(db: Session, booking_id: int, instance, status: int,
                     default_reason: str) -> None:
    """Ba kết cục KHÔNG duyệt: nhả phòng rồi đặt trạng thái.

    Gộp một hàm vì cả ba làm đúng một việc với phòng — tách ra ba bản chép thì
    sớm muộn có một bản để phiếu ở lại `RB_PENDING` và khóa phòng vĩnh viễn.
    """
    obj = _get(db, booking_id)
    if obj is None or obj.status != RB_PENDING:
        return
    actor = instance.updated_by or 0
    obj.status = status
    obj.decision_note = _reason(instance, default_reason)
    obj.decided_at = datetime.now()
    obj.updated_by = actor
    db.flush()


def _on_rejected(db: Session, booking_id: int, instance) -> None:
    """Từ chối → phiếu khóa. Muốn họp nữa thì đặt phiếu khác, không sửa phiếu cũ."""
    _release_and_set(db, booking_id, instance, RB_REJECTED, "Bị từ chối")


def _on_returned(db: Session, booking_id: int, instance) -> None:
    """Trả về người đặt → sửa được và gửi duyệt LẠI được.

    Khác «từ chối» đúng ở chỗ đó, và phải khác: người đặt mở phiếu ra mà chỉ
    thấy «Nháp» thì không biết mình vừa bị dẹp hay đang được mời sửa lại.
    """
    _release_and_set(db, booking_id, instance, RB_RETURNED, "Trả về chỉnh sửa")


def _on_withdrawn(db: Session, booking_id: int, instance) -> None:
    """Người đặt tự rút → về **Nháp**, không phải «Trả về»: không ai trả gì cho họ."""
    _release_and_set(db, booking_id, instance, RB_DRAFT, "")


entity_hooks.register(
    ENTITY,
    on_approved=_on_approved,
    on_rejected=_on_rejected,
    on_returned=_on_returned,
    on_withdrawn=_on_withdrawn,
)


def _context_by_id(db: Session, booking_id: int) -> dict:
    """Dựng lại bối cảnh từ id — cho lúc SỬA LUỒNG phải tính lại người duyệt."""
    obj = _get(db, booking_id)
    return entity_context(obj) if obj else {}


entity_hooks.register_subject(ENTITY, _context_by_id)


def can_read_booking(db: Session, booking_id: int, user) -> bool:
    """Ai được xem phiếu này: **trong phạm vi dữ liệu, HOẶC đang phải ký nó**.

    Vế sau không có thì bộ máy giao việc cho người duyệt rồi chặn chính họ mở
    phiếu ra đọc — đúng lỗi đã vá ở Nghỉ phép (CR-260). Nới đúng **lúc đang có
    việc treo**, không nới cho người «đã từng ký»: ký xong quyền đó đóng lại.
    """
    from app.core.auth import get_perm_profile
    from app.core.scoping import get_scoped
    from app.modules.approval import steps_service

    if get_scoped(db, RoomBooking, ENTITY, booking_id, user,
                  get_perm_profile(db, user)) is not None:
        return True

    return steps_service.has_pending_task(
        db, ENTITY, booking_id, getattr(user, "employee_id", 0) or 0)


def _can_read(db: Session, booking_id: int, user) -> bool:
    return can_read_booking(db, booking_id, user)


entity_hooks.register_reader(ENTITY, _can_read)


# ── Báo cho người được mời ─────────────────────────────────────────────────────

def notify_attendees(db: Session, obj: RoomBooking, moved: bool = False) -> int:
    """Gửi thông báo chuông cho người được mời. Trả số thư đã gửi.

    `moved=True` là đường **dời lịch** (kéo thả trên màn Lịch): cùng người nhận,
    cùng cái chuông, chỉ khác câu mở đầu. Một cuộc họp bị dời mà người dự không
    được báo thì họ tới đúng phòng cũ vào đúng giờ cũ — tệ hơn cả không mời.

    Gửi ở nhịp **DUYỆT XONG**, không phải lúc lập phiếu: phiếu chưa duyệt thì
    cuộc họp chưa chắc diễn ra, mà thư đã gửi rồi không rút lại được. Người dự
    nhận đúng một thư cho một cuộc họp.

    ⚠️ **Nuốt lỗi có chủ ý.** Thông báo hỏng (người dự chưa có tài khoản, bảng
    thông báo có chuyện) không được phép làm hỏng việc chốt phòng — phòng đã
    duyệt là chuyện lớn hơn một cái chuông. Cùng lẽ với `notify_new_tasks` của
    bộ máy duyệt, kể cả cách nuốt: ghi log rồi đi tiếp.

    Ghi thẳng vào `tab_notification` như `task_notification` làm — cùng cái
    chuông, cùng trang `/notifications`, cùng số chưa đọc. Không đẻ hộp thư thứ hai.
    """
    rows = (db.query(RoomBookingAttendee)
            .filter(RoomBookingAttendee.booking_id == obj.id).all())
    employee_ids = {r.employee_id for r in rows if r.employee_id}
    #  Người ĐẶT không nhận thư mời của chính mình.
    employee_ids.discard(obj.requester_employee_id)
    if not employee_ids:
        return 0

    written = 0
    try:
        from app.modules.notification.model import Notification
        from app.modules.user.model import User

        room = db.get(MeetingRoom, obj.room_id)
        where = room.name if room else ""
        users = (db.query(User)
                 .filter(User.employee_id.in_(employee_ids), User.is_active.is_(True))
                 .all())
        for account in users:
            db.add(Notification(
                user_id=account.id,
                title=f"{'Đổi giờ họp' if moved else 'Mời họp'}: {obj.title}",
                body=(f"{obj.start_at:%H:%M %d/%m/%Y} – {obj.end_at:%H:%M}"
                      + (f" tại {where}" if where else "")
                      + f". Phiếu {obj.code}."),
                link=f"/hr/room-bookings/{obj.id}",
                created_by=obj.updated_by or 0,
            ))
            written += 1
    except Exception as error:  # noqa: BLE001 — xem docstring
        logging.getLogger(__name__).exception(
            "Không báo được người dự của phiếu %s: %s", obj.code, error)
    return written
