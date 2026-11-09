"""TOÁN THUẦN của phiếu thanh toán nghỉ phép (duoc-CR-719) — số ngày TỐI ĐA được đổi ra tiền.

Hàm thuần (không truy vấn, không ghi) để bài kiểm chạy bảng ca ERPNext trực tiếp. Chép ý `set_actual_encashable_days`
của ERPNext, nhưng trần tính theo NĂM (cộng dồn mọi phiếu của năm), không theo từng lần.

    phép dư cuối năm (YEAR_END):
        phần mang sang chưa dùng = max(0, mang_sang − đã_dùng − giữ_chỗ)         # mang sang được coi là tiêu TRƯỚC
        nền  = dùng_được − phần mang sang chưa dùng − số_ngày_không_thanh_toán   # D6a: không đổi phần mang sang
        trần = trần_năm − đã_thanh_toán_năm        (chỉ khi trần_năm > 0)
    nghỉ việc (RESIGNATION):
        nền  = dùng_được ; không trần (D5a, Điều 113 khoản 3 BLLĐ: trả hết ngày chưa nghỉ)

    được_thanh_toán = kẹp(nền, 0, trần), rồi làm tròn XUỐNG bước 0,5 ngày.
"""
import math

from .constants import LeaveEncashmentReason

#  Số ngày thanh toán đi theo bước 0,5 (như đơn nghỉ).
DAY_STEP = 0.5
_EPS = 1e-9


def floor_to_step(value: float) -> float:
    """Làm tròn XUỐNG bội của 0,5 (6,25 -> 6,0). Âm -> 0."""
    if value <= 0:
        return 0.0
    return math.floor(value / DAY_STEP + _EPS) * DAY_STEP


def is_on_step(value: float) -> bool:
    """`value` có là bội của 0,5 không (chịu sai số số thực)."""
    return abs(value / DAY_STEP - round(value / DAY_STEP)) < 1e-6


def unused_carried(carried_days: float, used_days: float, pending_days: float, encashed_carried: float = 0.0) -> float:
    """Phần mang sang CHƯA dùng: mang sang được coi là tiêu trước (xem `carryover_service.expire_carried`)."""
    return max(0.0, float(carried_days or 0.0) - float(used_days or 0.0) - float(pending_days or 0.0)
               - float(encashed_carried or 0.0))


def carried_part(days: float, carried_days: float, used_days: float, pending_without_form: float,
                 encashed_carried: float, reason_kind: int) -> float:
    """Phần của phiếu `days` lấy từ ngày mang sang. Chỉ lý do Nghỉ việc (mang sang tiêu trước); cuối năm = 0 (D6a)."""
    if int(reason_kind) != int(LeaveEncashmentReason.RESIGNATION):
        return 0.0
    return round(min(float(days), unused_carried(carried_days, used_days, pending_without_form, encashed_carried)), 2)


def annual_cap(max_encashable_days: float, already_encashed: float) -> float | None:
    """Phần trần năm còn lại; `None` = không trần (`max_encashable_days` = 0)."""
    if not max_encashable_days or max_encashable_days <= 0:
        return None
    return max(0.0, float(max_encashable_days) - float(already_encashed or 0.0))


def encashable_days(*, available: float, carried_days: float, used_days: float, pending_days: float,
                    reason_kind: int, non_encashable_days: float, max_encashable_days: float,
                    already_encashed: float, encashed_carried: float = 0.0) -> float:
    """Số ngày tối đa được thanh toán. Ứng phép âm (`available` <= 0) -> 0."""
    available = float(available or 0.0)
    if available <= 0:
        return 0.0
    if int(reason_kind) == int(LeaveEncashmentReason.RESIGNATION):
        return floor_to_step(available)
    base = (available - unused_carried(carried_days, used_days, pending_days, encashed_carried)
            - float(non_encashable_days or 0.0))
    base = max(0.0, base)
    cap = annual_cap(max_encashable_days, already_encashed)
    if cap is not None:
        base = min(base, cap)
    return floor_to_step(base)
