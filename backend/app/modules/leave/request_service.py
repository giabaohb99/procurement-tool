"""NGHIỆP VỤ ĐƠN NGHỈ PHÉP (V1-7) — lập, sửa, gửi duyệt, hủy.

Bốn luật đặt ở đây và chỉ ở đây:

1. **Số ngày** do `workday_service` tính, người dùng sửa đè được.
2. **Đủ phép** kiểm bằng `balance_service.check_enough` — vượt thì CHẶN
   (QĐ-NP2, không ứng phép).
3. **Giữ chỗ** quỹ ngay lúc gửi duyệt, không đợi tới lúc duyệt xong.
4. **Trùng ngày** với đơn khác của cùng người thì chặn — hai đơn chồng nhau là
   trừ phép hai lần cho một ngày.

Chốt "nhập đủ" đặt ở lúc **GỬI DUYỆT**, không phải lúc lưu nháp — cùng luật với
`required-fields.ts` của Thu mua và với `type_metadata.require_on_submit`.
"""
from datetime import date, datetime, time

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.utils import generate_code
from app.modules.employee.model import Employee

from . import balance_service, workday_service
from .catalog_model import LeaveType
from .constants import (EDITABLE_STATUSES, GENDER_UNKNOWN, HOLDING_STATUSES,
                        LR_APPROVED, LR_CANCELLED, LR_DRAFT, LR_PENDING,
                        LUNCH_END, LUNCH_START, SESSION_AFTERNOON,
                        SESSION_HOURLY, SESSION_MORNING, UNIT_DAY, UNIT_HOUR,
                        WORK_DAY_END, WORK_DAY_START)
from .request_model import LeaveHandover, LeaveRequest

#  Bộ lọc danh sách (whitelist của `apply_filters`). `code` để ô tìm nhanh lo.
FILTERABLE = ["status", "employee_id", "leave_type_id", "company_id",
              "department_id", "unit"]
SEARCH_FIELDS = ("code", "reason")

CODE_PREFIX = "NP"


def apply_keyword_search(query, keyword: str | None):
    kw = (keyword or "").strip()
    if not kw:
        return query
    like = f"%{kw}%"
    return query.filter(or_(*[getattr(LeaveRequest, f).like(like) for f in SEARCH_FIELDS]))


# ── Tra cứu nền ────────────────────────────────────────────────────────────────

def get_leave_type(db: Session, leave_type_id: int) -> LeaveType:
    lt = db.get(LeaveType, leave_type_id)
    if lt is None or not lt.is_active:
        raise HTTPException(400, "Loại nghỉ không tồn tại hoặc đã ngừng dùng")
    return lt


def get_employee(db: Session, employee_id: int) -> Employee:
    emp = db.get(Employee, employee_id)
    if emp is None:
        raise HTTPException(400, "Không tìm thấy hồ sơ nhân sự của người nghỉ")
    return emp


def resolve_leave_taker(db: Session, user, employee_id: int) -> Employee:
    """Người NGHỈ: lấy theo ô trên đơn, bỏ trống thì là chính người đang lập."""
    target = employee_id or getattr(user, "employee_id", 0) or 0
    if not target:
        raise HTTPException(
            400, "Chưa xác định được người nghỉ — tài khoản này chưa gắn hồ sơ nhân sự.")
    #  ⚠️ KHÔNG gác quyền ở đây. Hàm này còn dùng cho mấy đường CHỈ ĐỌC (ước
    #  lượng số ngày, tra quỹ phép hộ người khác), nên nhét chốt "được lập hộ
    #  không" vào đây là chặn nhầm cả việc xem — đã làm đỏ hai bài
    #  `test_va_ro_du_lieu_xuyen_phap_nhan` ngay lần chạy đầu. Chốt nằm ở
    #  `ensure_can_create_for`, gọi từ `create()` và `update()`.
    return get_employee(db, target)


