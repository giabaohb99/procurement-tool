"""LUẬT CẤP QUỸ kiểu ERPNext (duoc-CR-715): hạn mức theo nhóm, tỷ lệ tháng làm việc, cộng dần theo tháng.

Hàm thuần (không đụng CSDL) ở nửa đầu để test được trực tiếp; `resolve_quota` là hàm duy nhất hỏi bảng
`tab_leave_type_quota`. `balance_service` gọi sang đây ở `ensure_balance` (cấp quỹ) và `remaining`/`check_enough`
(phần chưa tới tháng của loại cộng dần).

Quy ước tháng: vào làm ngày 1–15 tính CẢ tháng đó, từ ngày 16 tính từ tháng sau; làm tròn tới 0.5 ngày (half up).
"""
from __future__ import annotations

import math
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .catalog_model import LeaveType, LeaveTypeQuota
from .constants import (QUOTA_BASIS_EMPLOYMENT_TYPE, QUOTA_BASIS_JOB_LEVEL,
                        LeaveAccrualMode)

#  Ngày cuối cùng của nửa đầu tháng — vào làm tới ngày này vẫn tính trọn tháng.
HALF_MONTH_DAY = 15


def round_half_up(value: float) -> float:
    """Làm tròn tới 0.5 ngày, nửa lên (`4.75 → 5.0`, `4.74 → 4.5`)."""
    return math.floor(value * 2 + 0.5 + 1e-9) / 2


def round_down_half(value: float) -> float:
    """Làm tròn XUỐNG 0.5 ngày — dùng cho phần đã cộng dồn (không cho dùng lố)."""
    return math.floor(value * 2 + 1e-9) / 2


def first_month_in_year(hire_date: date | None, year: int) -> int:
    """Tháng đầu tiên (1–12) được tính phép trong `year`; `1` nếu vào làm trước năm đó hoặc chưa khai ngày vào làm.

    Trả `13` nghĩa là năm đó không có tháng nào: vào làm cuối tháng 12 (từ ngày 16), hoặc vào làm ở năm SAU.
    """
    if hire_date is not None and hire_date.year > year:
        return 13
    if hire_date is None or hire_date.year != year:
        return 1
    return hire_date.month if hire_date.day <= HALF_MONTH_DAY else hire_date.month + 1


def months_in_period(hire_date: date | None, year: int) -> int:
    """Số tháng của kỳ cấp quỹ: 12 nếu vào làm trước năm, 0 nếu vào làm năm sau, còn lại từ tháng đầu tới hết tháng 12.

    Hồ sơ hay được tạo TRƯỚC ngày vào làm (đi làm từ 05/01 năm sau mà cấp quỹ năm nay) — người đó chưa có tháng nào.
    """
    if hire_date is not None and hire_date.year > year:
        return 0
    if hire_date is None or hire_date.year != year:
        return 12
    return max(0, 13 - first_month_in_year(hire_date, year))


def prorate_allocation(quota: float, mode: int, hire_date: date | None, year: int) -> float:
    """`allocated_days` lưu vào quỹ: đủ quota với FULL_YEAR; tỷ lệ tháng với hai chế độ còn lại."""
    if mode == LeaveAccrualMode.FULL_YEAR:
        return float(quota)
    months = months_in_period(hire_date, year)
    if months >= 12:
        return float(quota)
    return round_half_up(quota * months / 12)


def accrual_holdback(allocated: float, mode: int, hire_date: date | None, year: int,
                     today: date) -> float:
    """Phần `allocated_days` CHƯA tới tháng (chỉ chế độ MONTHLY) — `remaining()` trừ ra.

    Số dùng được tới hôm nay = `allocated × số tháng đã tới / số tháng của kỳ`, làm tròn xuống 0.5; năm đã qua → đủ,
    năm chưa tới → chưa có tháng nào.
    """
    if mode != LeaveAccrualMode.MONTHLY or allocated <= 0:
        return 0.0
    period = months_in_period(hire_date, year)
    if period <= 0 or year < today.year:
        return 0.0
    if year > today.year:
        reached = 0
    else:
        start = first_month_in_year(hire_date, year)
        reached = min(period, max(0, today.month - start + 1))
    accrued = round_down_half(allocated * reached / period)
    return round(max(0.0, allocated - accrued), 2)


def pick_quota(rules: list[LeaveTypeQuota], leave_type: LeaveType, employee) -> float:
    """Phần THUẦN của `resolve_quota`: chọn hạn mức từ danh sách luật đã nạp sẵn (nạp một lượt cho nhiều người)."""
    if rules:
        wanted = ((QUOTA_BASIS_EMPLOYMENT_TYPE, getattr(employee, "employment_type", 0) or 0),
                  (QUOTA_BASIS_JOB_LEVEL, getattr(employee, "job_level", 0) or 0))
        for basis, value in wanted:
            for rule in rules:
                if rule.basis == basis and rule.basis_value == value and value:
                    return float(rule.quota_days or 0.0)
    return float(leave_type.annual_quota_days or 0.0)


def resolve_quota(db: Session, leave_type: LeaveType, employee) -> float:
    """Hạn mức năm của người này: hình thức nhân viên thắng cấp bậc, cấp bậc thắng `annual_quota_days`."""
    rules = db.query(LeaveTypeQuota).filter(LeaveTypeQuota.leave_type_id == leave_type.id).all()
    return pick_quota(rules, leave_type, employee)


def ensure_applicable(leave_type: LeaveType, hire_date: date | None, starts_on: date) -> None:
    """Chặn (422) khi khoảng nghỉ bắt đầu trước `hire_date + applicable_after_days`. Không có ngày vào làm → không chặn."""
    after = int(leave_type.applicable_after_days or 0)
    if after <= 0 or hire_date is None:
        return
    allowed_from = hire_date + timedelta(days=after)
    if starts_on < allowed_from:
        raise HTTPException(
            422,
            f"Loại nghỉ \"{leave_type.name}\" chỉ dùng được sau {after} ngày vào làm "
            f"(từ {allowed_from:%d/%m/%Y}).")
