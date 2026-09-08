"""NGHIỆP VỤ ĐẶT PHÒNG HỌP — lập, sửa, gửi duyệt, hủy.

Ba luật đặt ở đây và chỉ ở đây:

1. **Chặn trùng** — một phòng, một khung giờ, một phiếu. Xem `check_conflict`.
2. **Giữ phòng ngay khi GỬI DUYỆT**, không đợi tới lúc duyệt xong
   (`BLOCKING_STATUSES` — xem `constants.py`).
3. **Sức chứa** — đặt 30 người vào phòng 8 chỗ thì chặn, vì đó là sai thật chứ
   không phải sở thích.

Chốt "nhập đủ" đặt ở lúc **GỬI DUYỆT**, không phải lúc lưu nháp — cùng luật với
`leave/request_service.py` và với `required-fields.ts` của Thu mua.
"""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.utils import generate_code
from app.modules.employee.model import Employee

from .constants import (BLOCKING_STATUSES, EDITABLE_STATUSES, RB_APPROVED,
                        RB_CANCELLED, RB_DRAFT, RB_PENDING, RB_REJECTED)
from .model import MeetingRoom, RoomBooking, RoomBookingAttendee

#  Bộ lọc danh sách (whitelist của `apply_filters`).
FILTERABLE = ["status", "room_id", "company_id", "department_id",
              "requester_employee_id"]
SEARCH_FIELDS = ("code", "title", "purpose")

CODE_PREFIX = "PH"

#  Trần một lượt đặt. Phòng họp giữ liên tục quá một ngày thì gần như luôn là gõ
#  nhầm ngày (chọn 05/09 thay vì 04/09), và cái giá của việc gõ nhầm là cả phòng
#  bị khóa suốt tuần mà không ai hiểu vì sao.
MAX_HOURS_PER_BOOKING = 24


def apply_keyword_search(query, keyword: str | None):
    kw = (keyword or "").strip()
    if not kw:
        return query
    like = f"%{kw}%"
    return query.filter(or_(*[getattr(RoomBooking, f).like(like) for f in SEARCH_FIELDS]))


# ── Tra cứu nền ────────────────────────────────────────────────────────────────

def get_room(db: Session, room_id: int) -> MeetingRoom:
    room = db.get(MeetingRoom, room_id)
    if room is None or not room.is_active:
        raise HTTPException(400, "Phòng họp không tồn tại hoặc đã ngừng dùng")
    return room


def get_employee(db: Session, employee_id: int) -> Employee:
    emp = db.get(Employee, employee_id)
    if emp is None:
        raise HTTPException(400, "Không tìm thấy hồ sơ nhân sự của người đặt")
    return emp


def resolve_requester(db: Session, user, employee_id: int) -> Employee:
    """Người ĐẶT: lấy theo ô trên phiếu, bỏ trống thì là chính người đang lập."""
    target = employee_id or getattr(user, "employee_id", 0) or 0
    if not target:
        raise HTTPException(
            400, "Chưa xác định được người đặt — tài khoản này chưa gắn hồ sơ nhân sự.")
    return get_employee(db, target)


# ── Kiểm tra phiếu ─────────────────────────────────────────────────────────────

def check_time_range(start_at: datetime, end_at: datetime) -> None:
    if end_at <= start_at:
        raise HTTPException(400, "«Giờ kết thúc» phải sau «Giờ bắt đầu»")
    if end_at - start_at > timedelta(hours=MAX_HOURS_PER_BOOKING):
        raise HTTPException(
            400, f"Một lượt đặt tối đa {MAX_HOURS_PER_BOOKING} giờ. "
                 "Kiểm tra lại ngày — thường là chọn nhầm sang ngày hôm sau.")