def ensure_can_create_for(db: Session, user, employee: Employee) -> None:
    """LẬP HỘ — ai được đứng tên người khác trên tờ đơn nghỉ (07/09/2026).

    ⚠️ Trước hôm nay ô «người nghỉ» chỉ có ở API chứ không có trên màn hình, và
    **không ai gác nó**: gửi kèm `employee_id` bất kỳ là nộp được đơn đứng tên
    người đó, ở bất kỳ pháp nhân nào. Nay màn hình có ô chọn thật nên chốt này
    là bắt buộc, không phải trang trí.

    Hai điều kiện, cả hai đều phải đúng — mỗi cái trả lời một câu khác nhau:

    1. **Được phép lập hộ** — có ít nhất một vai trò cho `leave_request.create`
       với phạm vi RỘNG HƠN «của mình». Người thường chỉ có `own`: họ nộp đơn
       cho chính mình, chấm hết.
    2. **Người đó nằm trong tầm mình** — hồ sơ nhân sự ấy phải đọc được trong
       phạm vi khóa `employee`. Trưởng phòng lập hộ cho người phòng mình được,
       cho phòng khác thì không; phòng Nhân sự (`employee` phạm vi `all`) lập
       cho ai cũng được.

    Lập cho CHÍNH MÌNH thì không kiểm gì — đó là đường đi của mọi nhân viên.
    """
    from app.core.auth import get_perm_profile
    from app.core.scoping import get_scoped

    if employee.id == (getattr(user, "employee_id", 0) or 0):
        return

    profile = get_perm_profile(db, user)
    can_create_for_others = any(
        grant.get("perms", {}).get("leave_request", {}).get("create")
        and grant.get("perms", {}).get("leave_request", {}).get("scope") != "own"
        for grant in profile.get("grants", [])
    )
    if not can_create_for_others:
        raise HTTPException(
            403, "Bạn chỉ nộp được đơn nghỉ cho chính mình. Muốn lập hộ người khác "
                 "thì cần vai trò có phạm vi rộng hơn «của mình».")

    if get_scoped(db, Employee, "employee", employee.id, user, profile, "read") is None:
        raise HTTPException(
            403, f"«{employee.full_name}» nằm ngoài phạm vi nhân sự của bạn.")


# ── Kiểm tra tờ đơn ────────────────────────────────────────────────────────────

def check_date_range(from_date: date, to_date: date,
                     from_session: int, to_session: int,
                     from_time: time | None = None,
                     to_time: time | None = None) -> None:
    if to_date < from_date:
        raise HTTPException(400, "«Đến ngày» phải bằng hoặc sau «Từ ngày»")
    if (from_date == to_date and from_session == SESSION_AFTERNOON
            and to_session == SESSION_MORNING):
        #  Cùng câu chữ với `_check_leave` của giấy GNP — một luật, một câu báo.
        raise HTTPException(400, "Nghỉ từ buổi chiều đến buổi sáng cùng ngày là khoảng trống")
    check_hourly(from_date, to_date, from_session, to_session, from_time, to_time)


def is_hourly(from_session: int, to_session: int) -> bool:
    """Đơn khai theo GIỜ. Một trong hai ô buổi mang `SESSION_HOURLY` là đủ để
    coi là đơn theo giờ — `check_hourly` sẽ đòi ô kia khai giống vậy."""
    return SESSION_HOURLY in (from_session, to_session)


def check_hourly(from_date: date, to_date: date, from_session: int, to_session: int,
                 from_time: time | None, to_time: time | None) -> None:
    """Chốt của nghỉ theo giờ — chỗ nào bỏ qua thì số ngày ra sai.

    ⚠️ **Vắt qua nhiều ngày là HỢP LỆ**: *từ 14:00 ngày 07 đến 10:00 ngày 09* là
    tờ đơn có thật (đi viện hai hôm, đi công tác về muộn). Bản đầu bó trong một
    ngày và khách bác ngay — quy đổi nhiều ngày nằm ở
    `workday_service.count_hourly_days`, không khó như tưởng.
    """
    if not is_hourly(from_session, to_session):
        #  Không khai theo giờ mà vẫn gửi giờ lên → chặn tại đây, đừng lưu một
        #  khoảng giờ mà không chỗ nào đọc: lần sau có người đọc nó thật.
        if from_time is not None or to_time is not None:
            raise HTTPException(
                400, "Có khoảng giờ nhưng buổi nghỉ không phải «Theo giờ» — chọn lại buổi.")
        return

    if from_session != to_session:
        raise HTTPException(400, "Nghỉ theo giờ thì cả hai ô buổi đều phải là «Theo giờ»")
    if from_time is None or to_time is None:
        raise HTTPException(400, "Nghỉ theo giờ phải nhập đủ «Từ giờ» và «Đến giờ»")
    #  Chỉ so giờ khi CÙNG MỘT NGÀY: nghỉ 14:00 hôm nay tới 10:00 ngày kia thì
    #  «đến giờ» nhỏ hơn «từ giờ» là chuyện bình thường.
    if from_date == to_date and to_time <= from_time:
        raise HTTPException(400, "«Đến giờ» phải sau «Từ giờ»")


