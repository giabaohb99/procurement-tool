"""Luật THUẦN của quá trình công tác — chồng lấn, đóng dòng mở, chốt ÁP (A5-A8).

Tách khỏi `work_history_service.py` chỉ vì lý do MODULARIZATION (tệp kia đã gần
200 dòng), không phải vì khác nghiệp vụ: cả `work_history_service.create/update`
(cảnh báo + đóng dòng mở) và `work_history_apply_service.apply` (bốn chốt áp +
cờ `can_apply`) đều gọi vào đây.
"""
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.hr_work_history_codes import (APPLICABLE, MAIN_TRACK,
                                            POSITION_TRACK, WorkEventType)
from app.core.vn_time import vn_today

from .work_history_model import EmployeeWorkHistory


def safe_event_type(value: int) -> WorkEventType | None:
    """`WorkEventType(value)` nhưng KHÔNG ném — dữ liệu rác (nếu có) không được
    làm sập cả danh sách."""
    try:
        return WorkEventType(int(value))
    except ValueError:
        return None


def _dates_overlap(a_from: date, a_to: date | None, b_from: date, b_to: date | None) -> bool:
    a_end = a_to or date.max
    b_end = b_to or date.max
    return a_from <= b_end and b_from <= a_end


def overlap_warnings(db: Session, eid: int, row: EmployeeWorkHistory) -> list[str]:
    """Validate #6 — CẢNH BÁO, không chặn. Nhóm chính giao nhau nhóm chính;
    kiêm nhiệm CÙNG PHÒNG giao nhau kiêm nhiệm cùng phòng (khác phòng thì
    không cảnh báo — kiêm nhiệm hai phòng khác nhau cùng ngày là chuyện thường)."""
    et = safe_event_type(row.event_type)
    if et is None:
        return []

    others = (db.query(EmployeeWorkHistory)
              .filter(EmployeeWorkHistory.employee_id == eid,
                      EmployeeWorkHistory.id != (row.id or 0)).all())
    warnings: list[str] = []
    for other in others:
        other_et = safe_event_type(other.event_type)
        if other_et is None or not _dates_overlap(row.from_date, row.to_date,
                                                   other.from_date, other.to_date):
            continue
        if et in MAIN_TRACK and other_et in MAIN_TRACK:
            warnings.append(
                f"Chồng lấn nhóm chính với dòng #{other.id} (từ {other.from_date.isoformat()})")
        elif (et == WorkEventType.CONCURRENT and other_et == WorkEventType.CONCURRENT
              and row.department_id and row.department_id == other.department_id):
            warnings.append(
                f"Chồng lấn kiêm nhiệm cùng phòng ban với dòng #{other.id} "
                f"(từ {other.from_date.isoformat()})")
    return warnings


def close_open_main(db: Session, eid: int, new_from_date: date, actor_id: int,
                    exclude_id: int = 0) -> list[str]:
    """Validate #7 — dòng CHÍNH đang mở có `from_date` sớm hơn dòng mới thì đóng
    lại (`to_date = from_date mới − 1 ngày`). KHÔNG đụng dòng mở MỚI HƠN."""
    main_codes = [int(x) for x in MAIN_TRACK]
    rows = (db.query(EmployeeWorkHistory)
            .filter(EmployeeWorkHistory.employee_id == eid,
                    EmployeeWorkHistory.event_type.in_(main_codes),
                    EmployeeWorkHistory.to_date.is_(None),
                    EmployeeWorkHistory.from_date < new_from_date,
                    EmployeeWorkHistory.id != (exclude_id or 0))
            .all())
    closed: list[str] = []
    for r in rows:
        r.to_date = new_from_date - timedelta(days=1)
        r.updated_by = actor_id
        closed.append(f"#{r.id} (từ {r.from_date.isoformat()}) → đóng ngày {r.to_date.isoformat()}")
    return closed


