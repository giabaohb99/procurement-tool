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
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.utils import generate_code
from app.modules.employee.model import Employee

from . import balance_service, request_periods, workday_service
from .catalog_model import LeaveType
from .constants import (EDITABLE_STATUSES, GENDER_UNKNOWN,
                        LR_APPROVED, LR_CANCELLED, LR_DRAFT, LR_PENDING,
                        SESSION_AFTERNOON, SESSION_HOURLY, SESSION_MORNING,
                        UNIT_DAY, UNIT_HOUR)
from .period_spans import PeriodView
from .request_model import LeaveHandover, LeaveRequest, LeaveRequestLine

#  Bộ lọc danh sách (whitelist của `apply_filters`). `code` để ô tìm nhanh lo.
#  `leave_type_id` lọc theo **loại chính** của đơn — xem ghi chú ở cột đó trong
#  `request_model`. Đơn hai loại lọc theo loại phụ thì không ra; chấp nhận, vì
#  lọc trên bảng con đòi JOIN và màn danh sách chưa ai hỏi tới.
FILTERABLE = ["status", "employee_id", "leave_type_id", "company_id",
              "department_id", "unit"]

#  Whitelist RIÊNG cho BỘ LỌC ĐIỀU KIỆN (`<cột>__<toán tử>=`), rộng hơn bộ trên.
#  Tách hai vì mấy cột này phải loại khỏi lọc TRẦN mà vẫn phải lọc được ở bộ lọc
#  nâng cao: `code` và `reason` đã nhường param trần cho ô tìm nhanh đa trường,
#  còn `from_date`/`to_date` thì param trần mang nghĩa KHÁC hẳn — chúng lọc theo
#  GIAO NHAU của khoảng cho màn Lịch nghỉ, không phải so từng cột. Hậu tố `__gte`
#  không đụng vào nghĩa đó. Thiếu tên nào ở đây thì điều kiện của nó bị **bỏ qua
#  im lặng**: người dùng bấm Áp dụng, danh sách không đổi, không báo gì.
FILTER_OPERATORS = FILTERABLE + ["code", "reason", "from_date", "to_date",
                                 "total_days"]
SEARCH_FIELDS = ("code", "reason")

CODE_PREFIX = "NP"

#  Trần số loại nghỉ trong một đơn. Không phải giới hạn kỹ thuật — chỉ là mức mà
#  quá nó thì gần như chắc chắn người dùng đang nhập nhầm, và mỗi dòng là một
#  lượt khóa dòng quỹ lúc gửi duyệt.
MAX_LINES = 10


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

    ⚠️ Trước hôm nay ô "người nghỉ" chỉ có ở API chứ không có trên màn hình, và
    **không ai gác nó**: gửi kèm `employee_id` bất kỳ là nộp được đơn đứng tên
    người đó, ở bất kỳ pháp nhân nào. Nay màn hình có ô chọn thật nên chốt này
    là bắt buộc, không phải trang trí.

    Hai điều kiện, cả hai đều phải đúng — mỗi cái trả lời một câu khác nhau:

    1. **Được phép lập hộ** — có ít nhất một vai trò cho `leave_request.create`
       với phạm vi RỘNG HƠN "của mình". Người thường chỉ có `own`: họ nộp đơn
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
                 "thì cần vai trò có phạm vi rộng hơn \"của mình\".")

    if get_scoped(db, Employee, "employee", employee.id, user, profile, "read") is None:
        raise HTTPException(
            403, f"\"{employee.full_name}\" nằm ngoài phạm vi nhân sự của bạn.")


# ── Kiểm tra tờ đơn ────────────────────────────────────────────────────────────