def check_gender(leave_type: LeaveType, employee: Employee) -> None:
    """Thai sản chỉ hiện với nữ. Hồ sơ CHƯA khai giới tính thì cho qua.

    Chặn người chưa khai là khóa cả công ty cho tới khi Nhân sự nhập bù hàng
    trăm dòng — xem `constants.GENDER_UNKNOWN`.
    """
    want = int(leave_type.gender or GENDER_UNKNOWN)
    got = int(getattr(employee, "gender", 0) or GENDER_UNKNOWN)
    if want and got and want != got:
        raise HTTPException(400, f"Loại nghỉ «{leave_type.name}» không áp dụng cho hồ sơ này")


def check_max_days(leave_type: LeaveType, days: float) -> None:
    trần = float(leave_type.max_days_per_request or 0.0)
    if trần and days > trần:
        raise HTTPException(
            400, f"«{leave_type.name}» chỉ cho nghỉ tối đa {trần} ngày mỗi lần, đơn này xin {days}.")


#  ⚠️ KHÔNG có chốt "phải nộp trước N ngày" (bỏ 05/09/2026). Cột
#  `tab_leave_type.min_notice_days` còn nằm trong bảng nhưng KHÔNG ai đọc nữa —
#  đừng dựng lại luật này trừ khi khách yêu cầu.


def check_overlap(db: Session, employee_id: int, from_date: date, to_date: date,
                  exclude_id: int = 0) -> None:
    """Chặn hai đơn CHỒNG NGÀY của cùng một người.

    Không có chốt này thì cùng một ngày bị trừ phép hai lần, và màn Lịch nghỉ
    hiện một người nghỉ hai loại cùng lúc. Chỉ xét đơn còn GIỮ CHỖ (chờ duyệt /
    đã duyệt) — nháp và đơn đã hủy thì không tính.

    Hai khoảng chồng nhau khi `a.from <= b.to` VÀ `b.from <= a.to`. Nửa ngày
    không xét tới: chặn thừa một trường hợp hiếm (sáng nghỉ ốm, chiều nghỉ phép)
    an toàn hơn là để lọt trường hợp trừ đúp.
    """
    q = (db.query(LeaveRequest)
         .filter(LeaveRequest.employee_id == employee_id,
                 LeaveRequest.is_deleted.is_(False),
                 LeaveRequest.status.in_(HOLDING_STATUSES),
                 and_(LeaveRequest.from_date <= to_date,
                      from_date <= LeaveRequest.to_date)))
    if exclude_id:
        q = q.filter(LeaveRequest.id != exclude_id)
    other = q.first()
    if other is not None:
        raise HTTPException(
            400, f"Đã có đơn «{other.code}» nghỉ từ {other.from_date} đến {other.to_date} "
                 "trùng khoảng ngày này.")


# ── Tính số ngày ───────────────────────────────────────────────────────────────