def compute_can_apply(rows: list[EmployeeWorkHistory], today: date) -> dict[int, bool]:
    """Cờ `can_apply` cho CẢ DANH SÁCH — thuần Python trên dữ liệu ĐÃ fetch,
    không truy vấn thêm (tránh N+1). Bốn chốt của §Áp vào hồ sơ, KHÔNG xét quyền.

    ⚠️ Cùng luật với `apply_gate` dưới nhưng tính riêng (ở đây "dòng chính mới
    nhất" gom một lần cho cả danh sách đã có trong tay; `apply_gate` dùng một
    truy vấn SQL cho ĐÚNG MỘT dòng). Đổi luật ở hàm này thì nhớ đổi cả hai.
    """
    latest_main_from = max(
        (r.from_date for r in rows if safe_event_type(r.event_type) in MAIN_TRACK), default=None)

    result: dict[int, bool] = {}
    for r in rows:
        et = safe_event_type(r.event_type)
        ok = (
            et is not None and et in APPLICABLE
            and r.from_date <= today
            and not (et in POSITION_TRACK and r.to_date is not None and r.to_date < today)
            and not (et in MAIN_TRACK and latest_main_from is not None and latest_main_from > r.from_date)
        )
        result[r.id] = ok
    return result


def compute_is_current(rows: list[EmployeeWorkHistory], today: date) -> dict[int, bool]:
    """Cờ `is_current` (huy hiệu «Đang hiệu lực»/«Hiện tại») cho CẢ DANH SÁCH.

    Trước 05/10/2026 chỉ xét `to_date` nên hai trường hợp bị báo nhầm:
    - nhập BÙ dòng chính cũ hơn mà không đóng (vd Bổ nhiệm 03/10 nhập sau Điều
      chuyển 04/10) → cả hai dòng cùng «Đang hiệu lực»;
    - dòng có `from_date` ở TƯƠNG LAI → «Đang hiệu lực» dù chưa tới ngày.
    Nay dòng nhóm chính còn bị một dòng nhóm chính KHÁC bắt đầu muộn hơn, đã tới
    ngày (`from_date <= today`), thay thế. Kiêm nhiệm/Khác không bị thay theo
    kiểu này (song song là chuyện thường).
    """
    main_starts = sorted(
        r.from_date for r in rows
        if safe_event_type(r.event_type) in MAIN_TRACK and r.from_date <= today)

    result: dict[int, bool] = {}
    for r in rows:
        active = r.from_date <= today and (r.to_date is None or r.to_date >= today)
        if active and safe_event_type(r.event_type) in MAIN_TRACK:
            active = not any(start > r.from_date for start in main_starts)
        result[r.id] = active
    return result


def apply_gate(db: Session, eid: int, row: EmployeeWorkHistory, today: date | None = None) -> str | None:
    """Bốn chốt CHUNG của việc ÁP cho ĐÚNG MỘT dòng — dùng ở
    `work_history_apply_service.apply`. Trả câu lỗi (400), hoặc `None` nếu qua
    hết. Xem so sánh với `compute_can_apply` ở ghi chú của hàm đó."""
    today = today or vn_today()
    et = safe_event_type(row.event_type)
    if et is None or et not in APPLICABLE:
        return "Loại sự kiện này không áp được vào hồ sơ"
    if row.from_date > today:
        return "Chưa tới ngày hiệu lực — quay lại bấm Áp vào hồ sơ khi tới ngày"
    if et in POSITION_TRACK and row.to_date is not None and row.to_date < today:
        return "Dòng này đã kết thúc, không áp được vào hồ sơ"
    if et in MAIN_TRACK:
        main_codes = [int(x) for x in MAIN_TRACK]
        latest = (db.query(func.max(EmployeeWorkHistory.from_date))
                  .filter(EmployeeWorkHistory.employee_id == eid,
                          EmployeeWorkHistory.event_type.in_(main_codes))
                  .scalar())
        if latest is not None and latest > row.from_date:
            return ("Đã có dòng chính khác với ngày hiệu lực muộn hơn — chỉ áp được "
                     "đúng dòng chính mới nhất")
    return None