def check_capacity(room: MeetingRoom, attendee_count: int) -> None:
    """Sức chứa `0` = CHƯA KHAI, không phải "không chứa được ai" nên bỏ qua."""
    if room.capacity and attendee_count and attendee_count > room.capacity:
        raise HTTPException(
            400, f"«{room.name}» chứa được {room.capacity} người, phiếu này ghi "
                 f"{attendee_count} người. Chọn phòng lớn hơn hoặc sửa lại số người.")


def find_conflict(db: Session, room_id: int, start_at: datetime, end_at: datetime,
                  exclude_id: int = 0, lock: bool = False) -> RoomBooking | None:
    """Phiếu đang GIỮ phòng này chồng lên khoảng giờ đang xét — `None` nếu trống.

    Hai khoảng chồng nhau khi `start < other.end` VÀ `end > other.start`. Dấu so
    sánh là **nghiêm ngặt** ở cả hai vế, có chủ ý: họp 9-10h và họp 10-11h KHÔNG
    chồng nhau, đó là hai cuộc nối tiếp và đây là cách người ta xếp lịch thật.
    Dùng `<=` thì không ai đặt được ca liền sau.

    Chỉ xét phiếu còn GIỮ phòng (`BLOCKING_STATUSES`) — nháp, đã hủy, bị từ chối
    thì không tính.
    """
    q = (db.query(RoomBooking)
         .filter(RoomBooking.room_id == room_id,
                 RoomBooking.is_deleted.is_(False),
                 RoomBooking.status.in_(BLOCKING_STATUSES),
                 RoomBooking.start_at < end_at,
                 RoomBooking.end_at > start_at))
    if exclude_id:
        q = q.filter(RoomBooking.id != exclude_id)
    if lock:
        #  ⚠️ ĐỌC CÓ KHOÁ ở nhịp giữ chỗ, không phải đọc thường.
        #
        #  MySQL chạy **REPEATABLE READ**: giao dịch đã mở thì mọi câu `SELECT`
        #  thường đều đọc BẢN CHỤP lúc câu đầu tiên chạy, nên phiếu do người khác
        #  vừa commit xong KHÔNG hiện ra. Đo được ngày 04/09/2026: bắn 10 lệnh
        #  gửi duyệt song song thì 6 lệnh vẫn lọt dù đã khoá hàng phòng — mỗi
        #  lệnh nhìn thấy một thế giới cũ. `SELECT … FOR UPDATE` bỏ qua bản chụp
        #  và đọc bản mới nhất, nên đây là vế thứ hai không thể thiếu của chốt.
        q = q.with_for_update()
    return q.order_by(RoomBooking.start_at).first()


def check_conflict(db: Session, room: MeetingRoom, start_at: datetime,
                   end_at: datetime, exclude_id: int = 0, lock: bool = False) -> None:
    """Chặn đặt đôi. Câu báo phải nói RÕ ai đang giữ và giữ tới mấy giờ.

    Không có thông tin đó thì người bị chặn chỉ biết "không đặt được" rồi đi hỏi
    vòng quanh — mà thứ họ cần là biết nên xin lại phòng của ai, hoặc dời sang
    khung giờ nào.
    """
    other = find_conflict(db, room.id, start_at, end_at, exclude_id, lock=lock)
    if other is None:
        return
    raise HTTPException(
        400, f"«{room.name}» đã có phiếu {other.code} giữ từ "
             f"{other.start_at:%H:%M %d/%m} đến {other.end_at:%H:%M %d/%m} "
             f"({'đã duyệt' if other.status == RB_APPROVED else 'đang chờ duyệt'}). "
             "Chọn phòng khác hoặc dời giờ.")


# ── Tạo · sửa · xóa ────────────────────────────────────────────────────────────