def compute_days(db: Session, leave_type: LeaveType, employee: Employee,
                 from_date: date, to_date: date, from_session: int, to_session: int,
                 requested: float = 0.0,
                 from_time: time | None = None, to_time: time | None = None) -> float:
    """Số ngày của đơn. `requested > 0` là người dùng sửa đè, tôn trọng con số đó.

    Sửa đè vẫn phải > 0: `0` ngày thì không có gì để duyệt và quỹ không trừ gì.

    ⚠️ **Đơn theo giờ KHÔNG cho sửa đè.** Số ngày của nó là phép chia thuần túy
    (`số giờ / giờ công một ngày`), người dùng đã tự chọn hai đầu giờ rồi — cho
    gõ thêm một con số thứ ba là mở đường cho tờ đơn nghỉ 2 tiếng trừ 3 ngày phép.
    """
    if is_hourly(from_session, to_session):
        return hourly_days(db, from_date, to_date, from_time, to_time,
                           company_id=employee.company_id or 0,
                           exclude_holiday=bool(leave_type.exclude_holiday))
    if requested and requested > 0:
        return round(float(requested), 2)
    days = workday_service.count_leave_days(
        db, from_date, to_date, from_session, to_session,
        company_id=employee.company_id or 0,
        exclude_holiday=bool(leave_type.exclude_holiday))
    if days <= 0:
        raise HTTPException(
            400, "Khoảng ngày này không có ngày làm việc nào (rơi trọn vào cuối tuần "
                 "hoặc ngày lễ). Sửa lại ngày, hoặc nhập tay «Tổng số ngày».")
    return days


def hourly_days(db: Session, from_date: date, to_date: date,
                from_time: time | None, to_time: time | None, *,
                company_id: int = 0, exclude_holiday: bool = True) -> float:
    """Nghỉ theo giờ quy ra ngày phép — mỏng, việc thật nằm ở `workday_service`.

    Làm tròn 2 chữ số ở đó: 1 tiếng trong ngày công 8 giờ ra `0.13`, hụt một
    chút so với 1/8 thật. Chấp nhận, vì quỹ phép lưu dạng số ngày và sai số này
    luôn nghiêng về phía NGƯỜI LAO ĐỘNG (trừ ít hơn) chứ không ngược lại.
    """
    if from_time is None or to_time is None:
        raise HTTPException(400, "Nghỉ theo giờ phải nhập đủ «Từ giờ» và «Đến giờ»")
    days = workday_service.count_hourly_days(
        db, from_date, to_date, from_time, to_time,
        company_id=company_id, exclude_holiday=exclude_holiday)
    if days <= 0:
        raise HTTPException(
            400, "Khoảng giờ này không rơi vào giờ làm việc nào — kiểm lại ngày và giờ "
                 f"(giờ làm {WORK_DAY_START:%H:%M}–{WORK_DAY_END:%H:%M}, nghỉ trưa "
                 f"{LUNCH_START:%H:%M}–{LUNCH_END:%H:%M}).")
    return days


# ── Tạo · sửa · xóa ────────────────────────────────────────────────────────────

def _replace_handovers(db: Session, request_id: int, items, actor: int) -> None:
    """Ghi đè danh sách bàn giao. Xóa hết rồi thêm lại — danh sách ngắn (2-3 dòng)
    nên so từng dòng để sửa tại chỗ chỉ tổ phức tạp mà không nhanh hơn."""
    db.query(LeaveHandover).filter(LeaveHandover.request_id == request_id).delete()
    for i, item in enumerate(items or []):
        if not item.employee_id:
            continue
        db.add(LeaveHandover(request_id=request_id, employee_id=item.employee_id,
                             content=(item.content or "")[:500], sort_order=i,
                             created_by=actor, updated_by=actor))


