"""Nghiệp vụ Đặt xe nội bộ (DEGO Booking Auto) — MVP lát dọc.

Đợt này khép phần tạo & theo dõi phiếu của người dùng: tạo phiếu 2 loại (công tác /
giao hàng), lưu nháp hoặc gửi duyệt, danh sách "Yêu cầu của tôi" (đã bó phạm vi ở
controller), xem chi tiết, sửa khi còn nháp / bị trả về. Điều phối & tài xế ở đợt sau.
"""

import json
import re
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from .model import (
    BK_APPROVED,
    BK_CANCELLED,
    BK_COMPLETED,
    BK_DISPATCHED,
    BK_DRAFT,
    BK_PENDING,
    BK_REJECTED,
    BK_RETURNED,
    DRV_ACCEPTED,
    DRV_COMPLETED,
    DRV_ONGOING,
    DRV_REJECTED,
    DRV_WAITING,
    EDITABLE_STATUSES,
    TYPE_CAR,
    TYPE_DELIVERY,
    Driver,
    Vehicle,
    VehicleBooking,
)
from .notify import notify, notify_approved, notify_completed
from .schema import (
    CompleteIn,
    DispatchIn,
    DriverResponse,
    ReasonIn,
    VehicleBookingCreate,
    VehicleBookingResponse,
    VehicleBookingUpdate,
)

# Bộ lọc cho danh sách (whitelist của apply_filters). Cột số (status/request_type/…) tự
# so khớp chính xác; `code` để ô tìm nhanh lo nên KHÔNG đưa vào đây (xem apply_filters).
FILTERABLE = ["status", "request_type", "company_id", "department_id", "requester_id"]

# Ô "Tìm nhanh" trên danh sách quét các trường này.
SEARCH_FIELDS = ("code", "purpose", "requester", "start_location", "end_location")


def apply_keyword_search(query, keyword: str | None):
    """Lọc OR LIKE theo từ khóa trên nhiều trường. Bỏ trống thì giữ nguyên."""
    kw = (keyword or "").strip()
    if not kw:
        return query
    like = f"%{kw}%"
    return query.filter(or_(*[getattr(VehicleBooking, f).like(like) for f in SEARCH_FIELDS]))


def _requester_context(db: Session, user) -> tuple[str, int, int]:
    """Suy ra (tên hiển thị, phòng ban, công ty) của người tạo từ hồ sơ nhân sự.

    Snapshot lúc tạo để phiếu vẫn đúng dù hồ sơ đổi sau. Không có hồ sơ nhân sự thì
    lấy email làm tên, phạm vi để 0.
    """
    emp = None
    if getattr(user, "employee_id", 0):
        emp = db.get(Employee, user.employee_id)
    name = (emp.full_name if emp and emp.full_name else "") or getattr(user, "email", "") or ""
    dept_id = emp.department_id if emp else 0
    company_id = emp.company_id if emp else 0
    return name, dept_id or 0, company_id or 0


def _normalize_type(value: int | None) -> int:
    """Chỉ nhận 1 (công tác) hoặc 2 (giao hàng); lạ thì về công tác."""
    return TYPE_DELIVERY if value == TYPE_DELIVERY else TYPE_CAR


def _dump_stops(stops) -> str:
    """StopItem[] → chuỗi JSON, bỏ điểm dừng KHÔNG có địa điểm, giữ thứ tự.

    Mỗi điểm giữ cả tên + SĐT người liên hệ tại điểm đó.
    """
    out = []
    for s in stops or []:
        location = (s.location or "").strip()
        if not location:
            continue
        out.append({
            "location": location,
            "contact_name": (s.contact_name or "").strip(),
            "contact_phone": (s.contact_phone or "").strip(),
        })
    return json.dumps(out, ensure_ascii=False)


def _after_submit(db: Session, booking: VehicleBooking, user, background_tasks) -> None:
    """Sau khi phiếu chuyển sang Chờ duyệt.

    Bộ máy duyệt nhiều bước BẬT và có luồng khớp → mở một phiên (bộ máy tự báo
    người duyệt). Cờ TẮT, hoặc bật mà chưa khai luồng nào khớp → đi đường cũ: báo
    thẳng người duyệt bằng thông báo `dx_submitted`.
    """
    from .approval_bridge import is_enabled, submit_for_approval

    if is_enabled(db):
        instance = submit_for_approval(db, booking, getattr(user, "id", 0))
        if instance is not None:
            return  # bộ máy nhiều bước lo tiếp + tự báo người duyệt
    notify(db, "dx_submitted", booking, background_tasks, actor=user)


