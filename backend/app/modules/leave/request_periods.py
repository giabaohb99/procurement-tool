"""KHOẢNG NGÀY CỦA ĐƠN NGHỈ (duoc-CR-683) — chuẩn hóa · kiểm · ghi · chốt trùng ngày.

`request_service` gọi vào đây; đây là nơi DUY NHẤT hiểu "đơn có nhiều khoảng":

    normalize_create / normalize_update  →  [PeriodView] (đã sắp theo ngày bắt đầu)
    check_periods                        →  R1–R5: số lượng · theo giờ · chồng ngày · bao ngoài · cùng năm
    header_of / calendar_days            →  đầu đơn dẫn xuất · trần số ngày dương lịch
    replace_periods / periods_of         →  ghi / đọc (đọc rơi về đầu đơn)
    raise_if_overlap                     →  chốt trùng ngày với đơn khác, MỘT truy vấn
"""
from dataclasses import replace
from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .constants import HOLDING_STATUSES, SESSION_HOURLY
from .holiday_calendar import MAX_RANGE_DAYS
from .period_spans import PeriodView, header_period, period_text, periods_by_request
from .request_model import LeaveRequest, LeaveRequestPeriod
from .schema import MAX_PERIODS  # noqa: F401 — nguồn DUY NHẤT của trần số khoảng

PeriodIn = PeriodView

#  Các khóa ngày/buổi ở đầu đơn — vắng `periods` mà có khóa nào trong này là sửa "khoảng đang có".
HEADER_KEYS = ("from_date", "to_date", "from_session", "to_session")


def label_of(index: int, p: PeriodView) -> str:
    """"Khoảng thứ 2 (03/11 → 07/11)" — để câu báo lỗi chỉ đúng khoảng."""
    return f"Khoảng thứ {index + 1} ({p.from_date:%d/%m} → {p.to_date:%d/%m})"


def is_hourly_period(p: PeriodView) -> bool:
    return SESSION_HOURLY in (p.from_session, p.to_session)


# ── Chuẩn hóa đầu vào ─────────────────────────────────────────────────────────

def _from_items(items) -> list[PeriodView]:
    return [PeriodView(from_date=i.from_date, to_date=i.to_date,
                       from_session=i.from_session, to_session=i.to_session)
            for i in items]


def normalize_create(data) -> list[PeriodView]:
    """`periods` nếu có, không thì MỘT khoảng từ cặp `from_date`/`to_date` (tương thích ngược)."""
    if data.periods:
        return _from_items(data.periods)
    return [PeriodView(from_date=data.from_date, to_date=data.to_date,
                       from_session=data.from_session, to_session=data.to_session)]


def periods_of(db: Session, obj: LeaveRequest) -> list[PeriodView]:
    """Khoảng của một đơn; chưa có dòng thì rơi về đầu đơn."""
    return periods_by_request(db, [obj.id]).get(obj.id) or [header_period(obj)]


def normalize_update(db: Session, obj: LeaveRequest, values: dict, data) -> list[PeriodView]:
    """Khoảng SAU khi sửa (R11): có `periods` → ghi đè; vắng mà có ô ngày/buổi → sửa khoảng
    duy nhất (đơn ≥2 khoảng thì chặn); vắng hết → giữ khoảng đang có."""
    if data.periods is not None:
        if not data.periods:
            raise HTTPException(400, "Đơn cần ít nhất một khoảng ngày nghỉ")
        return _from_items(data.periods)
    current = periods_of(db, obj)
    given = {k: values[k] for k in HEADER_KEYS if values.get(k) is not None}
    if not given:
        return current
    if len(current) > 1:
        raise HTTPException(
            400, f"Đơn có {len(current)} khoảng ngày — gửi đủ danh sách khoảng khi sửa ngày")
    first = current[0]
    return [PeriodView(**{k: given.get(k, getattr(first, k)) for k in HEADER_KEYS})]


# ── Kiểm ──────────────────────────────────────────────────────────────────────

def check_count_and_hourly(periods: list[PeriodView]) -> None:
    """R1 (số khoảng) + R3 (theo giờ thì đúng một khoảng). Chạy TRƯỚC kiểm từng khoảng."""
    if not periods:
        raise HTTPException(400, "Đơn cần ít nhất một khoảng ngày nghỉ")
    if len(periods) > MAX_PERIODS:
        raise HTTPException(400, f"Một đơn khai tối đa {MAX_PERIODS} khoảng ngày.")
    if len(periods) > 1 and any(is_hourly_period(p) for p in periods):
        raise HTTPException(
            400, "Nghỉ theo giờ chỉ khai được một khoảng ngày. Bỏ bớt khoảng, hoặc chọn lại buổi nghỉ.")