def _replace_attendees(db: Session, booking_id: int, items, actor: int) -> None:
    """Ghi đè danh sách người dự. Xóa hết rồi thêm lại — danh sách ngắn nên so
    từng dòng để sửa tại chỗ chỉ tổ phức tạp mà không nhanh hơn.

    ⚠️ **Chỉ nhận nhân sự CÓ THẬT.** Id bịa lọt vào thì danh sách người dự hiện
    một dòng «#999999» không tên, không ai gỡ được vì không biết nó là ai, và
    thư mời thì lặng lẽ bỏ qua nó (nhân sự không tồn tại → không có tài khoản).
    Đo được ngày 04/09/2026 bằng một lệnh gọi API thẳng.
    """
    (db.query(RoomBookingAttendee)
     .filter(RoomBookingAttendee.booking_id == booking_id).delete())

    wanted_ids = {i.employee_id for i in (items or []) if i.employee_id}
    existing_ids = {
        row[0] for row in
        db.query(Employee.id).filter(Employee.id.in_(wanted_ids)).all()
    } if wanted_ids else set()

    seen: set[int] = set()
    for i, item in enumerate(items or []):
        #  Mời trùng một người hai lần thì họ nhận hai thông báo giống hệt nhau.
        if not item.employee_id or item.employee_id in seen:
            continue
        if item.employee_id not in existing_ids:
            continue
        seen.add(item.employee_id)
        db.add(RoomBookingAttendee(
            booking_id=booking_id, employee_id=item.employee_id,
            role=(item.role or "")[:100], sort_order=i,
            created_by=actor, updated_by=actor))


def create(db: Session, data, user) -> RoomBooking:
    """Lập phiếu — luôn ở **Nháp**. Gửi duyệt là một bước riêng.

    ⚠️ Nháp **KHÔNG kiểm trùng**: nó chưa giữ phòng gì cả, và chặn ở đây là bắt
    người dùng phải chọn xong phòng + giờ đúng ngay trong một lần gõ. Cảnh báo
    sớm là việc của `/availability`; chốt chặn thật nằm ở bước gửi duyệt.
    """
    requester = resolve_requester(db, user, data.requester_employee_id)
    room = get_room(db, data.room_id)
    check_time_range(data.start_at, data.end_at)
    check_capacity(room, data.attendee_count)

    obj = RoomBooking(
        code=generate_code(db, RoomBooking, CODE_PREFIX),
        room_id=room.id,
        company_id=requester.company_id or 0,
        department_id=requester.department_id or 0,
        requester_employee_id=requester.id,
        title=(data.title or "").strip()[:255],
        purpose=(data.purpose or "").strip(),
        start_at=data.start_at, end_at=data.end_at,
        attendee_count=data.attendee_count or 0,
        status=RB_DRAFT,
        created_by=user.id, updated_by=user.id,
    )
    db.add(obj)
    db.flush()
    _replace_attendees(db, obj.id, data.attendees, user.id)
    db.commit()
    db.refresh(obj)
    return obj


def check_editable(obj: RoomBooking) -> None:
    if obj.status not in EDITABLE_STATUSES:
        raise HTTPException(
            400, "Phiếu đã gửi duyệt nên không sửa được. Hủy phiếu rồi đặt lại nếu "
                 "cần đổi phòng hoặc đổi giờ.")


def update(db: Session, obj: RoomBooking, data, user) -> RoomBooking:
    check_editable(obj)
    values = data.model_dump(exclude_unset=True)
    #  Lấy danh sách người dự từ CHÍNH đối tượng Pydantic, không lấy bản dump:
    #  bản dump biến `AttendeeItem` thành `dict`, mà `_replace_attendees` đọc
    #  bằng thuộc tính. Cờ "có gửi lên hay không" thì vẫn hỏi bản dump — `None`
    #  là giá trị hợp lệ, không phân biệt được với "không gửi".
    has_attendees = "attendees" in values
    values.pop("attendees", None)
    attendees = data.attendees if has_attendees else None

    requester = (resolve_requester(db, user, values["requester_employee_id"])
                 if "requester_employee_id" in values
                 else get_employee(db, obj.requester_employee_id))
    room = get_room(db, values.get("room_id", obj.room_id))
    start_at = values.get("start_at", obj.start_at)
    end_at = values.get("end_at", obj.end_at)
    check_time_range(start_at, end_at)
    check_capacity(room, values.get("attendee_count", obj.attendee_count))

    for key, value in values.items():
        setattr(obj, key, value)
    obj.room_id = room.id
    obj.requester_employee_id = requester.id
    obj.company_id = requester.company_id or 0
    obj.department_id = requester.department_id or 0
    obj.updated_by = user.id

    if has_attendees:
        _replace_attendees(db, obj.id, attendees, user.id)
    db.commit()
    db.refresh(obj)
    return obj


