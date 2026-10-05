"""NGÀY LÀM VIỆC — đếm số ngày nghỉ thật theo LỊCH LÀM VIỆC của chính người nghỉ, đã trừ ngày lễ.

Từ 05/10/2026 luật «chỉ nghỉ Chủ nhật» không còn cứng ở đây: mỗi ngày trong khoảng
nghỉ tra lịch của nhân sự (`work_schedule.resolver.load_day_plans`: Nhân sự > Phòng
ban > Pháp nhân > Hệ thống > mặc định T2–T7 08–17). Chưa gán lịch nào thì ra ĐÚNG
từng số như trước (bài tương đương đóng băng ở `test_lich_lam_viec_tinh_ngay_nghi.py`).

Đây là NƠI DUY NHẤT đoán số ngày nghỉ — đừng chép công thức sang service khác. Con số là
**GỢI Ý**: người dùng sửa đè được (`LeaveRequest.total_days` là cột nhập) vì lịch thật
luôn có ngoại lệ máy không biết (ca kíp, nghỉ bù, công trường chạy cả Chủ nhật).

Quy ước hai ô buổi giữ **y hệt** `suggested_days()` của giấy GNP — là MỐC chứ không phải
buổi (xem `constants.START_DAY_CREDIT`). Ở đây nó thành BITMASK nửa buổi:
`leave_mask` (nghỉ nửa nào) ∩ `work_mask` (phải làm nửa nào) → công = 0.5 × số nửa.
"""
from datetime import date, time

from sqlalchemy.orm import Session

from app.modules.employee.model import Employee
from app.modules.work_schedule import resolver
from app.modules.work_schedule.day_rules import (AM, FULL_DAY_SPEC, PM, DaySpec,
                                                 day_capacity, day_hours, work_mask,
                                                 worked_hours)

from .constants import SESSION_AFTERNOON, SESSION_FULL, SESSION_MORNING
from .holiday_calendar import MAX_RANGE_DAYS, date_range, holiday_dates  # noqa: F401 (tái xuất)


def leave_mask(day: date, from_date: date, to_date: date, from_session: int, to_session: int) -> int:
    """Nửa buổi nào của `day` nằm trong khoảng nghỉ (AM=1, PM=2).

    Ngày giữa = cả hai nửa. Ngày đầu: bắt đầu buổi Chiều → chỉ PM, còn lại → cả ngày.
    Ngày cuối: kết thúc buổi Sáng → chỉ AM, còn lại → cả ngày. Nghỉ gọn trong MỘT ngày
    = các nửa từ nửa-bắt-đầu tới nửa-kết-thúc (Chiều → Sáng = 0, khoảng trống).
    """
    if from_date == to_date:
        start = 1 if from_session == SESSION_AFTERNOON else 0
        end = 0 if to_session == SESSION_MORNING else 1
        return sum(1 << h for h in range(start, end + 1))
    if day == from_date:
        return PM if from_session == SESSION_AFTERNOON else AM | PM
    if day == to_date:
        return AM if to_session == SESSION_MORNING else AM | PM
    return AM | PM


def _plan_and_holidays(db: Session, from_date: date, to_date: date, company_id: int,
                       exclude_holiday: bool, employee: Employee | None):
    """(hàm lịch theo ngày, tập ngày lễ). `exclude_holiday=False` → bỏ qua lịch, mọi ngày
    là ngày làm trọn như cũ (thai sản đếm lịch dương)."""
    if not exclude_holiday:
        return (lambda _day: FULL_DAY_SPEC), set()
    if employee is not None:
        company_id = company_id or int(employee.company_id or 0)
    plan = resolver.load_day_plans(
        db, employee_id=int(employee.id or 0) if employee else 0,
        department_id=int(employee.department_id or 0) if employee else 0,
        company_id=company_id, from_date=from_date, to_date=to_date)
    return plan, holiday_dates(db, company_id, from_date, to_date)


def count_hourly_days(db: Session, from_date: date, to_date: date,
                      from_time: time, to_time: time,
                      *, company_id: int = 0, exclude_holiday: bool = True,
                      employee: Employee | None = None) -> float:
    """Số ngày phép của đơn khai THEO GIỜ — kể cả khi vắt qua nhiều ngày.

    Mỗi ngày làm góp `giờ nghỉ ÷ giờ làm CỦA NGÀY ĐÓ × công tối đa` (ngày 8h → giờ/8 như cũ;
    nửa ngày góp tối đa 0.5): ngày đầu `[from_time, hết giờ làm)`, ngày cuối
    `[đầu giờ làm, to_time)`, ở giữa trọn ngày. Ngày OFF / ngày lễ bỏ qua.
    """
    if to_date < from_date:
        return 0.0
    plan, holidays = _plan_and_holidays(db, from_date, to_date, company_id, exclude_holiday, employee)

    total = 0.0
    for day in date_range(from_date, to_date):
        spec: DaySpec = plan(day)
        if day in holidays or work_mask(spec) == 0 or spec.start is None or spec.end is None:
            continue
        lo = from_time if day == from_date else spec.start
        hi = to_time if day == to_date else spec.end
        whole = day_hours(spec)
        if whole <= 0:
            continue
        total += worked_hours(spec, lo, hi) / whole * day_capacity(spec)
    return round(total, 2)


def count_leave_days(db: Session, from_date: date, to_date: date,
                     from_session: int = SESSION_FULL, to_session: int = SESSION_FULL,
                     *, company_id: int = 0, exclude_holiday: bool = True,
                     employee: Employee | None = None) -> float:
    """Số ngày nghỉ GỢI Ý cho một khoảng.

    `exclude_holiday=False` thì đếm tuốt theo lịch dương, kể cả T7/CN/lễ — loại nghỉ dài
    liên tục (thai sản), khai bằng cột `LeaveType.exclude_holiday`.

    Trả `0.0` khi khoảng ngược thay vì nổ: chỗ CHẶN khoảng ngược là tầng schema.
    """
    if to_date < from_date:
        return 0.0
    plan, holidays = _plan_and_holidays(db, from_date, to_date, company_id, exclude_holiday, employee)

    total = 0.0
    for day in date_range(from_date, to_date):
        if day in holidays:
            continue
        mask = leave_mask(day, from_date, to_date, from_session, to_session) & work_mask(plan(day))
        total += 0.5 * bin(mask).count("1")
    return round(total, 2)


def schedule_name_on(db: Session, employee: Employee, on_date: date) -> str:
    """Tên lịch áp cho nhân sự vào `on_date` — để form hiện «Theo lịch …»."""
    return resolver.schedule_name_on(db, employee, on_date)
