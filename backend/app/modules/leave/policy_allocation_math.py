"""HẠN MỨC NĂM theo phân bổ chính sách — hàm THUẦN (duoc-CR-717), không đụng CSDL.

Luật (D1 + D2 của kế hoạch):
  · Tháng `m` của năm `Y` thuộc phân bổ `A` ⇔ `A.từ ≤ ngày 15 tháng m ≤ (A.đến hoặc vô hạn)` (cùng quy ước 1–15
    của CR-715).
  · `q(m)` = số ngày/năm của dòng chính sách khớp loại nghỉ nếu tháng đó có phân bổ VÀ gói có dòng loại đó;
    còn lại = hạn mức theo luật của loại (`base_quota`: hình thức > cấp bậc > mặc định).
  · Tập tháng tính: FULL_YEAR → 1..12; PRORATA_HIRE / MONTHLY → từ `first_month_in_year(hire)` tới 12.
  · Không tháng nào được phân bổ khớp loại, hoặc mọi `q(m)` bằng nhau → trả ĐÚNG `prorate_allocation(q, ...)`
    (giữ nguyên cách làm tròn cũ, kể cả hạn mức lẻ như 12.25). Ngược lại `round_half_up(Σ q(m) / 12)`.

Phân bổ BẮT ĐẦU từ ngày vào làm (hoặc trong tháng vào làm, hoặc trước đó) phủ luôn các tháng TRƯỚC khi vào làm của năm
đó (review CR-717 M2): luật loại cả năm (FULL_YEAR) không được tính 9 tháng "chưa làm" theo luật loại rồi 3 tháng theo
gói ra số lai — gói 15 gán từ ngày vào làm 01/10 cho loại 12 ngày ra 15, không phải 13.

MONTHLY: `accrual_holdback` vẫn nhân tỷ lệ tháng trên `allocated_days` — khi đổi chính sách giữa năm đó là xấp xỉ
(chấp nhận, đã chốt ở kế hoạch).
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from . import accrual_service
from .constants import LeaveAccrualMode


@dataclass(frozen=True)
class AssignmentSpan:
    """Một phân bổ đã nạp: khoảng ngày + số ngày/năm theo từng loại nghỉ của gói."""

    from_date: date
    to_date: date | None
    quotas: dict[int, float] = field(default_factory=dict)


def covers_mid_month(span: AssignmentSpan, year: int, month: int) -> bool:
    """Phân bổ có hiệu lực vào ngày 15 của tháng đó không."""
    mid = date(year, month, accrual_service.HALF_MONTH_DAY)
    return span.from_date <= mid and (span.to_date is None or mid <= span.to_date)


def overlaps_year(from_date: date, to_date: date | None, year: int) -> bool:
    """Khoảng `[from, to]` có chạm năm dương lịch `year` không."""
    return from_date <= date(year, 12, 31) and (to_date is None or to_date >= date(year, 1, 1))


def month_quota(spans: list[AssignmentSpan], leave_type_id: int, year: int, month: int) -> float | None:
    """Số ngày/năm do phân bổ quy định cho tháng này, hoặc `None` nếu không phân bổ nào quy định loại đó."""
    #  Phân bổ không chồng nhau; nếu dữ liệu lỡ chồng thì lấy cái bắt đầu MUỘN hơn (mới hơn).
    for span in sorted(spans, key=lambda s: s.from_date, reverse=True):
        if leave_type_id in span.quotas and covers_mid_month(span, year, month):
            return float(span.quotas[leave_type_id])
    return None


def extend_to_year_start(spans: list[AssignmentSpan], hire_date: date | None, year: int) -> list[AssignmentSpan]:
    """Phân bổ bắt đầu trong khoảng `(01/01 năm xét, hết tháng vào làm]` được kéo lùi về 01/01 — nhưng không lấn vào
    ngày đã thuộc phân bổ khác kết thúc trước nó."""
    if hire_date is None:
        return spans
    jan1 = date(year, 1, 1)
    hire_month_end = date(hire_date.year, hire_date.month, calendar.monthrange(hire_date.year, hire_date.month)[1])
    out = []
    for span in spans:
        if not jan1 < span.from_date <= hire_month_end:
            out.append(span)
            continue
        prior_ends = [o.to_date for o in spans if o is not span and o.to_date is not None and o.to_date < span.from_date]
        start = max(jan1, max(prior_ends) + timedelta(days=1)) if prior_ends else jan1
        out.append(replace(span, from_date=start))
    return out


def compute_allocated(base_quota: float, mode: int, hire_date: date | None, year: int,
                      spans: list[AssignmentSpan], leave_type_id: int) -> float:
    """`allocated_days` của (người × loại × năm) — xem docstring đầu tệp."""
    spans = extend_to_year_start(spans, hire_date, year)
    if mode == LeaveAccrualMode.FULL_YEAR:
        months = list(range(1, 13))
    else:
        months = list(range(accrual_service.first_month_in_year(hire_date, year), 13))
    overrides = {m: month_quota(spans, leave_type_id, year, m) for m in months}
    quotas = [base_quota if q is None else q for q in overrides.values()]
    if not any(q is not None for q in overrides.values()) or len(set(quotas)) <= 1:
        #  Không phân bổ nào (hoặc mọi tháng cùng một số) → đúng công thức cũ.
        common = quotas[0] if quotas else base_quota
        return accrual_service.prorate_allocation(common, mode, hire_date, year)
    return accrual_service.round_half_up(sum(quotas) / 12)