def reschedule(db: Session, obj: RoomBooking, room_id: int, start_at: datetime,
               end_at: datetime, user) -> RoomBooking:
    """DỜI GIỜ / ĐỔI PHÒNG — đường của thao tác kéo thả trên lịch.

    ⚠️ **Cố ý KHÔNG gọi `check_editable`.** Lịch chỉ vẽ phiếu đang GIỮ phòng
    (`BLOCKING_STATUSES`), tức mọi khối kéo được đều là *Chờ duyệt* hoặc *Đã
    duyệt* — hai trạng thái mà `check_editable` chặn. Gác bằng chốt đó thì tính
    năng kéo thả không dùng được lấy một lần. Đổi lại, đường này chỉ cho đụng vào
    **phòng và giờ**; nội dung, người dự, số người vẫn phải mở phiếu ra sửa.

    Phiếu đã kết thúc (bị từ chối / đã hủy) thì không dời: nó đã nhả phòng, dời
    nó chỉ đẻ ra một cuộc họp ma không ai giữ chỗ cho.

    Trạng thái **giữ nguyên** sau khi dời — dời một phiếu đã duyệt không bắt đi
    duyệt lại. Đó là lựa chọn nghiệp vụ: người kéo phải có quyền `write` trên
    phiếu, và người dự được báo lại (xem `notify_attendees(..., moved=True)`).
    """
    if obj.status in (RB_REJECTED, RB_CANCELLED):
        raise HTTPException(
            400, "Phiếu đã hủy hoặc bị từ chối thì không dời được. "
                 "Muốn họp lại thì lập phiếu mới.")

    check_time_range(start_at, end_at)
    target_id = room_id or obj.room_id

    if obj.status in BLOCKING_STATUSES:
        #  Cùng nhịp và cùng lý do với `reserve_slot`: thoát bản chụp
        #  REPEATABLE READ, khoá hàng phòng, rồi mới kiểm trùng. Thiếu một trong
        #  hai thì hai người kéo hai phiếu vào cùng một khung giờ đều lọt.
        db.rollback()
        room = (db.query(MeetingRoom)
                .filter(MeetingRoom.id == target_id)
                .with_for_update()
                .first())
        if room is None or not room.is_active:
            raise HTTPException(400, "Phòng họp không tồn tại hoặc đã ngừng dùng")
        db.refresh(obj)
        check_capacity(room, obj.attendee_count)
        check_conflict(db, room, start_at, end_at, exclude_id=obj.id, lock=True)
    else:
        room = get_room(db, target_id)
        check_capacity(room, obj.attendee_count)

    obj.room_id = room.id
    obj.start_at = start_at
    obj.end_at = end_at
    obj.updated_by = user.id
    db.commit()
    db.refresh(obj)
    return obj


def soft_delete(db: Session, obj: RoomBooking, user) -> None:
    """Xóa mềm. Chỉ phiếu chưa vào luồng — phiếu đã duyệt phải HỦY chứ không xóa."""
    check_editable(obj)
    obj.is_deleted = True
    obj.updated_by = user.id
    db.commit()


# ── Gửi duyệt · hủy ────────────────────────────────────────────────────────────

