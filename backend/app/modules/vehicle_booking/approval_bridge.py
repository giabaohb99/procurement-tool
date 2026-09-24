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
import logging
from datetime import datetime
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.approval import entity_hooks, flow_service, instance_service

from .model import (BK_APPROVED, BK_DISPATCHED, BK_DRAFT, BK_PENDING,
                    BK_REJECTED, BK_RETURNED, VehicleBooking)

ENTITY = "vehicle_booking"

#  Trạng thái phiếu mà một kết cục của luồng CÒN CÓ NGHĨA. Ngoài khoảng này ra
#  thì phiếu đã đi đường khác (bị xóa, đã khóa, đã chạy xong chuyến) và bộ máy
#  KHÔNG được đặt lại trạng thái — xem `_booking_for_outcome`.
_OPEN_FOR_FLOW = (BK_PENDING, BK_APPROVED, BK_DISPATCHED)


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


def latest_instance(db: Session, booking_id: int):
    """Phiên duyệt mới nhất, KỂ CẢ đã kết thúc — để trang chi tiết còn vẽ dấu vết."""
    return instance_service.latest_instance(db, ENTITY, booking_id)


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


def _booking_for_outcome(db: Session, booking_id: int, what: str) -> VehicleBooking | None:
    """Phiếu mà kết cục của luồng ĐƯỢC PHÉP đụng vào. `None` = bỏ qua, có ghi log.

    ⚠️ Không có chốt này thì hook đặt trạng thái VÔ ĐIỀU KIỆN, và mỗi cửa đổi
    trạng thái khác của đặt xe đều biến thành một đường làm hỏng dữ liệu:

    * phiếu **đã bị từ chối** (điều phối viên từ chối trong lúc luồng còn chạy)
      SỐNG LẠI thành «Đã duyệt» khi người duyệt bấm Duyệt sau đó;
    * phiếu **đã xóa** vẫn được đặt lại trạng thái, nên `is_deleted` mang một
      trạng thái mới toanh mà không màn nào bày ra để ai đó sửa;
    * phiếu **đã chạy xong chuyến** bị đẩy lùi về «Đã duyệt».

    Đây là chốt cuối, không thay cho `block_legacy_path` ở controller: cửa kia
    nói với người bấm «đi ra màn duyệt», cửa này giữ dữ liệu khi có đường nào lọt.
    """
    booking = db.get(VehicleBooking, booking_id)
    if booking is None or booking.is_deleted:
        logging.getLogger(__name__).warning(
            "Luồng duyệt %s phiếu đặt xe #%s: phiếu không còn tồn tại", what, booking_id)
        return None
    if booking.status not in _OPEN_FOR_FLOW:
        logging.getLogger(__name__).warning(
            "Luồng duyệt %s phiếu đặt xe #%s: phiếu đang ở trạng thái %s nên KHÔNG đổi "
            "trạng thái theo luồng", what, booking_id, booking.status)
        return None
    return booking


def _on_approved(db: Session, booking_id: int, instance) -> None:
    """Ký hết các bước → phiếu Đã duyệt (chờ điều phối). Báo Điều phối viên + Người tạo."""
    from .notify import notify_approved

    booking = _booking_for_outcome(db, booking_id, "duyệt")
    if booking is None:
        return
    #  ⚠️ GHI NGƯỜI KÝ THẬT + MỐC GIỜ, đúng như đường duyệt một bước.
    #
    #  Thiếu hai cột này thì `serialize_booking` lùi về `first_approver_id` —
    #  **người mà NGƯỜI TẠO tự chọn trong biểu mẫu**, có thể chưa hề ký và có thể
    #  không nằm trong luồng — rồi trang chi tiết lẫn BẢN IN đều ghi tên người đó
    #  ở dòng «Người phê duyệt», với ô thời gian trống
    #  (`build-booking-stages.ts` đọc `approved_at`).
    booking.approved_by = instance.updated_by or 0
    booking.approved_at = datetime.now().isoformat(timespec="seconds")
    #  Phiếu đã được điều phối trước khi ký xong (cửa điều phối cố ý không chặn
    #  trạng thái Chờ duyệt) thì GIỮ NGUYÊN «Đã điều phối»: đẩy lùi về «Đã duyệt»
    #  là xóa mất bước đã đi, trong khi xe và tài xế vẫn đang giữ chuyến đó.
    if booking.status == BK_PENDING:
        booking.status = BK_APPROVED
    booking.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, booking_id, instance, "approve", "Xong hết các bước của luồng — đã duyệt")
    notify_approved(db, booking, None, actor=_actor(instance))


def _clear_dispatch_if_needed(booking: VehicleBooking) -> None:
    """Phiếu bị chặn mà đang giữ xe/tài xế thì phải nhả ra — cùng luật với
    `service._clear_dispatch` ở đường duyệt một bước. Không nhả thì xe vẫn bị
    tính là có chuyến trong phép chống trùng khung giờ của một phiếu đã khóa."""
    from .service import _clear_dispatch

    if booking.status == BK_DISPATCHED:
        _clear_dispatch(booking)