def check_date_range(from_date: date, to_date: date,
                     from_session: int, to_session: int,
                     from_time: time | None = None,
                     to_time: time | None = None) -> None:
    if to_date < from_date:
        raise HTTPException(400, "\"Đến ngày\" phải bằng hoặc sau \"Từ ngày\"")
    #  ⚠️ Chặn khoảng DÀI QUÁ TRẦN — không có chốt này thì `date_range` lặng lẽ
    #  dừng ở `MAX_RANGE_DAYS` và trả về một con số nhỏ hơn sự thật: gõ nhầm năm
    #  2036 (3651 ngày) ra đúng **343 ngày**, một con số trông hoàn toàn hợp lý.
    #  Sai kiểu này không có triệu chứng nào cho tới lúc đối chiếu sổ.
    span = (to_date - from_date).days + 1
    if span > workday_service.MAX_RANGE_DAYS:
        raise HTTPException(
            400, f"Khoảng nghỉ dài {span} ngày, vượt trần {workday_service.MAX_RANGE_DAYS} "
                 "ngày của một tờ đơn. Kiểm lại năm ở hai ô ngày.")
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
                400, "Có khoảng giờ nhưng buổi nghỉ không phải \"Theo giờ\" — chọn lại buổi.")
        return

    if from_session != to_session:
        raise HTTPException(400, "Nghỉ theo giờ thì cả hai ô buổi đều phải là \"Theo giờ\"")
    if from_time is None or to_time is None:
        raise HTTPException(400, "Nghỉ theo giờ phải nhập đủ \"Từ giờ\" và \"Đến giờ\"")
    #  Chỉ so giờ khi CÙNG MỘT NGÀY: nghỉ 14:00 hôm nay tới 10:00 ngày kia thì
    #  "đến giờ" nhỏ hơn "từ giờ" là chuyện bình thường.
    if from_date == to_date and to_time <= from_time:
        raise HTTPException(400, "\"Đến giờ\" phải sau \"Từ giờ\"")


def check_gender(leave_type: LeaveType, employee: Employee) -> None:
    """Thai sản chỉ hiện với nữ. Hồ sơ CHƯA khai giới tính thì cho qua.

    Chặn người chưa khai là khóa cả công ty cho tới khi Nhân sự nhập bù hàng
    trăm dòng — xem `constants.GENDER_UNKNOWN`.
    """
    want = int(leave_type.gender or GENDER_UNKNOWN)
    got = int(getattr(employee, "gender", 0) or GENDER_UNKNOWN)
    if want and got and want != got:
        raise HTTPException(400, f"Loại nghỉ \"{leave_type.name}\" không áp dụng cho hồ sơ này")


def check_max_days(leave_type: LeaveType, days: float) -> None:
    trần = float(leave_type.max_days_per_request or 0.0)
    if trần and days > trần:
        raise HTTPException(
            400, f"\"{leave_type.name}\" chỉ cho nghỉ tối đa {trần} ngày mỗi lần, đơn này xin {days}.")


#  ⚠️ KHÔNG có chốt "phải nộp trước N ngày" (bỏ 05/09/2026). Cột
#  `tab_leave_type.min_notice_days` còn nằm trong bảng nhưng KHÔNG ai đọc nữa —
#  đừng dựng lại luật này trừ khi khách yêu cầu.


def check_overlap(db: Session, employee_id: int, from_date: date, to_date: date,
                  exclude_id: int = 0) -> None:
    """Chặn hai đơn CHỒNG NGÀY của cùng một người (bản một khoảng — lớp mỏng).

    Không có chốt này thì cùng một ngày bị trừ phép hai lần, và màn Lịch nghỉ
    hiện một người nghỉ hai loại cùng lúc. Chỉ xét đơn còn GIỮ CHỖ (chờ duyệt /
    đã duyệt) — nháp và đơn đã hủy thì không tính. Nửa ngày không xét tới: chặn
    thừa một trường hợp hiếm an toàn hơn là để lọt trường hợp trừ đúp.

    Đơn nhiều khoảng (CR-683) so từng khoảng × từng khoảng ở
    `request_periods.raise_if_overlap`; hàm này giữ tên cũ cho nơi gọi một khoảng.
    """
    request_periods.raise_if_overlap(
        db, employee_id, [request_periods.single_period(from_date, to_date)], exclude_id)


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
                           exclude_holiday=bool(leave_type.exclude_holiday),
                           employee=employee)
    if requested and requested > 0:
        return round(float(requested), 2)
    days = workday_service.count_leave_days(
        db, from_date, to_date, from_session, to_session,
        company_id=employee.company_id or 0,
        exclude_holiday=bool(leave_type.exclude_holiday), employee=employee)
    if days <= 0:
        raise HTTPException(
            400, "Khoảng ngày này không có ngày làm việc nào theo lịch làm việc áp cho "
                 f"\"{employee.full_name}\" (rơi trọn vào ngày nghỉ hoặc ngày lễ). Sửa lại ngày, "
                 "hoặc nhập tay \"Tổng số ngày\".")
    return days