def check_ready_to_submit(obj: RoomBooking) -> None:
    """Chốt "nhập đủ" — đặt ở lúc GỬI, không phải lúc lưu nháp.

    Người duyệt mở phiếu ra mà không có tiêu đề cuộc họp thì họ duyệt cái gì.
    """
    if not (obj.title or "").strip():
        raise HTTPException(400, "Thiếu «Nội dung cuộc họp» — nhập đủ trước khi gửi duyệt.")


def prepare_submit(db: Session, obj: RoomBooking, user) -> MeetingRoom:
    """Những chốt RẺ của bước gửi duyệt — kiểm trước khi đụng vào khoá và bộ máy.

    Tách khỏi `reserve_slot` để hỏng vì thiếu tiêu đề hay sai giờ thì không phải
    đi qua khoá hàng phòng: đó là những lỗi của riêng tờ phiếu, không liên quan
    tới ai đang giữ phòng.
    """
    if obj.status not in EDITABLE_STATUSES:
        raise HTTPException(400, "Phiếu này đã gửi duyệt rồi")
    check_ready_to_submit(obj)

    room = get_room(db, obj.room_id)
    check_time_range(obj.start_at, obj.end_at)
    check_capacity(room, obj.attendee_count)
    return room


def reserve_slot(db: Session, obj: RoomBooking, user) -> RoomBooking:
    """GIỮ CHỖ: khoá phòng → kiểm trùng → đặt phiếu vào *Chờ duyệt*, một nhịp.

    ⚠️ **`with_for_update()` trên hàng PHÒNG không được bỏ.** Chốt chặn trùng là
    một câu `SELECT` rồi mới ghi, nên nhiều lệnh gửi duyệt **song song** cho cùng
    một phòng đều thấy "chưa ai giữ" rồi cùng ghi. Đo được ngày 04/09/2026: bắn
    5 lệnh cùng lúc cho Hội trường 501 khung 14:00–15:00 thì **cả 5 đều lọt** —
    năm cuộc họp chung một phòng, và không có ràng buộc nào ở tầng dữ liệu cứu
    được (khoảng thời gian chồng nhau không diễn tả nổi bằng unique index).
    Khoá hàng phòng bắt mọi lệnh của CÙNG một phòng xếp hàng; phòng khác vẫn
    chạy song song bình thường.

    Đặt trạng thái và commit ngay trong nhịp này, TRƯỚC khi trình bộ máy duyệt:
    khoá chỉ giữ tới lúc commit, nên nếu để việc ghi trạng thái ở sau lượt gọi
    sang bộ máy thì cửa sổ đua mở lại đúng bằng quãng đó.
    """
    #  ⚠️ Kết thúc giao dịch đang mở TRƯỚC khi khoá. Đường này đã đọc vài câu ở
    #  bước trước (lấy phiếu, lấy phòng), nên dưới REPEATABLE READ của MySQL thì
    #  bản chụp dữ liệu đã bị ghim từ câu đầu tiên — kiểm trùng trên bản chụp đó
    #  là kiểm một thế giới cũ. Ở đây chưa có gì để mất: cả nhánh mới chỉ đọc.
    db.rollback()

    room = (db.query(MeetingRoom)
            .filter(MeetingRoom.id == obj.room_id)
            .with_for_update()
            .first())
    if room is None or not room.is_active:
        raise HTTPException(400, "Phòng họp không tồn tại hoặc đã ngừng dùng")

    #  Phiếu nằm nháp cả tuần thì trong tuần đó người khác đã có thể giữ mất
    #  phòng — và `lock=True` để câu này đọc bản MỚI NHẤT, không phải bản chụp.
    db.refresh(obj)
    check_conflict(db, room, obj.start_at, obj.end_at, exclude_id=obj.id, lock=True)

    obj.status = RB_PENDING
    obj.submitted_at = datetime.now()
    obj.decision_note = ""
    obj.updated_by = user.id
    db.commit()
    db.refresh(obj)
    return obj