def create(db: Session, data, user) -> LeaveRequest:
    """Lập đơn — luôn ở trạng thái **Nháp**. Gửi duyệt là một bước riêng."""
    employee = resolve_leave_taker(db, user, data.employee_id)
    ensure_can_create_for(db, user, employee)
    leave_type = get_leave_type(db, data.leave_type_id)

    check_date_range(data.from_date, data.to_date, data.from_session, data.to_session,
                     data.from_time, data.to_time)
    check_gender(leave_type, employee)
    days = compute_days(db, leave_type, employee, data.from_date, data.to_date,
                        data.from_session, data.to_session, data.total_days,
                        data.from_time, data.to_time)
    check_max_days(leave_type, days)

    hourly = is_hourly(data.from_session, data.to_session)
    obj = LeaveRequest(
        code=generate_code(db, LeaveRequest, CODE_PREFIX),
        company_id=employee.company_id or 0,
        department_id=employee.department_id or 0,
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        from_date=data.from_date, to_date=data.to_date,
        from_session=data.from_session, to_session=data.to_session,
        from_time=data.from_time, to_time=data.to_time,
        #  `unit` bám theo cách khai, không để người gửi tự đặt: đơn theo giờ mà
        #  ghi đơn vị «Ngày» thì mọi báo cáo đọc sau này hiểu sai bản chất.
        unit=UNIT_HOUR if hourly else (data.unit or UNIT_DAY), total_days=days,
        reason=(data.reason or "").strip()[:1000],
        contact_phone=(data.contact_phone or "").strip()[:30],
        contact_address=(data.contact_address or "").strip()[:255],
        status=LR_DRAFT,
        created_by=user.id, updated_by=user.id,
    )
    db.add(obj)
    db.flush()
    _replace_handovers(db, obj.id, data.handovers, user.id)
    db.commit()
    db.refresh(obj)
    return obj


def check_editable(obj: LeaveRequest) -> None:
    if obj.status not in EDITABLE_STATUSES:
        raise HTTPException(
            400, "Đơn đã gửi duyệt nên không sửa được. Rút phiếu duyệt hoặc hủy đơn "
                 "rồi lập lại.")


def update(db: Session, obj: LeaveRequest, data, user) -> LeaveRequest:
    check_editable(obj)
    values = data.model_dump(exclude_unset=True)
    #  Lấy danh sách bàn giao từ CHÍNH đối tượng Pydantic, không lấy từ bản
    #  `model_dump()`: bản dump biến `HandoverItem` thành `dict`, mà
    #  `_replace_handovers` đọc bằng thuộc tính. Cờ "có gửi lên hay không" thì
    #  vẫn phải hỏi bản dump — `None` là giá trị hợp lệ, không phân biệt được
    #  với "không gửi" nếu chỉ nhìn thuộc tính.
    has_handovers = "handovers" in values
    values.pop("handovers", None)
    handovers = data.handovers if has_handovers else None

    employee = (resolve_leave_taker(db, user, values["employee_id"])
                if "employee_id" in values else get_employee(db, obj.employee_id))
    #  Đổi người nghỉ khi SỬA cũng phải qua chốt lập hộ — nếu không thì lập đơn
    #  cho mình rồi sửa sang tên người khác là đi vòng qua đúng cái chốt đó.
    ensure_can_create_for(db, user, employee)
    leave_type = get_leave_type(db, values.get("leave_type_id", obj.leave_type_id))

    from_date = values.get("from_date", obj.from_date)
    to_date = values.get("to_date", obj.to_date)
    from_session = values.get("from_session", obj.from_session)
    to_session = values.get("to_session", obj.to_session)
    #  Đổi buổi mà KHÔNG gửi kèm giờ thì đọc giờ cũ trên phiếu — trừ khi vừa
    #  chuyển ra khỏi «Theo giờ», lúc đó giờ cũ phải bị xóa chứ không giữ lại.
    hourly = is_hourly(from_session, to_session)
    from_time = values.get("from_time", obj.from_time if hourly else None)
    to_time = values.get("to_time", obj.to_time if hourly else None)
    check_date_range(from_date, to_date, from_session, to_session, from_time, to_time)
    check_gender(leave_type, employee)

    #  `total_days` chỉ coi là "sửa đè" khi người dùng GỬI LÊN nó. Không gửi thì
    #  tính lại — sửa ngày mà giữ nguyên số ngày cũ là sai ngay lập tức.
    requested = values.get("total_days", 0.0) if "total_days" in values else 0.0
    days = compute_days(db, leave_type, employee, from_date, to_date,
                        from_session, to_session, requested, from_time, to_time)
    check_max_days(leave_type, days)

    for key, value in values.items():
        setattr(obj, key, value)
    obj.employee_id = employee.id
    obj.company_id = employee.company_id or 0
    obj.department_id = employee.department_id or 0
    obj.leave_type_id = leave_type.id
    obj.from_time = from_time
    obj.to_time = to_time
    obj.unit = UNIT_HOUR if hourly else UNIT_DAY
    obj.total_days = days
    obj.updated_by = user.id

    if has_handovers:
        _replace_handovers(db, obj.id, handovers, user.id)
    db.commit()
    db.refresh(obj)
    return obj