def hourly_days(db: Session, from_date: date, to_date: date,
                from_time: time | None, to_time: time | None, *,
                company_id: int = 0, exclude_holiday: bool = True,
                employee: Employee | None = None) -> float:
    """Nghỉ theo giờ quy ra ngày phép — mỏng, việc thật nằm ở `workday_service`.

    Làm tròn 2 chữ số ở đó: 1 tiếng trong ngày công 8 giờ ra `0.13`, hụt một
    chút so với 1/8 thật. Chấp nhận, vì quỹ phép lưu dạng số ngày và sai số này
    luôn nghiêng về phía NGƯỜI LAO ĐỘNG (trừ ít hơn) chứ không ngược lại.
    """
    if from_time is None or to_time is None:
        raise HTTPException(400, "Nghỉ theo giờ phải nhập đủ \"Từ giờ\" và \"Đến giờ\"")
    days = workday_service.count_hourly_days(
        db, from_date, to_date, from_time, to_time,
        company_id=company_id, exclude_holiday=exclude_holiday, employee=employee)
    if days <= 0:
        raise HTTPException(
            400, "Khoảng giờ này không rơi vào giờ làm việc nào theo lịch làm việc của người "
                 "nghỉ (ngày nghỉ, ngoài khung giờ, giờ nghỉ trưa hoặc ngày lễ) — kiểm lại ngày và giờ.")
    return days


# ── Khoảng ngày (duoc-CR-683) ──────────────────────────────────────────────────

def validate_periods(periods: list[PeriodView], from_time: time | None,
                     to_time: time | None) -> list[PeriodView]:
    """Kiểm cả danh sách khoảng, trả về danh sách đã sắp theo ngày.

    Từng khoảng đi qua `check_date_range` (một luật, một câu báo); đơn nhiều khoảng
    thì câu lỗi gắn tên khoảng. Rồi tới luật toàn đơn ở `request_periods.check_layout`.
    """
    request_periods.check_count_and_hourly(periods)
    multi = len(periods) > 1
    for i, p in enumerate(periods):
        try:
            check_date_range(p.from_date, p.to_date, p.from_session, p.to_session,
                             from_time, to_time)
        except HTTPException as exc:
            if not multi:
                raise
            raise HTTPException(
                exc.status_code, f"{request_periods.label_of(i, p)}: {exc.detail}") from None
    return request_periods.check_layout(periods)


def resolve_period_days(db: Session, pairs: list[tuple[LeaveType, float]], employee: Employee,
                        periods: list[PeriodView], from_time: time | None,
                        to_time: time | None) -> tuple[list[tuple[LeaveType, float]], list[float]]:
    """(dòng đã chốt ngày, số ngày TỪNG khoảng).

    Một khoảng: đúng đường cũ `resolve_days`, ngày của khoảng = tổng các dòng. Nhiều
    khoảng (không theo giờ): lịch + ngày lễ nạp một lần (`count_leave_days_periods`);
    khoảng nào ước tính 0 ngày làm việc thì LUÔN chặn (kể cả khi dòng có số sửa đè —
    form luôn gửi `days`, nên chặn theo cờ sửa đè thì không bao giờ chạy). Một dòng
    không sửa đè → tổng = Σ ngày khoảng; có sửa đè hoặc nhiều dòng → giữ số người
    dùng, ngày khoảng lưu là số ước tính.
    """
    first = periods[0]
    if len(periods) == 1:
        resolved = resolve_days(db, pairs, employee, first.from_date, first.to_date,
                                first.from_session, first.to_session, from_time, to_time)
        return resolved, [round(sum(d for _, d in resolved), 2)]

    leave_type, requested = pairs[0]
    per_days = workday_service.count_leave_days_periods(
        db, periods, company_id=employee.company_id or 0,
        exclude_holiday=bool(leave_type.exclude_holiday), employee=employee)
    for i, (p, d) in enumerate(zip(periods, per_days)):
        if d <= 0:
            raise HTTPException(
                400, f"{request_periods.label_of(i, p)} không có ngày làm việc nào theo lịch "
                     f"làm việc áp cho \"{employee.full_name}\" (rơi trọn vào ngày nghỉ hoặc "
                     "ngày lễ). Bỏ khoảng này khỏi đơn.")
    if len(pairs) > 1:
        resolved = resolve_days(db, pairs, employee, first.from_date, first.to_date,
                                first.from_session, first.to_session, from_time, to_time)
    elif requested and requested > 0:
        resolved = [(leave_type, round(float(requested), 2))]
    else:
        resolved = [(leave_type, round(sum(per_days), 2))]
    return resolved, per_days