def _next_booking_code(db: Session) -> str:
    """Sinh mã DX kế tiếp — BỀN với mã lẫn chữ.

    `core.utils.generate_code` sắp theo chuỗi giảm dần rồi `int(code[2:])`; dữ liệu
    demo có mã kiểu `DXTC10` (chữ sắp cao hơn số) làm nó rơi về `DX001` → trùng khóa.
    Ở đây chỉ xét mã đúng dạng `DX<số>`, lấy số lớn nhất + 1, và nhảy tiếp nếu đụng.
    """
    rows = db.query(VehicleBooking.code).filter(VehicleBooking.code.like("DX%")).all()
    existing = {code for (code,) in rows if code}
    max_num = 0
    for code in existing:
        m = re.fullmatch(r"DX(\d+)", code)
        if m:
            max_num = max(max_num, int(m.group(1)))
    num = max_num + 1
    while f"DX{num:03d}" in existing:
        num += 1
    return f"DX{num:03d}"


def create_booking(db: Session, data: VehicleBookingCreate, user, submit: bool,
                   background_tasks=None) -> VehicleBooking:
    """Tạo phiếu đặt xe. `submit=True` → gửi duyệt ngay (Chờ duyệt); ngược lại lưu Nháp.

    Phạm vi (phòng ban / công ty) auto-fill từ hồ sơ người tạo khi client bỏ trống, để
    `apply_scope` lọc đúng theo pháp nhân/bộ phận. Điểm dừng lưu chuỗi JSON, giữ thứ tự.
    """
    if not (data.purpose or "").strip():
        raise HTTPException(400, "Mục đích không được để trống")

    req_type = _normalize_type(data.request_type)
    name, dept_id, company_id = _requester_context(db, user)

    booking = VehicleBooking(
        request_type=req_type,
        purpose=data.purpose.strip(),
        is_self_drive=bool(data.is_self_drive),
        license_number=(data.license_number or "").strip(),
        license_class=(data.license_class or "").strip(),
        start_location=data.start_location or "",
        end_location=data.end_location or "",
        stops=_dump_stops(data.stops),
        start_time=data.start_time or "",
        end_time=data.end_time or "",
        # Khối riêng đặt xe công tác
        passenger_count=data.passenger_count or 1,
        attendees=data.attendees or "",
        contact_phone=data.contact_phone or "",
        is_round_trip=bool(data.is_round_trip),
        # Khối riêng giao hàng
        goods_name=data.goods_name or "",
        goods_size=data.goods_size or "",
        sender_name=data.sender_name or "",
        sender_phone=data.sender_phone or "",
        receiver_name=data.receiver_name or "",
        receiver_phone=data.receiver_phone or "",
        special_instructions=data.special_instructions or "",
        # Người tạo + phạm vi
        requester=name,
        requester_id=getattr(user, "id", 0),
        department_id=data.department_id or dept_id,
        company_id=data.company_id or company_id,
        first_approver_id=data.first_approver_id or 0,
        status=BK_PENDING if submit else BK_DRAFT,
        note=data.note or "",
        created_by=getattr(user, "id", 0),
        updated_by=getattr(user, "id", 0),
    )
    db.add(booking)
    db.flush()  # có id để sinh mã
    booking.code = _next_booking_code(db)
    db.commit()
    db.refresh(booking)
    if submit:
        _after_submit(db, booking, user, background_tasks)
    return booking


def update_booking(db: Session, booking: VehicleBooking, data: VehicleBookingUpdate,
                   user, submit: bool, background_tasks=None) -> VehicleBooking:
    """Sửa phiếu — CHỈ khi còn Nháp hoặc bị trả về (A07). Sau khi vào luồng thì khóa.

    `submit=True` chuyển tiếp sang Chờ duyệt sau khi lưu.
    """
    if booking.status not in EDITABLE_STATUSES:
        raise HTTPException(400, "Phiếu đã vào luồng duyệt/điều phối — không sửa được nữa")

    patch = data.model_dump(exclude_unset=True)
    if "request_type" in patch:
        booking.request_type = _normalize_type(patch.pop("request_type"))
    if "stops" in patch:
        patch.pop("stops")  # dump từ đối tượng StopItem đã validate, không từ dict thô
        booking.stops = _dump_stops(data.stops or [])
    for field, value in patch.items():
        setattr(booking, field, value)

    became_pending = submit and booking.status != BK_PENDING
    if submit:
        booking.status = BK_PENDING
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    if became_pending:
        _after_submit(db, booking, user, background_tasks)
    return booking