def soft_delete(db: Session, obj: LeaveRequest, user) -> None:
    """Xóa mềm. Chỉ đơn chưa vào luồng — đơn đã duyệt là hồ sơ, phải HỦY chứ không xóa."""
    check_editable(obj)
    obj.is_deleted = True
    obj.updated_by = user.id
    db.commit()


# ── Gửi duyệt · hủy ────────────────────────────────────────────────────────────

REQUIRED_ON_SUBMIT = ("reason",)


def check_ready_to_submit(obj: LeaveRequest) -> None:
    """Chốt "nhập đủ" — đặt ở lúc GỬI, không phải lúc lưu nháp.

    Người duyệt mở đơn ra mà không có lý do nghỉ thì họ duyệt cái gì.
    """
    if not (obj.reason or "").strip():
        raise HTTPException(400, "Thiếu «Lý do nghỉ» — nhập đủ trước khi gửi duyệt.")
    if obj.total_days <= 0:
        raise HTTPException(400, "«Tổng số ngày» phải lớn hơn 0")


def prepare_submit(db: Session, obj: LeaveRequest, user) -> tuple[Employee, LeaveType]:
    """Mọi chốt chặn của bước GỬI DUYỆT, theo thứ tự rẻ trước đắt sau.

    Tách khỏi `submit()` để controller gọi được trước khi đụng vào bộ máy duyệt:
    trình phiếu xong mới phát hiện hết phép thì phải đi rút phiếu, và người dùng
    đã kịp thấy một phiếu duyệt hiện ra rồi biến mất.
    """
    if obj.status not in EDITABLE_STATUSES:
        raise HTTPException(400, "Đơn này đã gửi duyệt rồi")
    check_ready_to_submit(obj)

    employee = get_employee(db, obj.employee_id)
    leave_type = get_leave_type(db, obj.leave_type_id)
    check_overlap(db, obj.employee_id, obj.from_date, obj.to_date, exclude_id=obj.id)
    balance_service.check_enough(db, employee, obj.from_date.year, leave_type,
                                 obj.total_days)
    return employee, leave_type


def mark_submitted(db: Session, obj: LeaveRequest, employee: Employee,
                   leave_type: LeaveType, user, instance_id: int = 0) -> LeaveRequest:
    """Đặt đơn vào *Chờ duyệt* và GIỮ CHỖ quỹ. Gọi sau khi đã trình bộ máy duyệt."""
    obj.status = LR_PENDING
    obj.approval_instance_id = instance_id
    obj.submitted_at = datetime.now()
    obj.decision_note = ""
    obj.updated_by = user.id
    balance_service.reserve(db, employee, obj.from_date.year, leave_type,
                            obj.total_days, user.id)
    db.commit()
    db.refresh(obj)
    return obj


def cancel(db: Session, obj: LeaveRequest, reason: str, actor: int) -> LeaveRequest:
    """Hủy đơn và TRẢ LẠI quỹ — cả đơn đang chờ lẫn đơn đã duyệt.

    Đơn đã duyệt hủy được là có chủ ý: người xin nghỉ tuần sau, tuần này đổi ý.
    Không hoàn thì ngày phép của họ mất luôn và Nhân sự phải bù bằng tay.
    """
    if obj.status == LR_CANCELLED:
        return obj
    year = obj.from_date.year
    if obj.status == LR_PENDING:
        balance_service.release(db, obj.employee_id, year, obj.leave_type_id,
                                obj.total_days, actor)
    elif obj.status == LR_APPROVED:
        balance_service.refund_used(db, obj.employee_id, year, obj.leave_type_id,
                                    obj.total_days, actor)

    obj.status = LR_CANCELLED
    obj.decision_note = (reason or "")[:500]
    obj.decided_at = datetime.now()
    obj.updated_by = actor
    db.commit()
    db.refresh(obj)
    return obj