# ── Dòng loại nghỉ (07/09/2026) ────────────────────────────────────────────────
#
#  Một tờ đơn khai được NHIỀU loại nghỉ — *"nghỉ 07→10/09: 3 ngày phép năm +
#  1 ngày không lương"*. Cả đơn dùng chung MỘT khoảng ngày; dòng chỉ chia số
#  ngày. Ba hàm dưới đây chạy nối nhau và đúng thứ tự đó:
#
#      collect_lines  →  đọc ô `lines` (hoặc cặp cột cũ) ra [(loại nghỉ, ngày)]
#      resolve_days   →  điền số ngày máy tính cho dòng để trống
#      check_lines    →  bốn chốt: trùng loại · ngày ≤ 0 · quá trần · quá khoảng

def collect_lines(db: Session, raw_lines, leave_type_id: int,
                  total_days: float) -> list[tuple[LeaveType, float]]:
    """Danh sách dòng của đơn, dạng `[(LeaveType, số ngày)]`.

    Không gửi `lines` thì dựng MỘT dòng từ cặp `leave_type_id` + `total_days`
    cũ. Đó là cả đường tương thích ngược lẫn đường đi của đơn một loại — tức
    gần như mọi tờ đơn — nên nó không phải nhánh phụ tạm bợ.
    """
    items = [(item.leave_type_id, float(item.days or 0.0))
             for item in (raw_lines or []) if item.leave_type_id]
    if not items:
        if not leave_type_id:
            raise HTTPException(400, "Chưa chọn loại nghỉ cho đơn này")
        items = [(leave_type_id, float(total_days or 0.0))]
    if len(items) > MAX_LINES:
        raise HTTPException(
            400, f"Một đơn khai tối đa {MAX_LINES} loại nghỉ. Nghỉ dài nhiều đợt "
                 "thì lập nhiều đơn.")
    return [(get_leave_type(db, type_id), days) for type_id, days in items]


def resolve_days(db: Session, pairs: list[tuple[LeaveType, float]], employee: Employee,
                 from_date: date, to_date: date, from_session: int, to_session: int,
                 from_time: time | None, to_time: time | None
                 ) -> list[tuple[LeaveType, float]]:
    """Chốt số ngày của từng dòng.

    Đơn MỘT dòng đi qua `compute_days` y như trước: để trống thì máy tính từ
    khoảng ngày, gõ vào thì tôn trọng con số đó (đơn theo giờ vẫn không cho gõ
    đè). Đơn NHIỀU dòng thì mỗi dòng phải gõ rõ — máy không đoán được chia
    4 ngày thành 3+1 hay 2+2, và đoán sai là trừ nhầm quỹ.

    ⚠️ **Theo giờ thì đúng một dòng.** Nghỉ hai tiếng mà chia hai loại nghỉ là
    ca chưa từng có, còn cho vào thì phải chia con số quy đổi giờ→ngày ra nhiều
    phần — thêm một đường sinh lỗi cho một thứ không ai dùng.
    """
    if is_hourly(from_session, to_session) and len(pairs) > 1:
        raise HTTPException(
            400, "Nghỉ theo giờ chỉ khai được một loại nghỉ. Bỏ bớt dòng, hoặc "
                 "chọn lại buổi nghỉ.")

    if len(pairs) == 1:
        leave_type, days = pairs[0]
        return [(leave_type, compute_days(db, leave_type, employee, from_date, to_date,
                                          from_session, to_session, days,
                                          from_time, to_time))]

    resolved = []
    for leave_type, days in pairs:
        if days <= 0:
            raise HTTPException(
                400, f"Dòng \"{leave_type.name}\" chưa có số ngày. Đơn nhiều loại nghỉ "
                     "phải ghi rõ mỗi loại mấy ngày.")
        resolved.append((leave_type, round(days, 2)))
    return resolved


