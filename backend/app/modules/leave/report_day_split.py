"""CHIA NGÀY NGHỈ THEO KỲ / MỐC cho báo cáo Tình hình nghỉ phép (duoc-CR-686).

Vì sao: `days_approved`/`days_pending` cũ tính TOÀN BỘ số ngày của đơn vào kỳ chứa NGÀY BẮT ĐẦU.
Đơn 28/09 → 03/10 hiện hết 5 ngày ở tháng 9, tháng 10 không có gì; đơn bắt đầu 29/08 nghỉ sang
tháng 9 thì tháng 9 thiếu. Luật mới: mỗi đơn chỉ góp PHẦN NGÀY rơi vào kỳ / mốc xu hướng.

Cách chia (mỗi đơn):
  - Theo TỪNG KHOẢNG (`tab_leave_request_period`, `period_spans.periods_by_request`): khoảng góp
    phần `days_khoảng / tổng days các khoảng` của đơn (tổng 0 → chia đều số khoảng).
  - Trong một khoảng, trọng số mỗi ngày = số nửa buổi VỪA nghỉ VỪA phải làm (lịch làm việc của
    chính người nghỉ `load_day_plans_many` + ngày lễ + `leave_mask`), ngày lễ = 0. Tổng trọng số
    bằng 0 (cả khoảng rơi vào ngày nghỉ/lễ) → chia đều theo ngày lịch.
  - Loại nghỉ `exclude_holiday=False` (thai sản...) đếm lịch dương: bỏ qua lịch + ngày lễ.
  - Đơn nhiều loại nghỉ: mỗi dòng nhận cùng tỷ lệ → dòng góp `line.days × tỷ lệ` (= chia dòng
    theo `line.days / tổng`).

Chỉ tính lại bằng Python cho đơn VẮT QUA biên (kỳ hoặc mốc); đơn gọn trong một mốc giữ nguyên
đường SQL. Số truy vấn CỐ ĐỊNH (đơn · dòng · khoảng · 3 truy vấn lịch · ngày lễ), không tăng theo
số đơn. Phòng ban/công ty của lịch lấy theo cột chép trên đơn (lúc lập) — xem ghi chú báo cáo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Callable

from sqlalchemy.orm import Session

from app.modules.leave.constants import LR_APPROVED, LR_PENDING
from app.modules.leave.holiday_calendar import MAX_RANGE_DAYS, date_range, holiday_names_many
from app.modules.leave.period_spans import periods_by_request
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine
from app.modules.leave.workday_service import leave_mask
from app.modules.work_schedule.day_rules import FULL_DAY_SPEC, work_mask
from app.modules.work_schedule.resolver_many import load_day_plans_many

#  Đơn góp ngày vào báo cáo khi ở một trong hai trạng thái này.
DAY_STATUSES = (LR_APPROVED, LR_PENDING)


@dataclass
class SplitRequest:
    """Một đơn vắt qua biên, kèm phần ngày (tỷ lệ) rơi vào từng ngày lịch."""

    id: int
    status: int
    code: str
    from_date: date
    to_date: date
    company_id: int
    department_id: int
    employee_id: int
    leave_type_id: int
    lines: list[tuple[int, float]] = field(default_factory=list)   # (loại nghỉ, số ngày)
    day_share: dict[date, float] = field(default_factory=dict)     # tổng ≈ 1

    def share_where(self, pred: Callable[[date], bool]) -> float:
        """Phần (0..1) của đơn rơi vào các ngày thỏa `pred`."""
        return sum(s for d, s in self.day_share.items() if pred(d))

    def line_days(self, type_id: int | None = None) -> float:
        return sum(d for t, d in self.lines if type_id is None or t == type_id)


def overlapping_rows(base_query, d_from: date, d_to: date, multi_day_only: bool = True):
    """Đơn chờ/đã duyệt CÓ NGÀY rơi vào [d_from, d_to] (bắt đầu trước kỳ cũng tính). 1 truy vấn.
    `multi_day_only`: đơn trong MỘT ngày không bao giờ vắt biên nên bỏ ngay ở SQL."""
    q = base_query.filter(LeaveRequest.status.in_(DAY_STATUSES), LeaveRequest.from_date <= d_to,
                          LeaveRequest.to_date >= d_from)
    if multi_day_only:
        q = q.filter(LeaveRequest.to_date > LeaveRequest.from_date)
    return q.with_entities(
        LeaveRequest.id, LeaveRequest.status, LeaveRequest.code, LeaveRequest.from_date,
        LeaveRequest.to_date, LeaveRequest.company_id, LeaveRequest.department_id,
        LeaveRequest.employee_id, LeaveRequest.leave_type_id).all()


def _holidays_chunked(db: Session, company_ids, lo: date, hi: date) -> dict[int, set[date]]:
    """Ngày lễ theo pháp nhân cho [lo, hi]. `holiday_names_many` chỉ trải ngày lặp trong tối đa
    `MAX_RANGE_DAYS` (400) ngày, nên cửa sổ dài được cắt thành các khúc ≤ 400 ngày — số truy vấn
    theo độ dài cửa sổ (≈ số năm), KHÔNG theo số đơn."""
    out: dict[int, set[date]] = {int(c or 0): set() for c in company_ids}
    start = lo
    while start <= hi:
        end = min(start + timedelta(days=MAX_RANGE_DAYS - 1), hi)
        for cid, names in holiday_names_many(db, out.keys(), start, end).items():
            out[cid] |= set(names)
        start = end + timedelta(days=1)
    return out


def _day_weights(period, spec_at: Callable[[date], object], holidays: set[date]) -> dict[date, float]:
    """Trọng số từng ngày của MỘT khoảng, đã chuẩn hóa tổng = 1 (rỗng nếu khoảng ngược)."""
    weights = {}
    for day in date_range(period.from_date, period.to_date):
        mask = leave_mask(day, period.from_date, period.to_date, period.from_session,
                          period.to_session)
        weights[day] = 0.0 if day in holidays else 0.5 * bin(mask & work_mask(spec_at(day))).count("1")
    total = sum(weights.values())
    if total <= 0:   # cả khoảng là ngày nghỉ/lễ → chia đều theo ngày lịch
        return {d: 1 / len(weights) for d in weights}
    return {d: w / total for d, w in weights.items()}


def build_split_requests(db: Session, rows, calendar_types: set[int]) -> list[SplitRequest]:
    """Dựng `SplitRequest` cho `rows` (từ `overlapping_rows`, đã lọc đơn vắt biên): 1 truy vấn
    dòng + khoảng (+1 nếu thiếu dòng khoảng) + 3 truy vấn lịch + 1 truy vấn ngày lễ."""
    if not rows:
        return []
    ids = [r.id for r in rows]
    lines: dict[int, list[tuple[int, float]]] = {}
    for ln in (db.query(LeaveRequestLine.request_id, LeaveRequestLine.leave_type_id,
                        LeaveRequestLine.days).filter(LeaveRequestLine.request_id.in_(ids)).all()):
        lines.setdefault(ln.request_id, []).append((ln.leave_type_id or 0, float(ln.days or 0)))
    periods = periods_by_request(db, ids)
    spans = [p for plist in periods.values() for p in plist]
    lo, hi = min(p.from_date for p in spans), max(p.to_date for p in spans)
    emps = {r.employee_id: SimpleNamespace(id=r.employee_id, department_id=r.department_id,
                                           company_id=r.company_id) for r in rows}
    plans = load_day_plans_many(db, emps.values(), lo, hi)
    holidays = _holidays_chunked(db, {r.company_id for r in rows}, lo, hi)

    out = []
    for r in rows:
        plist = periods.get(r.id) or []
        calendar = r.leave_type_id in calendar_types
        spec_at = ((lambda _d: FULL_DAY_SPEC) if calendar
                   else (lambda d, e=r.employee_id: plans.at(e, d)[0]))
        hol = set() if calendar else holidays.get(int(r.company_id or 0), set())
        pdays = sum(p.days for p in plist)
        share: dict[date, float] = {}
        for p in plist:
            part = (p.days / pdays) if pdays > 0 else 1 / len(plist)
            for day, w in _day_weights(p, spec_at, hol).items():
                share[day] = share.get(day, 0.0) + part * w
        total = sum(share.values())
        if total > 0:
            share = {d: s / total for d, s in share.items()}
        out.append(SplitRequest(id=r.id, status=r.status, code=r.code, from_date=r.from_date,
                                to_date=r.to_date, company_id=r.company_id or 0,
                                department_id=r.department_id or 0, employee_id=r.employee_id or 0,
                                leave_type_id=r.leave_type_id or 0, lines=lines.get(r.id, []),
                                day_share=share))
    return out


def load_crossing_requests(db: Session, base_query, d_from: date, d_to: date,
                           key_of_day: Callable[[date], str], calendar_types: set[int]
                           ) -> list[SplitRequest]:
    """Đơn vắt qua biên KỲ hoặc biên MỐC xu hướng (`key_of_day` = khóa mốc của một ngày).
    Đơn gọn trong một mốc nằm trọn trong kỳ bị loại — giữ đường SQL cũ."""
    rows = [r for r in overlapping_rows(base_query, d_from, d_to)
            if r.from_date < d_from or r.to_date > d_to
            or key_of_day(r.from_date) != key_of_day(r.to_date)]
    return build_split_requests(db, rows, calendar_types)
