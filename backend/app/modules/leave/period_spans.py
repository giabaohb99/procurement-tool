"""KHOẢNG NGÀY ĐỂ ĐỌC (duoc-CR-683) — một đơn nghỉ = một hoặc nhiều khoảng liền.

Mọi chỗ hỏi *"ngày D có nghỉ không"* (Lịch nghỉ, "Ai làm / ai nghỉ", hồ sơ làm việc,
tải việc, chốt trùng ngày) phải đọc qua đây, KHÔNG đọc `[from_date, to_date]` ở đầu
đơn: đầu đơn là bao ngoài, nuốt cả khe giữa các khoảng.

Đường rơi: đơn chưa có dòng `tab_leave_request_period` (dữ liệu dựng tay không qua
service, hoặc đơn cũ chưa backfill) được coi là MỘT khoảng lấy từ đầu đơn.
"""
from dataclasses import dataclass
from datetime import date, time

from sqlalchemy.orm import Session

from .constants import SESSION_AFTERNOON, SESSION_MORNING
from .request_model import LeaveRequest, LeaveRequestPeriod


@dataclass(frozen=True)
class PeriodView:
    """Một khoảng ngày dạng thuần dữ liệu — vừa là đầu vào đã chuẩn hóa, vừa là bản đọc."""

    from_date: date
    to_date: date
    from_session: int = 1
    to_session: int = 1
    days: float = 0.0
    id: int = 0            # 0 = khoảng dựng từ đầu đơn (chưa có dòng trong DB)
    sort_order: int = 0


@dataclass(frozen=True)
class LeaveSpan:
    """Một khoảng nghỉ của một đơn, kèm đủ thông tin để vẽ/đếm mà khỏi đọc lại đơn."""

    id: int
    code: str
    status: int
    employee_id: int
    leave_type_id: int
    from_date: date
    to_date: date
    from_session: int
    to_session: int
    from_time: time | None
    to_time: time | None


def span_of(req: LeaveRequest, period=None) -> LeaveSpan:
    """Span của đơn. Có `period` thì lấy ngày/buổi của khoảng đó, `None` thì lấy đầu đơn."""
    src = period if period is not None else req
    return LeaveSpan(
        id=req.id, code=req.code, status=req.status, employee_id=req.employee_id,
        leave_type_id=req.leave_type_id,
        from_date=src.from_date, to_date=src.to_date,
        from_session=src.from_session, to_session=src.to_session,
        from_time=req.from_time, to_time=req.to_time)


def header_period(req: LeaveRequest) -> PeriodView:
    """Khoảng dựng từ đầu đơn — đường rơi khi đơn chưa có dòng khoảng."""
    return PeriodView(from_date=req.from_date, to_date=req.to_date,
                      from_session=req.from_session, to_session=req.to_session,
                      days=float(req.total_days or 0.0))


def _view(row: LeaveRequestPeriod) -> PeriodView:
    return PeriodView(from_date=row.from_date, to_date=row.to_date,
                      from_session=row.from_session, to_session=row.to_session,
                      days=float(row.days or 0.0), id=row.id, sort_order=row.sort_order)


def periods_by_request(db: Session, request_ids) -> dict[int, list[PeriodView]]:
    """`{id đơn: [khoảng]}` cho nhiều đơn: 1 truy vấn (+1 chỉ khi có đơn chưa có dòng khoảng).

    Mọi id đều có mặt trong kết quả (rơi về đầu đơn), trừ id không tồn tại.
    """
    ids = {int(i) for i in request_ids if i}
    if not ids:
        return {}
    out: dict[int, list[PeriodView]] = {}
    rows = (db.query(LeaveRequestPeriod)
            .filter(LeaveRequestPeriod.request_id.in_(ids))
            .order_by(LeaveRequestPeriod.request_id, LeaveRequestPeriod.sort_order,
                      LeaveRequestPeriod.id).all())
    for row in rows:
        out.setdefault(row.request_id, []).append(_view(row))
    missing = ids - set(out)
    if missing:
        for req in db.query(LeaveRequest).filter(LeaveRequest.id.in_(missing)).all():
            out[req.id] = [header_period(req)]
    return out


def _fmt(d: date, with_year: bool) -> str:
    return d.strftime("%d/%m/%Y") if with_year else d.strftime("%d/%m")


def period_text(periods) -> str:
    """Chữ đọc được cho người/AI: "27/10/2026 · 03/11 (chiều) → 07/11/2026".

    Năm chỉ hiện ở khoảng đầu và ở đầu cuối mỗi khoảng nhiều ngày khi khác năm khoảng đầu.
    """
    parts = []
    base_year = None
    for p in periods:
        if base_year is None:
            base_year = p.from_date.year
        start = _fmt(p.from_date, p.from_date.year != base_year or not parts)
        if p.from_session == SESSION_AFTERNOON:
            start += " (chiều)"
        if p.to_date == p.from_date:
            if p.to_session == SESSION_MORNING and p.from_session != SESSION_AFTERNOON:
                start += " (sáng)"
            parts.append(start)
            continue
        end = _fmt(p.to_date, True)
        if p.to_session == SESSION_MORNING:
            end += " (sáng)"
        parts.append(f"{start} → {end}")
    return " · ".join(parts)