def check_lines(pairs: list[tuple[LeaveType, float]], periods: list[PeriodView]) -> float:
    """Bốn chốt trên danh sách dòng. Trả TỔNG số ngày của đơn.

    Chốt cuối là **trần theo khoảng ngày**: tổng số ngày nghỉ không vượt quá TỔNG số
    ngày dương lịch của các khoảng đã chọn (khe giữa các khoảng không tính — bao ngoài
    sẽ nuốt cả khe). Trần này cố ý đếm cả T7/CN/lễ nên nó không bao giờ chặn nhầm một
    ca hợp lệ — kể cả công trường chạy Chủ nhật — nhưng nó chặn được ca gõ nhầm 30 ngày
    trên khoảng hai ngày, thứ mà trước đây lọt thẳng vào sổ quỹ vì `total_days` cho
    sửa đè tự do.
    """
    seen: set[int] = set()
    for leave_type, days in pairs:
        if leave_type.id in seen:
            raise HTTPException(
                400, f"Loại nghỉ \"{leave_type.name}\" khai hai lần — gộp lại thành "
                     "một dòng.")
        seen.add(leave_type.id)
        if days <= 0:
            raise HTTPException(400, f"Dòng \"{leave_type.name}\" phải có số ngày lớn hơn 0")
        check_max_days(leave_type, days)

    total = round(sum(days for _, days in pairs), 2)
    ceiling = request_periods.calendar_days(periods)
    if total > ceiling:
        raise HTTPException(
            400, f"Tổng {total} ngày nhiều hơn số ngày của khoảng đã chọn "
                 f"({ceiling} ngày). Sửa lại số ngày, hoặc nới khoảng ngày nghỉ.")
    return total


def primary_type_id(pairs: list[tuple[LeaveType, float]]) -> int:
    """Loại nghỉ CHÍNH của đơn — dòng chiếm nhiều ngày nhất, hòa thì dòng đầu.

    Đây là con số đi vào cột dẫn xuất `LeaveRequest.leave_type_id`, tức cũng là
    thứ bộ lọc danh sách và điều kiện rẽ nhánh của luồng duyệt đọc được. Xem
    phần *Hạn chế đã biết* ở `doc/erp/hrm/02-nghi-phep.md`.
    """
    return max(pairs, key=lambda pair: pair[1])[0].id if pairs else 0


def replace_lines(db: Session, request_id: int,
                  pairs: list[tuple[LeaveType, float]], actor: int) -> None:
    """Ghi đè danh sách dòng. Xóa hết rồi thêm lại — cùng lý lẽ với `_replace_handovers`."""
    db.query(LeaveRequestLine).filter(LeaveRequestLine.request_id == request_id).delete()
    for i, (leave_type, days) in enumerate(pairs):
        db.add(LeaveRequestLine(request_id=request_id, leave_type_id=leave_type.id,
                                days=days, sort_order=i,
                                created_by=actor, updated_by=actor))


def lines_of(db: Session, request_id: int) -> list[LeaveRequestLine]:
    """Dòng của một đơn, theo thứ tự nhập. Rỗng chỉ xảy ra với dữ liệu hỏng."""
    return (db.query(LeaveRequestLine)
            .filter(LeaveRequestLine.request_id == request_id)
            .order_by(LeaveRequestLine.sort_order)
            .all())


