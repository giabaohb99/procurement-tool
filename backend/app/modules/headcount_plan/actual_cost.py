"""Số THỰC TẾ cùng nguồn với khoản của kế hoạch (duoc-CR-690, phase 24) — dùng chung cho A5 và chi tiết kế hoạch.

ERP không có bảng lương: thực tế chỉ lấy được từ HĐLĐ đang hiệu lực (`doc/erp/hrm/06-ke-hoach-nhan-su.md` §6). Mỗi khoản khai
«Lấy thực tế từ» (`ActualSource`): lương cơ bản · phụ cấp · % × lương đóng BHXH (đúng % và trần của khoản). Khoản không có nguồn
KHÔNG tham gia so sánh. Một tháng chỉ có số thực tế khi đã bắt đầu (không ước lượng tháng tương lai).
"""
from __future__ import annotations

import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

from app.modules.labor_contract.payroll_report_data import PayRecord, rows_at

from .constants import ActualSource
from .effective import ItemMeta, Month

_HUNDRED = Decimal(100)


def months_between(d_from: date, d_to: date) -> list[Month]:
    """Các tháng mà khoảng [d_from, d_to] chạm tới, theo thứ tự."""
    out, (y, m) = [], (d_from.year, d_from.month)
    while (y, m) <= (d_to.year, d_to.month):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def month_as_of(year: int, month: int, today: date, hi: date | None = None) -> date | None:
    """Mốc đo thực tế của tháng: cuối tháng, không quá hôm nay và không quá `hi`. `None` = tháng chưa bắt đầu."""
    if date(year, month, 1) > today:
        return None
    t = min(date(year, month, calendar.monthrange(year, month)[1]), today)
    return min(t, hi) if hi else t


def covered_codes(metas: dict[str, ItemMeta]) -> list[str]:
    return [c for c, m in metas.items() if m.source != ActualSource.NONE]


def actual_by_item(rows: Iterable[PayRecord], metas: dict[str, ItemMeta]) -> dict[str, int]:
    """{mã khoản có nguồn: đồng} cộng trên các HĐ `rows` (đã lọc đúng pháp nhân / phòng và đúng tháng)."""
    rows = list(rows)
    out: dict[str, int] = {}
    for code, meta in metas.items():
        if meta.source == ActualSource.BASE_SALARY:
            total = Decimal(sum(r.base_salary for r in rows))
        elif meta.source == ActualSource.ALLOWANCE:
            total = Decimal(sum(r.allowance for r in rows))
        elif meta.source == ActualSource.PERCENT_OF_INSURANCE_SALARY:
            total = sum((Decimal(min(r.insurance_salary, meta.cap_amount) if meta.cap_amount else r.insurance_salary)
                         * meta.rate / _HUNDRED for r in rows), Decimal(0))
        else:
            continue
        out[code] = int(total.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return out


class ActualIndex:
    """HĐ còn hiệu lực theo tháng, nạp LƯỜI (chỉ tháng nào được hỏi) từ MỘT lần `load_records`."""

    def __init__(self, records: list[PayRecord], today: date, hi: date | None = None):
        self._records, self._today, self._hi = records, today, hi
        self._by_month: dict[Month, dict[int, list[PayRecord]] | None] = {}

    def is_elapsed(self, year: int, month: int) -> bool:
        return month_as_of(year, month, self._today, self._hi) is not None

    def rows(self, year: int, month: int, company_id: int, department_id: int = 0) -> list[PayRecord]:
        """HĐ của pháp nhân (và phòng nếu khác 0) còn hiệu lực ở cuối tháng; tháng chưa bắt đầu → rỗng."""
        if (year, month) not in self._by_month:
            t = month_as_of(year, month, self._today, self._hi)
            grouped: dict[int, list[PayRecord]] = {}
            for r in (rows_at(self._records, t) if t else []):
                grouped.setdefault(r.company_id, []).append(r)
            self._by_month[(year, month)] = grouped
        in_company = self._by_month[(year, month)].get(company_id, [])
        return [r for r in in_company if r.department_id == department_id] if department_id else in_company