# --- Điều phối -------------------------------------------------------------

# Phiếu đã kết thúc thì không điều phối được nữa.
_CLOSED_STATUSES = (BK_CANCELLED, BK_REJECTED, BK_COMPLETED)

# Trạng thái tài xế còn "giữ chỗ" khung giờ (chưa hủy/hoàn tất) — dùng để chống trùng.
_ACTIVE_DRV_STATUSES = (DRV_WAITING, DRV_ACCEPTED, DRV_ONGOING)


def _overlaps(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    """Hai khung giờ có GIAO nhau không (so chuỗi ISO cùng khuôn 'YYYY-MM-DDTHH:MM').

    Thiếu bất kỳ mốc nào → coi như không kết luận được trùng (bỏ qua). Giáp ranh
    (kết thúc == bắt đầu) KHÔNG tính là trùng.
    """
    if not (a_start and a_end and b_start and b_end):
        return False
    return a_start < b_end and b_start < a_end


def _find_time_conflict(db: Session, booking: VehicleBooking, vehicle_id: int, driver_id: int):
    """Xe/tài xế được chọn có chuyến khác TRÙNG khung giờ đang còn hiệu lực không.

    Trả `(phiếu_trùng, "Xe"|"Tài xế")` nếu có, ngược lại `None`. Chỉ xét phiếu đang
    Điều phối và tài xế chưa hủy/hoàn tất; bỏ chính phiếu đang điều phối.
    """
    if not (booking.start_time and booking.end_time):
        return None
    #  Tự lái không có tài xế (driver_id = 0) → CHỈ chống trùng theo XE, nếu không
    #  mọi chuyến tự lái (đều driver_id 0) sẽ báo trùng tài xế lẫn nhau.
    same = [VehicleBooking.assigned_vehicle_id == vehicle_id]
    if driver_id:
        same.append(VehicleBooking.assigned_driver_id == driver_id)
    others = (
        db.query(VehicleBooking)
        .filter(
            VehicleBooking.id != booking.id,
            VehicleBooking.is_deleted == False,  # noqa: E712
            VehicleBooking.status == BK_DISPATCHED,
            VehicleBooking.driver_status.in_(_ACTIVE_DRV_STATUSES),
            or_(*same),
        )
        .all()
    )
    for other in others:
        if _overlaps(booking.start_time, booking.end_time, other.start_time, other.end_time):
            which = "Xe" if other.assigned_vehicle_id == vehicle_id else "Tài xế"
            return other, which
    return None


def dispatch_booking(db: Session, booking: VehicleBooking, data: DispatchIn, user,
                     background_tasks=None) -> VehicleBooking:
    """Gán 1 xe + 1 tài xế cho phiếu → chuyển sang Điều phối, tài xế Chờ nhận."""
    if booking.status in _CLOSED_STATUSES:
        raise HTTPException(400, "Phiếu đã kết thúc — không điều phối được")

    vehicle = db.get(Vehicle, data.assigned_vehicle_id)
    if vehicle is None:
        raise HTTPException(400, "Xe được chọn không tồn tại")

    #  Tự lái: điều phối viên CHỈ gán xe; người yêu cầu là tài xế (không chọn tài xế).
    if booking.is_self_drive:
        driver = None
    else:
        driver = db.get(Driver, data.assigned_driver_id)
        if driver is None:
            raise HTTPException(400, "Tài xế được chọn không tồn tại")

    #  Chống trùng giờ: 1 xe / 1 tài xế không nhận 2 chuyến chồng khung giờ.
    conflict = _find_time_conflict(db, booking, vehicle.id, driver.id if driver else 0)
    if conflict is not None:
        other, which = conflict
        raise HTTPException(
            400,
            f"{which} đã có chuyến {other.code} trùng khung giờ "
            f"({other.start_time} → {other.end_time}). Chọn xe/tài xế khác hoặc đổi giờ.",
        )

    booking.assigned_vehicle_id = vehicle.id
    booking.assigned_driver_id = driver.id if driver else 0
    booking.dispatched_by = getattr(user, "id", 0)
    booking.dispatched_at = datetime.now().isoformat(timespec="seconds")
    booking.status = BK_DISPATCHED
    booking.driver_status = DRV_WAITING
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    notify(db, "dx_dispatched", booking, background_tasks, actor=user)
    return booking


def filter_my_trips(query, db: Session, user):
    """Lọc còn CHUYẾN ĐƯỢC PHÂN CHO CHÍNH người đang xem (màn "Chuyến của tôi").

    Khác phạm vi `assigned` (còn gồm phiếu mình TẠO): ở đây chỉ chuyến mà mình là
    TÀI XẾ được phân. Không có hồ sơ tài xế nối tài khoản → rỗng (điều kiện không
    bao giờ khớp), thay vì trả cả danh sách.
    """
    uid = getattr(user, "id", 0)
    my_driver = db.query(Driver).filter(Driver.user_id == uid).first()
    driver_id = my_driver.id if my_driver else -1
    #  Chuyến của tôi = được phân cho tài xế của tôi HOẶC chuyến TỰ LÁI của chính tôi.
    return query.filter(
        or_(
            VehicleBooking.assigned_driver_id == driver_id,
            and_(VehicleBooking.is_self_drive == True, VehicleBooking.requester_id == uid),  # noqa: E712
        )
    )


# --- Nguồn tài xế khi điều phối (lọc theo vai trò) -------------------------

def my_driver_profile(db: Session, user) -> dict | None:
    """Hồ sơ tài xế của CHÍNH người đang đăng nhập (để tự lái tự điền GPLX), `None`
    nếu họ chưa phải tài xế."""
    d = db.query(Driver).filter(Driver.user_id == getattr(user, "id", 0)).first()
    if d is None:
        return None
    return {"id": d.id, "name": d.name,
            "license_number": d.license_number, "license_class": d.license_class}


def drivers_for_dispatch(db: Session) -> list[dict]:
    """Danh sách tài xế để ĐIỀU PHỐI — chỉ người thật sự là tài xế.

    Gồm: tài xế **thuê ngoài** (không có tài khoản → luôn hiện) + tài xế **nội bộ
    ĐANG GIỮ vai trò `booking_driver`**. Loại bỏ hồ sơ tài xế nội bộ gắn tài khoản
    KHÔNG có vai trò Tài xế (lỡ tạo) — để ô chọn lúc điều phối không hiện nhầm.
    Danh mục Tài xế (màn quản lý) vẫn hiện hết; lọc này CHỈ cho ô điều phối.
    """
    from app.modules.notification.service import get_users_by_role_codes

    driver_user_ids = {u.id for u in get_users_by_role_codes(db, ["booking_driver"])}
    rows = db.query(Driver).order_by(Driver.name.asc()).all()
    out: list[dict] = []
    for d in rows:
        if d.is_external or (d.user_id and d.user_id in driver_user_ids):
            out.append(DriverResponse.model_validate(d).model_dump())
    return out


# --- Chuyển trạng thái theo vai trò ----------------------------------------

def _now() -> str:
    """Mốc thời gian ISO tới phút, cùng khuôn với start_time/end_time đang lưu."""
    return datetime.now().isoformat(timespec="minutes")


def _append_note(booking: VehicleBooking, label: str, reason: str) -> None:
    """Ghi thêm một dòng lý do vào ô ghi chú, giữ lịch sử các lần trả/từ chối."""
    reason = (reason or "").strip()
    if not reason:
        return
    line = f"[{label}] {reason}"
    booking.note = f"{booking.note}\n{line}".strip() if booking.note else line


# --- Người duyệt (quyền `approve`) ---

def approve_booking(db: Session, booking: VehicleBooking, user,
                    background_tasks=None) -> VehicleBooking:
    """Người duyệt CHẤP NHẬN phiếu Chờ duyệt → Đã duyệt (chờ điều phối)."""
    if booking.status != BK_PENDING:
        raise HTTPException(400, "Chỉ duyệt được phiếu đang Chờ duyệt")
    booking.status = BK_APPROVED
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    #  Báo Điều phối viên "có chuyến cần điều phối" + Người tạo "đã duyệt" (2 mẫu khác nhau).
    notify_approved(db, booking, background_tasks, actor=user)
    return booking


def return_booking(db: Session, booking: VehicleBooking, data: ReasonIn, user,
                   background_tasks=None) -> VehicleBooking:
    """Người duyệt YÊU CẦU CHỈNH SỬA: trả phiếu về người tạo sửa lại rồi gửi lại."""
    if booking.status != BK_PENDING:
        raise HTTPException(400, "Chỉ trả lại được phiếu đang Chờ duyệt")
    booking.status = BK_RETURNED
    _append_note(booking, "Yêu cầu chỉnh sửa", data.reason)
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    notify(db, "dx_returned", booking, background_tasks, actor=user, reason=data.reason)
    return booking


def reject_booking(db: Session, booking: VehicleBooking, data: ReasonIn, user,
                   background_tasks=None) -> VehicleBooking:
    """Người duyệt TỪ CHỐI: khóa phiếu, không đi tiếp luồng."""
    if booking.status != BK_PENDING:
        raise HTTPException(400, "Chỉ từ chối được phiếu đang Chờ duyệt")
    booking.status = BK_REJECTED
    _append_note(booking, "Từ chối", data.reason)
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    notify(db, "dx_rejected", booking, background_tasks, actor=user, reason=data.reason)
    return booking


# --- Tài xế (quyền `write` + đúng tài xế được phân) ---

def _ensure_can_drive(db: Session, booking: VehicleBooking, user) -> None:
    """Chỉ ĐÚNG tài xế được phân mới thao tác được chuyến của mình.

    Người KHÔNG phải tài xế (điều phối viên / admin — không có hồ sơ tài xế nối tài
    khoản) được thao tác thay khi cần (tài xế báo qua điện thoại). Còn ai đã là tài
    xế thì chỉ đụng vào chuyến được phân cho chính mình.
    """
    #  Tự lái: chính NGƯỜI YÊU CẦU là tài xế; người không có hồ sơ tài xế (admin/
    #  điều phối) được thao tác thay.
    if booking.is_self_drive:
        if booking.requester_id and booking.requester_id == getattr(user, "id", 0):
            return
        my_driver = db.query(Driver).filter(Driver.user_id == getattr(user, "id", 0)).first()
        if my_driver is None:
            return
        raise HTTPException(403, "Chuyến tự lái — chỉ người yêu cầu (hoặc quản trị) mới thao tác")

    my_driver = db.query(Driver).filter(Driver.user_id == getattr(user, "id", 0)).first()
    if my_driver is None:
        return
    if booking.assigned_driver_id != my_driver.id:
        raise HTTPException(403, "Bạn không phải tài xế được phân cho chuyến này")


def driver_accept(db: Session, booking: VehicleBooking, user,
                  background_tasks=None) -> VehicleBooking:
    """Tài xế CHẤP NHẬN chuyến được phân (Chờ tài xế / Đã từ chối lại → Đã nhận)."""
    _ensure_can_drive(db, booking, user)
    if booking.status != BK_DISPATCHED or booking.driver_status not in (DRV_WAITING, DRV_REJECTED):
        raise HTTPException(400, "Chuyến chưa ở trạng thái chờ tài xế nhận")
    booking.driver_status = DRV_ACCEPTED
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    notify(db, "dx_driver_accepted", booking, background_tasks, actor=user)
    return booking


def driver_reject(db: Session, booking: VehicleBooking, data: ReasonIn, user,
                  background_tasks=None) -> VehicleBooking:
    """Tài xế TỪ CHỐI chuyến → quay về điều phối (điều phối viên phân lại)."""
    _ensure_can_drive(db, booking, user)
    if booking.status != BK_DISPATCHED or booking.driver_status not in (DRV_WAITING, DRV_ACCEPTED):
        raise HTTPException(400, "Chuyến không ở trạng thái tài xế từ chối được")
    booking.driver_status = DRV_REJECTED
    _append_note(booking, "Tài xế từ chối", data.reason)
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    notify(db, "dx_driver_rejected", booking, background_tasks, actor=user, reason=data.reason)
    return booking


def driver_start(db: Session, booking: VehicleBooking, user) -> VehicleBooking:
    """Tài xế BẮT ĐẦU chuyến (Đã nhận → Đang đi), chấm mốc giờ đi thực tế."""
    _ensure_can_drive(db, booking, user)
    if booking.driver_status != DRV_ACCEPTED:
        raise HTTPException(400, "Chỉ bắt đầu được chuyến tài xế đã nhận")
    booking.driver_status = DRV_ONGOING
    booking.actual_start_time = _now()
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    return booking


def driver_complete(db: Session, booking: VehicleBooking, data: CompleteIn, user,
                    background_tasks=None) -> VehicleBooking:
    """Tài xế HOÀN TẤT chuyến (Đang đi → Hoàn thành), chấm giờ về + km + chi phí."""
    _ensure_can_drive(db, booking, user)
    if booking.driver_status != DRV_ONGOING:
        raise HTTPException(400, "Chỉ hoàn tất được chuyến đang đi")
    booking.driver_status = DRV_COMPLETED
    booking.status = BK_COMPLETED
    booking.actual_end_time = _now()
    if data.distance_km is not None:
        booking.distance_km = data.distance_km
    if data.cost is not None:
        booking.cost = data.cost
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    notify_completed(db, booking, background_tasks, actor=user)
    return booking


# --- Nối nhãn xe / tài xế khi trả API --------------------------------------

def _vehicle_label(vehicle) -> str:
    if not vehicle:
        return ""
    return vehicle.license_plate + (f" — {vehicle.model}" if vehicle.model else "")


def _is_assigned_driver(db: Session, obj: VehicleBooking, viewer) -> bool:
    """Người đang xem có phải TÀI XẾ ĐƯỢC PHÂN cho phiếu này không.

    Tự lái: người yêu cầu chính là tài xế. Có tài xế: nối qua `Driver.user_id`.
    """
    if viewer is None:
        return False
    if obj.is_self_drive:
        return bool(obj.requester_id and obj.requester_id == getattr(viewer, "id", 0))
    if not obj.assigned_driver_id:
        return False
    driver = db.get(Driver, obj.assigned_driver_id)
    return bool(driver and driver.user_id and driver.user_id == getattr(viewer, "id", 0))


def serialize_booking(db: Session, obj: VehicleBooking, viewer=None) -> dict:
    """Một phiếu → dict, đã nối nhãn xe/tài xế được phân (nếu có).

    `viewer` (người đang gọi API) để tính cờ `is_assigned_driver` — frontend dựa vào
    đó bày nhóm nút của tài xế đúng người.
    """
    out = VehicleBookingResponse.model_validate(obj)
    if obj.assigned_vehicle_id:
        out.assigned_vehicle_label = _vehicle_label(db.get(Vehicle, obj.assigned_vehicle_id))
    if obj.assigned_driver_id:
        driver = db.get(Driver, obj.assigned_driver_id)
        out.assigned_driver_label = driver.name if driver else ""
    elif obj.is_self_drive:
        out.assigned_driver_label = f"{obj.requester} (tự lái)" if obj.requester else "Tự lái"
    out.is_assigned_driver = _is_assigned_driver(db, obj, viewer)
    #  Có phiên duyệt nhiều bước đang chạy? → frontend ẩn nút duyệt một bước.
    from .approval_bridge import running_instance
    out.approval_running = running_instance(db, obj.id) is not None
    return out.model_dump()


def serialize_bookings(db: Session, objs: list[VehicleBooking]) -> list[dict]:
    """Danh sách phiếu → list dict, nối nhãn xe/tài xế theo LÔ (tránh N+1)."""
    veh_ids = {o.assigned_vehicle_id for o in objs if o.assigned_vehicle_id}
    drv_ids = {o.assigned_driver_id for o in objs if o.assigned_driver_id}
    veh_map = (
        {v.id: v for v in db.query(Vehicle).filter(Vehicle.id.in_(veh_ids)).all()}
        if veh_ids else {}
    )
    drv_map = (
        {d.id: d for d in db.query(Driver).filter(Driver.id.in_(drv_ids)).all()}
        if drv_ids else {}
    )
    result = []
    for o in objs:
        out = VehicleBookingResponse.model_validate(o)
        out.assigned_vehicle_label = _vehicle_label(veh_map.get(o.assigned_vehicle_id))
        driver = drv_map.get(o.assigned_driver_id)
        if driver:
            out.assigned_driver_label = driver.name
        elif o.is_self_drive:
            out.assigned_driver_label = f"{o.requester} (tự lái)" if o.requester else "Tự lái"
        result.append(out.model_dump())
    return result