# ── Bốn nhịp sổ quỹ, chạy THEO DÒNG ────────────────────────────────────────────
#
#  Quỹ phép là (người × năm × **loại nghỉ**), nên đơn hai loại là hai lượt ghi
#  vào hai dòng quỹ khác nhau. Gói lại thành bốn hàm ở đây chứ không để nơi gọi
#  tự lặp: nơi gọi có bốn chỗ (gửi duyệt · duyệt xong · ba kết cục không duyệt ·
#  hủy đơn) và chỉ cần một chỗ quên vòng lặp là sổ lệch âm thầm.

def check_enough_lines(db: Session, employee: Employee, obj: LeaveRequest) -> None:
    """Đủ phép cho MỌI dòng. Một dòng thiếu là cả đơn không gửi được (QĐ-NP2)."""
    year = obj.from_date.year
    for line in lines_of(db, obj.id):
        balance_service.check_enough(db, employee, year,
                                     get_leave_type(db, line.leave_type_id), line.days)


def reserve_lines(db: Session, employee: Employee, obj: LeaveRequest, actor: int) -> None:
    year = obj.from_date.year
    for line in lines_of(db, obj.id):
        balance_service.reserve(db, employee, year,
                                get_leave_type(db, line.leave_type_id), line.days, actor)


def release_lines(db: Session, obj: LeaveRequest, actor: int) -> None:
    year = obj.from_date.year
    for line in lines_of(db, obj.id):
        balance_service.release(db, obj.employee_id, year, line.leave_type_id,
                                line.days, actor)


def consume_lines(db: Session, obj: LeaveRequest, actor: int) -> None:
    year = obj.from_date.year
    for line in lines_of(db, obj.id):
        balance_service.consume(db, obj.employee_id, year, line.leave_type_id,
                                line.days, actor)


def refund_lines(db: Session, obj: LeaveRequest, actor: int) -> None:
    year = obj.from_date.year
    for line in lines_of(db, obj.id):
        balance_service.refund_used(db, obj.employee_id, year, line.leave_type_id,
                                    line.days, actor)


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

    periods = validate_periods(request_periods.normalize_create(data),
                               data.from_time, data.to_time)
    pairs = collect_lines(db, data.lines, data.leave_type_id, data.total_days)
    for leave_type, _ in pairs:
        check_gender(leave_type, employee)
    pairs, per_days = resolve_period_days(db, pairs, employee, periods,
                                          data.from_time, data.to_time)
    days = check_lines(pairs, periods)
    periods = request_periods.with_days(periods, per_days)

    hourly = request_periods.is_hourly_period(periods[0])
    obj = LeaveRequest(
        code=generate_code(db, LeaveRequest, CODE_PREFIX),
        company_id=employee.company_id or 0,
        department_id=employee.department_id or 0,
        employee_id=employee.id,
        leave_type_id=primary_type_id(pairs),
        #  Đầu đơn là DẪN XUẤT của danh sách khoảng (khoảng đầu ↔ khoảng cuối).
        **request_periods.header_of(periods),
        from_time=data.from_time, to_time=data.to_time,
        #  `unit` bám theo cách khai, không để người gửi tự đặt: đơn theo giờ mà
        #  ghi đơn vị "Ngày" thì mọi báo cáo đọc sau này hiểu sai bản chất.
        unit=UNIT_HOUR if hourly else (data.unit or UNIT_DAY), total_days=days,
        reason=(data.reason or "").strip()[:1000],
        contact_phone=(data.contact_phone or "").strip()[:30],
        contact_address=(data.contact_address or "").strip()[:255],
        status=LR_DRAFT,
        created_by=user.id, updated_by=user.id,
    )
    db.add(obj)
    db.flush()
    replace_lines(db, obj.id, pairs, user.id)
    request_periods.replace_periods(db, obj.id, periods, user.id)
    _replace_handovers(db, obj.id, data.handovers, user.id)
    db.commit()
    db.refresh(obj)
    return obj


def check_editable(obj: LeaveRequest) -> None:
    if obj.status not in EDITABLE_STATUSES:
        raise HTTPException(
            400, "Đơn đã gửi duyệt nên không sửa được. Rút phiếu duyệt hoặc hủy đơn "
                 "rồi lập lại.")