def _on_rejected(db: Session, booking_id: int, instance) -> None:
    """Từ chối ở một bước → phiếu Từ chối (khóa)."""
    from .notify import notify

    booking = _booking_for_outcome(db, booking_id, "từ chối")
    if booking is None:
        return
    reason = _reason(instance, "Bị từ chối")
    _clear_dispatch_if_needed(booking)
    booking.status = BK_REJECTED
    #  Lý do ở nhật ký + thông báo, không ghi vào Ghi chú.
    booking.updated_by = instance.updated_by or 0
    db.commit()
    _write_log(db, booking_id, instance, "cancel", reason)
    notify(db, "dx_rejected", booking, None, actor=_actor(instance), reason=reason)


def _on_returned(db: Session, booking_id: int, instance) -> None:
    """Trả lại tận người nộp → phiếu Yêu cầu chỉnh sửa (sửa & gửi lại được)."""
    from .notify import notify

    booking = _booking_for_outcome(db, booking_id, "trả lại")
    if booking is None:
        return
    reason = _reason(instance, "Bị trả về")
    _clear_dispatch_if_needed(booking)
    booking.status = BK_RETURNED
    #  Lý do ở nhật ký + thông báo, không ghi vào Ghi chú.
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
    booking = _booking_for_outcome(db, booking_id, "rút lại")
    if booking is None:
        return
    _clear_dispatch_if_needed(booking)
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


def booking_for_approver(db: Session, booking_id: int, user) -> VehicleBooking | None:
    """Phiếu mà người này đang PHẢI KÝ — `None` nếu họ không giữ việc nào trên nó.

    Đường lùi của `GET /api/vehicle-bookings/{id}` khi `get_scoped` không cho qua.
    Mở cửa ĐỌC ở `entity_hooks` thôi thì chưa đủ: nút Duyệt của Đặt xe nằm trong
    `BookingApprovalPanel`, mà panel đó nằm TRONG trang chi tiết phiếu — chi tiết
    404 thì người duyệt vẫn không tới được nút của mình.

    Chỉ ĐỌC. Mọi cửa GHI (sửa · điều phối · duyệt thẳng) vẫn đi qua `get_scoped`
    với đúng hành động của nó.
    """
    from app.modules.approval import steps_service

    booking = db.get(VehicleBooking, booking_id)
    if booking is None or booking.is_deleted:
        return None
    if not steps_service.has_pending_task(
            db, ENTITY, booking_id, getattr(user, "employee_id", 0) or 0):
        return None
    return booking


def _can_read_booking(db: Session, booking_id: int, user) -> bool:
    """Ai xem được phiếu này: **trong phạm vi dữ liệu, HOẶC đang phải ký nó**.

    Vế đầu là luật cũ — dùng lại đúng phạm vi của `vehicle_booking`, không chép
    luật lần hai. Bỏ nó là `/api/approvals/of/vehicle_booking/<id>` phơi mục đích
    chuyến + tên người đi cho bất kỳ ai đăng nhập (lỗ đã dựng lại được với văn
    bản 25/08/2026).

    ⚠️ Vế sau thêm 21/09/2026, và không có nó thì **luồng duyệt nhiều bước của
    Đặt xe không chạy được**: chặng 2 của luồng thật gần như luôn là người phòng
    khác (Hành chính · Nhân sự · Ban giám đốc), mà phạm vi dữ liệu của họ không
    với tới phiếu của phòng Kế toán. Nặng hơn Nghỉ phép một bậc vì Đặt xe **không
    còn màn «Việc của tôi»** (xóa 21/08/2026) — chỗ duy nhất bấm Duyệt là
    `BookingApprovalPanel` NẰM TRONG trang chi tiết phiếu. Cho nên chuỗi hậu quả
    là: chi tiết phiếu 404 → `of/…` trả `null` → panel duyệt không render → thư
    báo bấm vào ra trang trống → **phiếu kẹt vĩnh viễn, không chỗ nào đỏ lên**.

    ⚠️ Nới đúng **lúc đang có việc treo**, không nới cho người «đã từng ký» —
    cùng lý lẽ với `can_read_request` của Nghỉ phép (CR-260): ký xong là quyền
    đọc thêm đó đóng lại, nếu không thì mỗi lượt ký lại thêm vĩnh viễn một phiếu
    vào tầm nhìn của một người và phạm vi dữ liệu phình dần, không ai rà lại được.
    """
    from app.core.auth import get_perm_profile
    from app.core.scoping import get_scoped

    obj = get_scoped(db, VehicleBooking, ENTITY, booking_id, user, get_perm_profile(db, user))
    if obj is not None and not obj.is_deleted:
        return True
    #  Phiếu đã xóa thì thôi, kể cả đang giữ việc: không còn gì để đọc.
    return booking_for_approver(db, booking_id, user) is not None


entity_hooks.register_reader(ENTITY, _can_read_booking)