def attach_instance(db: Session, obj: RoomBooking, instance_id: int) -> RoomBooking:
    """Gắn phiên duyệt vào phiếu đã giữ chỗ."""
    obj.approval_instance_id = instance_id
    db.commit()
    db.refresh(obj)
    return obj


def rollback_to_draft(db: Session, obj: RoomBooking) -> None:
    """Trả phiếu về *Nháp* và NHẢ phòng khi trình bộ máy duyệt hỏng.

    Không có nhịp này thì phiếu nằm lại ở *Chờ duyệt* mà chẳng có phiên duyệt
    nào: không ai ký được, mà phòng thì bị khóa vĩnh viễn trong khung giờ đó.
    """
    obj.status = RB_DRAFT
    obj.submitted_at = None
    obj.approval_instance_id = 0
    db.commit()


def cancel(db: Session, obj: RoomBooking, reason: str, actor: int) -> RoomBooking:
    """Hủy phiếu và NHẢ phòng — cả phiếu đang chờ lẫn phiếu đã duyệt.

    Phiếu đã duyệt hủy được là có chủ ý: họp hoãn là chuyện thường, và không nhả
    thì phòng bị khóa suốt khung giờ đó dù chẳng ai dùng.
    """
    if obj.status == RB_CANCELLED:
        return obj
    obj.status = RB_CANCELLED
    obj.decision_note = (reason or "")[:500]
    obj.decided_at = datetime.now()
    obj.updated_by = actor
    db.commit()
    db.refresh(obj)
    return obj


# ── Phòng trống ────────────────────────────────────────────────────────────────

def list_availability(db: Session, start_at: datetime, end_at: datetime,
                      company_id: int = 0) -> list[dict]:
    """Từng phòng đang dùng được có trống trong khoảng này không.

    Trả **cả phòng bận** kèm phiếu đang giữ, không lọc bỏ: người đặt cần thấy
    "P301 bận vì phiếu PH012 tới 10:30" để đi xin hoặc dời giờ, chứ không phải
    một danh sách ngắn đi mà không rõ vì sao.

    Một truy vấn cho phòng, một cho phiếu chồng giờ — không hỏi trong vòng lặp.
    """
    check_time_range(start_at, end_at)

    rooms_q = db.query(MeetingRoom).filter(MeetingRoom.is_active.is_(True))
    if company_id:
        #  `company_id = 0` trên phòng nghĩa là "dùng chung mọi pháp nhân" — cùng
        #  quy ước với lịch ngày lễ của Nghỉ phép, nên phải lấy CẢ hai nhóm.
        rooms_q = rooms_q.filter(or_(MeetingRoom.company_id == company_id,
                                     MeetingRoom.company_id == 0))
    rooms = rooms_q.order_by(MeetingRoom.sort_order, MeetingRoom.code).all()
    if not rooms:
        return []

    busy = (db.query(RoomBooking)
            .filter(RoomBooking.room_id.in_([r.id for r in rooms]),
                    RoomBooking.is_deleted.is_(False),
                    RoomBooking.status.in_(BLOCKING_STATUSES),
                    RoomBooking.start_at < end_at,
                    RoomBooking.end_at > start_at)
            .order_by(RoomBooking.start_at).all())
    by_room: dict[int, list[RoomBooking]] = {}
    for b in busy:
        by_room.setdefault(b.room_id, []).append(b)

    result = []
    for room in rooms:
        holders = by_room.get(room.id, [])
        result.append({
            "room_id": room.id,
            "room_code": room.code,
            "room_name": room.name,
            "location": room.location,
            "capacity": room.capacity,
            "equipment": room.equipment,
            "available": not holders,
            "bookings": [{
                "id": b.id, "code": b.code, "title": b.title,
                "start_at": b.start_at, "end_at": b.end_at, "status": b.status,
            } for b in holders],
        })
    return result