def _lines_for_update(db: Session, obj: LeaveRequest, raw_lines,
                      leave_type_id: int | None,
                      requested: float) -> list[tuple[LeaveType, float]]:
    """Dòng của tờ đơn SAU khi sửa, theo ba đường vào — xếp từ rõ ràng nhất.

    1. Gửi `lines` → dùng đúng danh sách đó.
    2. Gửi `leave_type_id` (đường cũ, một loại) → một dòng loại đó.
    3. Không gửi gì về loại nghỉ → giữ nguyên dòng đang có trong sổ.

    Ở đường 3, đơn MỘT dòng trả về số ngày `requested` chứ không phải số ngày đã
    lưu: `resolve_days` sẽ tính lại từ khoảng ngày khi `requested = 0`, tức giữ
    đúng hành vi cũ *"sửa ngày thì số ngày tự tính lại"*. Đơn NHIỀU dòng thì giữ
    nguyên phân bổ — máy không có cách nào chia lại hộ, và im lặng chia lại là
    sửa vào quỹ phép của người ta.
    """
    if raw_lines is not None:
        return collect_lines(db, raw_lines, 0, 0.0)
    if leave_type_id:
        return collect_lines(db, None, leave_type_id, requested)

    existing = lines_of(db, obj.id)
    if len(existing) <= 1:
        return collect_lines(db, None, obj.leave_type_id, requested)
    return [(get_leave_type(db, line.leave_type_id), line.days) for line in existing]


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
    #  Cùng quy ước với `handovers`: CÓ MẶT khóa `lines` là ghi đè cả danh sách,
    #  vắng mặt là giữ nguyên dòng đang có.
    has_lines = "lines" in values
    values.pop("lines", None)
    values.pop("periods", None)

    employee = (resolve_leave_taker(db, user, values["employee_id"])
                if "employee_id" in values else get_employee(db, obj.employee_id))
    #  Đổi người nghỉ khi SỬA cũng phải qua chốt lập hộ — nếu không thì lập đơn
    #  cho mình rồi sửa sang tên người khác là đi vòng qua đúng cái chốt đó.
    ensure_can_create_for(db, user, employee)

    periods = request_periods.normalize_update(db, obj, values, data)
    #  Đổi buổi mà KHÔNG gửi kèm giờ thì đọc giờ cũ trên phiếu — trừ khi vừa
    #  chuyển ra khỏi "Theo giờ", lúc đó giờ cũ phải bị xóa chứ không giữ lại.
    hourly = any(request_periods.is_hourly_period(p) for p in periods)
    from_time = values.get("from_time", obj.from_time if hourly else None)
    to_time = values.get("to_time", obj.to_time if hourly else None)
    periods = validate_periods(periods, from_time, to_time)

    #  `total_days` chỉ coi là "sửa đè" khi người dùng GỬI LÊN nó. Không gửi thì
    #  tính lại — sửa ngày mà giữ nguyên số ngày cũ là sai ngay lập tức.
    requested = values.get("total_days", 0.0) if "total_days" in values else 0.0
    pairs = _lines_for_update(db, obj, data.lines if has_lines else None,
                              values.get("leave_type_id"), requested)
    for line_type, _ in pairs:
        check_gender(line_type, employee)
    pairs, per_days = resolve_period_days(db, pairs, employee, periods, from_time, to_time)
    days = check_lines(pairs, periods)
    periods = request_periods.with_days(periods, per_days)

    for key, value in values.items():
        if key not in request_periods.HEADER_KEYS:   # đầu đơn dẫn xuất từ `periods`
            setattr(obj, key, value)
    for key, value in request_periods.header_of(periods).items():
        setattr(obj, key, value)
    obj.employee_id = employee.id
    obj.company_id = employee.company_id or 0
    obj.department_id = employee.department_id or 0
    obj.leave_type_id = primary_type_id(pairs)
    obj.from_time = from_time
    obj.to_time = to_time
    obj.unit = UNIT_HOUR if hourly else UNIT_DAY
    obj.total_days = days
    obj.updated_by = user.id

    replace_lines(db, obj.id, pairs, user.id)
    request_periods.replace_periods(db, obj.id, periods, user.id)
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
        raise HTTPException(400, "Thiếu \"Lý do nghỉ\" — nhập đủ trước khi gửi duyệt.")
    if obj.total_days <= 0:
        raise HTTPException(400, "\"Tổng số ngày\" phải lớn hơn 0")


