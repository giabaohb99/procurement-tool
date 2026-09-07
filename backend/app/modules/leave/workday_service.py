"""NGÀY LÀM VIỆC — đếm số ngày nghỉ thật, đã trừ ngày nghỉ tuần và ngày lễ.

⚠️ **DEGO Holding làm cả ngày thứ Bảy**, nên "nghỉ tuần" ở đây chỉ có Chủ nhật.
Xem `WEEKEND_DAYS` bên dưới — đừng đọc lướt rồi tưởng theo tuần 5 ngày.

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
from datetime import date, time, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .catalog_model import Holiday
from .constants import (LUNCH_END, LUNCH_START, SESSION_CREDIT, SESSION_FULL,
                        WORK_DAY_END, WORK_DAY_START, WORK_HOURS_PER_DAY)

#  Ngày KHÔNG tính vào phép, theo `date.weekday()` (Thứ Hai = 0 … Chủ nhật = 6).
#
#  ⚠️ **DEGO Holding làm cả ngày thứ Bảy**, nên chỉ Chủ nhật nằm ở đây (chốt
#  04/09/2026). Trước đó khai `(5, 6)` — copy theo mặc định "tuần làm 5 ngày" —
#  và luật đó SAI với công ty này theo đúng hướng tốn tiền: nghỉ riêng một thứ
#  Bảy bị tính **0 ngày phép**, tức nghỉ không mất gì; còn nghỉ từ thứ Sáu sang
#  thứ Hai thì trừ 2 thay vì 3. Sai âm thầm, vì con số vẫn ra một số hợp lý.
#
#  Áp CHUNG cho mọi pháp nhân (chốt cùng ngày). Nơi nào lịch khác thì mở cấu
#  hình theo `company_id` như `tab_holiday` đang làm — đừng thêm ngoại lệ rải
#  rác trong mã.
WEEKEND_DAYS = (6,)

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


def worked_hours(start: time, end: time) -> float:
    """Số GIỜ CÔNG trong khoảng `[start, end)` của một ngày làm việc.

    Cắt theo khung giờ làm (`WORK_DAY_START`/`WORK_DAY_END`) rồi trừ phần chồng
    lên giờ nghỉ trưa. Nhờ vậy nghỉ nguyên ngày (8:00 → 17:00) ra đúng 8 giờ,
    còn nghỉ 11:30 → 13:30 chỉ tính 1 giờ chứ không phải 2 — người ta có làm gì
    trong giờ ăn trưa đâu mà trừ phép.

    Khai giờ NGOÀI khung làm việc (nghỉ lúc 19:00) thì phần ngoài không tính:
    vắng mặt ngoài giờ làm không phải là nghỉ phép.
    """
    lo = max(_minutes(start), _minutes(WORK_DAY_START))
    hi = min(_minutes(end), _minutes(WORK_DAY_END))
    if hi <= lo:
        return 0.0
    lunch = max(0, min(hi, _minutes(LUNCH_END)) - max(lo, _minutes(LUNCH_START)))
    return (hi - lo - lunch) / 60.0


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def count_hourly_days(db: Session, from_date: date, to_date: date,
                      from_time: time, to_time: time,
                      *, company_id: int = 0, exclude_holiday: bool = True) -> float:
    """Số ngày phép của một đơn khai THEO GIỜ — kể cả khi vắt qua nhiều ngày.

    Nghỉ *từ 14:00 ngày 07 đến 10:00 ngày 09* là chuyện thường (đi công tác về
    muộn, đi viện hai hôm), nên đây KHÔNG bó trong một ngày:

    * ngày đầu tính từ giờ khai tới hết giờ làm;
    * ngày cuối tính từ đầu giờ làm tới giờ khai;
    * ngày ở giữa tính trọn `WORK_HOURS_PER_DAY`;
    * ngày nào là T7/CN/lễ thì bỏ qua (trừ loại nghỉ khai `exclude_holiday=False`).

    Gọn trong MỘT ngày thì chỉ còn phép trừ hai đầu giờ — nhánh riêng ở dòng đầu.
    """
    if to_date < from_date:
        return 0.0

    holidays = (holiday_dates(db, company_id, from_date, to_date)
                if exclude_holiday else set())

    def is_workday(day: date) -> bool:
        return not exclude_holiday or is_working_day(day, holidays)

    if from_date == to_date:
        return round(worked_hours(from_time, to_time) / WORK_HOURS_PER_DAY, 2)\
            if is_workday(from_date) else 0.0

    hours = 0.0
    for day in date_range(from_date, to_date):
        if not is_workday(day):
            continue
        if day == from_date:
            hours += worked_hours(from_time, WORK_DAY_END)
        elif day == to_date:
            hours += worked_hours(WORK_DAY_START, to_time)
        else:
            hours += WORK_HOURS_PER_DAY
    return round(hours / WORK_HOURS_PER_DAY, 2)


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