def check_layout(periods: list[PeriodView]) -> list[PeriodView]:
    """R2, R4, R5 trên các khoảng đã qua kiểm từng khoảng. Trả danh sách đã sắp theo ngày."""
    ordered = sorted(periods, key=lambda p: (p.from_date, p.to_date))
    for i in range(len(ordered) - 1):
        if ordered[i].to_date >= ordered[i + 1].from_date:
            raise HTTPException(
                400, f"{label_of(i, ordered[i])} và {label_of(i + 1, ordered[i + 1])} "
                     "chồng ngày nhau — các khoảng không được trùng ngày.")
    span = (ordered[-1].to_date - ordered[0].from_date).days + 1
    if span > MAX_RANGE_DAYS:
        raise HTTPException(
            400, f"Các khoảng nghỉ trải dài {span} ngày, vượt trần {MAX_RANGE_DAYS} ngày của "
                 "một tờ đơn. Kiểm lại năm ở các ô ngày.")
    if len(ordered) > 1 and len({p.from_date.year for p in ordered} | {p.to_date.year for p in ordered}) > 1:
        #  Q1 (26/10/2026): quỹ phép trừ theo năm của khoảng đầu — vắt năm thì trừ nhầm năm.
        raise HTTPException(
            422, "Đơn nhiều khoảng ngày phải nằm trong cùng một năm. Tách thành hai đơn: "
                 "một đơn cho năm trước, một đơn cho năm sau.")
    return ordered


def with_days(periods: list[PeriodView], days: list[float]) -> list[PeriodView]:
    return [replace(p, days=d, sort_order=i) for i, (p, d) in enumerate(zip(periods, days))]


# ── Dẫn xuất · ghi ────────────────────────────────────────────────────────────

def header_of(periods: list[PeriodView]) -> dict:
    """Đầu đơn dẫn xuất (R9): khoảng đầu ↔ khoảng cuối."""
    return {"from_date": periods[0].from_date, "from_session": periods[0].from_session,
            "to_date": periods[-1].to_date, "to_session": periods[-1].to_session}


def calendar_days(periods: list[PeriodView]) -> int:
    """Σ số ngày DƯƠNG LỊCH của các khoảng (R8) — khe giữa các khoảng không tính."""
    return sum((p.to_date - p.from_date).days + 1 for p in periods)


def replace_periods(db: Session, request_id: int, periods: list[PeriodView], actor: int) -> None:
    """Ghi đè cả danh sách khoảng (xóa rồi thêm, cùng lý lẽ với `replace_lines`)."""
    db.query(LeaveRequestPeriod).filter(LeaveRequestPeriod.request_id == request_id).delete()
    for i, p in enumerate(periods):
        db.add(LeaveRequestPeriod(
            request_id=request_id, from_date=p.from_date, from_session=p.from_session,
            to_date=p.to_date, to_session=p.to_session, days=p.days, sort_order=i,
            created_by=actor, updated_by=actor))


# ── Chốt trùng ngày (R10) ─────────────────────────────────────────────────────

def find_overlap(db: Session, employee_id: int, periods: list[PeriodView],
                 exclude_id: int = 0) -> LeaveRequest | None:
    """Đơn GIỮ CHỖ khác của cùng người có khoảng nào chồng với khoảng nào của `periods`.

    Một truy vấn: đơn LEFT JOIN khoảng, `coalesce` rơi về đầu đơn khi chưa có dòng khoảng.
    Lọc trước bằng bao ngoài để ăn `ix_leave_request_range`, rồi OR tối đa 20 vế.
    Ngày khe giữa hai khoảng của đơn kia KHÔNG chặn.
    """
    lo = min(p.from_date for p in periods)
    hi = max(p.to_date for p in periods)
    P = LeaveRequestPeriod
    other_from = func.coalesce(P.from_date, LeaveRequest.from_date)
    other_to = func.coalesce(P.to_date, LeaveRequest.to_date)
    q = (db.query(LeaveRequest)
         .outerjoin(P, P.request_id == LeaveRequest.id)
         .filter(LeaveRequest.employee_id == employee_id,
                 LeaveRequest.is_deleted.is_(False),
                 LeaveRequest.status.in_(HOLDING_STATUSES),
                 LeaveRequest.from_date <= hi, lo <= LeaveRequest.to_date,
                 or_(*[and_(other_from <= p.to_date, p.from_date <= other_to) for p in periods])))
    if exclude_id:
        q = q.filter(LeaveRequest.id != exclude_id)
    return q.first()


def raise_if_overlap(db: Session, employee_id: int, periods: list[PeriodView],
                     exclude_id: int = 0) -> None:
    other = find_overlap(db, employee_id, periods, exclude_id)
    if other is not None:
        raise HTTPException(
            400, f"Đã có đơn \"{other.code}\" nghỉ {period_text(periods_of(db, other))} "
                 "trùng khoảng ngày này.")


def single_period(from_date: date, to_date: date, from_session: int = 1,
                  to_session: int = 1) -> PeriodView:
    return PeriodView(from_date=from_date, to_date=to_date,
                      from_session=from_session, to_session=to_session)