def check_required_attachment(db: Session, obj: LeaveRequest) -> None:
    """Loại nghỉ bật "Bắt buộc đính kèm" thì đơn phải có ít nhất một tệp (HR1-2, CR-661).

    Đơn nhiều loại: chỉ cần MỘT loại bật cờ là đơn phải có tệp. Tệp treo ở tờ đơn
    (`tab_file_link`, entity `leave_request`) chứ không ở từng dòng nên không phân
    biệt được tệp nào của loại nào — chặn theo "có hay chưa", nêu tên các loại đòi.
    Chỉ chạy lúc GỬI DUYỆT: lưu nháp để đính kèm sau, vì tệp chỉ treo được vào
    đơn đã có id.
    """
    type_ids = {ln.leave_type_id for ln in lines_of(db, obj.id)} or {obj.leave_type_id}
    required = (db.query(LeaveType.name)
                .filter(LeaveType.id.in_(type_ids), LeaveType.require_attachment.is_(True))
                .order_by(LeaveType.id).all())
    if not required:
        return
    from app.modules.attachment.model import FileLink  # tránh vòng import lúc nạp module

    has_file = (db.query(FileLink.id)
                .filter(FileLink.entity == "leave_request", FileLink.entity_id == obj.id)
                .first())
    if has_file:
        return
    names = ", ".join(f"\"{n}\"" for (n,) in required)
    raise HTTPException(
        400,
        f"Loại nghỉ {names} bắt buộc đính kèm giấy tờ (giấy khám bệnh, giấy chứng nhận…) — "
        "tải tệp lên ở mục \"Tệp đính kèm\" rồi gửi duyệt lại.")


def prepare_submit(db: Session, obj: LeaveRequest, user) -> Employee:
    """Mọi chốt chặn của bước GỬI DUYỆT, theo thứ tự rẻ trước đắt sau.

    Tách khỏi `submit()` để controller gọi được trước khi đụng vào bộ máy duyệt:
    trình phiếu xong mới phát hiện hết phép thì phải đi rút phiếu, và người dùng
    đã kịp thấy một phiếu duyệt hiện ra rồi biến mất.
    """
    if obj.status not in EDITABLE_STATUSES:
        raise HTTPException(400, "Đơn này đã gửi duyệt rồi")
    check_ready_to_submit(obj)
    check_required_attachment(db, obj)

    employee = get_employee(db, obj.employee_id)
    request_periods.raise_if_overlap(db, obj.employee_id, request_periods.periods_of(db, obj),
                                     exclude_id=obj.id)
    #  Kiểm TỪNG DÒNG, không kiểm tổng: mỗi loại nghỉ có sổ quỹ riêng, nên
    #  4 ngày = 3 phép năm + 1 không lương có thể qua trong khi 4 ngày phép năm
    #  thì hết phép.
    check_enough_lines(db, employee, obj)
    return employee


def mark_submitted(db: Session, obj: LeaveRequest, employee: Employee,
                   user, instance_id: int = 0) -> LeaveRequest:
    """Đặt đơn vào *Chờ duyệt* và GIỮ CHỖ quỹ. Gọi sau khi đã trình bộ máy duyệt."""
    obj.status = LR_PENDING
    obj.approval_instance_id = instance_id
    obj.submitted_at = datetime.now()
    obj.decision_note = ""
    obj.updated_by = user.id
    reserve_lines(db, employee, obj, user.id)
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
    if obj.status == LR_PENDING:
        release_lines(db, obj, actor)
    elif obj.status == LR_APPROVED:
        refund_lines(db, obj, actor)

    obj.status = LR_CANCELLED
    obj.decision_note = (reason or "")[:500]
    obj.decided_at = datetime.now()
    obj.updated_by = actor
    db.commit()
    db.refresh(obj)
    return obj
