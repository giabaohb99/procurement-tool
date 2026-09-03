"""NGÀY LÀM VIỆC — đếm số ngày nghỉ thật, đã trừ thứ Bảy / Chủ nhật / ngày lễ.

Đây là thứ `document/type_metadata.suggested_days()` cố ý **không** làm được ở
CR-159, và tệp đó ghi thẳng lý do: lúc ấy chưa có bảng lịch làm việc nào, nên
"đoán ra một con số trông có vẻ chính xác còn tệ hơn đưa ra con số thô". Nay đã
có `tab_holiday` nên đoán được thật, và đây là NƠI DUY NHẤT đoán — đừng chép
công thức sang service khác.

Vẫn giữ nguyên một điều: con số này là **GỢI Ý**. Người dùng sửa đè được
(`LeaveRequest.total_days` là cột nhập), vì lịch làm việc thật luôn có ngoại lệ
mà máy không biết — ca kíp, nghỉ bù, công trường chạy cả Chủ nhật.

⚠️ Quy ước hai ô buổi giữ **y hệt** `suggested_days()`: `from_session` /
`to_session` nói *buổi nào của ngày đó được nghỉ*, nên `morning` và `afternoon`
đều là **0.5** ở cả hai đầu. Đổi quy ước ở đây thôi thì cùng một tờ đơn ra hai
con số khác nhau tùy người nhập qua màn Nghỉ phép hay qua giấy GNP.
"""
from datetime import date, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .catalog_model import Holiday
from .constants import SESSION_CREDIT, SESSION_FULL

#  Thứ Bảy = 5, Chủ nhật = 6 theo `date.weekday()`.
WEEKEND_DAYS = (5, 6)

#  Trần bảo hiểm cho vòng lặp ngày. Thai sản 6 tháng là ~180 ngày; đơn dài hơn
#  một năm là dữ liệu hỏng hoặc gõ nhầm năm, và ta không muốn một ô nhập sai kéo
#  theo một vòng lặp mười nghìn lượt.
MAX_RANGE_DAYS = 400


def holiday_dates(db: Session, company_id: int, from_date: date, to_date: date) -> set[date]:
    """Tập ngày lễ áp cho pháp nhân này, trong khoảng đã cho.

    Gộp HAI nguồn: dòng dùng chung (`company_id = 0`) và dòng riêng của pháp
    nhân. Đây chính là phép gộp mà khuôn một-cột của `apply_scope` không diễn
    đạt được — lý do `holiday` khai `PUBLIC` ở `SCOPE_FIELDS`.

    Ngày lễ LẶP hằng năm (`is_recurring`) khớp theo ngày/tháng, bất kể năm lưu
    trong bảng — nhập «01/01» một lần là năm nào cũng nhận. Tết Âm lịch thì
    không lặp được vì trôi theo lịch âm, mỗi năm phải nhập một lần.
    """
    rows = (db.query(Holiday)
            .filter(Holiday.is_active.is_(True),
                    or_(Holiday.company_id == 0, Holiday.company_id == company_id))
            .all())

    fixed = {r.date for r in rows if not r.is_recurring and r.date}
    recurring = {(r.date.month, r.date.day) for r in rows if r.is_recurring and r.date}
    if not recurring:
        return {d for d in fixed if from_date <= d <= to_date}

    #  Chỉ trải các ngày LẶP ra trong đúng khoảng đang hỏi — trải cả năm thì
    #  tốn công vô ích với đơn nghỉ hai ngày.
    out = {d for d in fixed if from_date <= d <= to_date}
    for day in date_range(from_date, to_date):
        if (day.month, day.day) in recurring:
            out.add(day)
    return out


def date_range(from_date: date, to_date: date):
    """Sinh từng ngày trong khoảng, bao gồm cả hai đầu. Chặn ở `MAX_RANGE_DAYS`."""
    day, guard = from_date, 0
    while day <= to_date and guard < MAX_RANGE_DAYS:
        yield day
        day += timedelta(days=1)
        guard += 1


def is_working_day(day: date, holidays: set[date]) -> bool:
    return day.weekday() not in WEEKEND_DAYS and day not in holidays


def session_credit(day: date, from_date: date, to_date: date,
                   from_session: int, to_session: int) -> float:
    """Số công của MỘT ngày trong khoảng nghỉ, chưa xét lễ / cuối tuần.

    Ngày ở giữa luôn là 1.0. Hai ngày đầu và cuối lấy theo ô buổi. Nghỉ gọn
    trong MỘT ngày thì hai ô buổi nói về cùng một buổi — lấy một cái, đúng như
    `suggested_days()` đang làm.
    """
    if from_date == to_date:
        return SESSION_CREDIT.get(from_session, 1.0)
    if day == from_date:
        return SESSION_CREDIT.get(from_session, 1.0)
    if day == to_date:
        return SESSION_CREDIT.get(to_session, 1.0)
    return 1.0


def count_leave_days(db: Session, from_date: date, to_date: date,
                     from_session: int = SESSION_FULL, to_session: int = SESSION_FULL,
                     *, company_id: int = 0, exclude_holiday: bool = True) -> float:
    """Số ngày nghỉ GỢI Ý cho một khoảng.

    `exclude_holiday=False` thì đếm tuốt, kể cả T7/CN/lễ — đó là loại nghỉ dài
    liên tục (thai sản nghỉ 6 tháng thì không ai bù cuối tuần), khai bằng cột
    `LeaveType.exclude_holiday`.

    Trả `0.0` khi khoảng ngược (`to_date < from_date`) thay vì nổ: chỗ CHẶN
    khoảng ngược là tầng schema, ở đây mà ném nữa thì cùng một lỗi báo hai câu
    khác nhau tùy đường đi.
    """
    if to_date < from_date:
        return 0.0

    holidays = (holiday_dates(db, company_id, from_date, to_date)
                if exclude_holiday else set())

    total = 0.0
    for day in date_range(from_date, to_date):
        if exclude_holiday and not is_working_day(day, holidays):
            continue
        total += session_credit(day, from_date, to_date, from_session, to_session)
    return round(total, 2)
