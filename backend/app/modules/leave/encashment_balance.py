"""TÍNH SỐ NGÀY ĐƯỢC THANH TOÁN trên một dòng quỹ (duoc-CR-719). Tách khỏi `encashment_service` cho gọn tệp.

Đọc quỹ qua `balance_service` (nơi duy nhất tính số dùng được) rồi đưa cho hàm thuần `encashment_math`.
"""
from sqlalchemy.orm import Session

from app.core.vn_time import vn_today
from app.modules.employee.model import Employee

from . import balance_service, encashment_math
from .balance_model import LeaveBalance
from .catalog_model import LeaveType


def get_row(db: Session, employee: Employee, leave_type: LeaveType, year: int, *, lock: bool = False,
            actor: int = 0) -> LeaveBalance | None:
    """Dòng quỹ. `lock=True` là đường GHI: năm nay tự cấp nếu chưa có, năm trước không tự cấp (None)."""
    if lock and year == vn_today().year:
        return balance_service.ensure_balance(db, employee, year, leave_type, actor, for_update=True)
    row = balance_service.get_balance(db, employee.id, year, leave_type.id, for_update=lock)
    if row is not None:
        #  Như `ensure_balance`: phần mang sang quá hạn phải bị thu hồi TRƯỚC khi tính, kẻo số được thanh toán phồng lên.
        from . import carryover_service
        carryover_service.expire_carried(row, leave_type)
    return row


def compute(db: Session, row: LeaveBalance | None, leave_type: LeaveType, reason_kind: int) -> dict:
    """Số liệu để quyết định thanh toán trên MỘT dòng quỹ (`None` = chưa cấp quỹ -> mọi số 0)."""
    if row is None:
        return {"has_balance": False, "available": 0.0, "unused_carried": 0.0, "already_encashed": 0.0,
                "non_encashable_days": float(leave_type.non_encashable_days or 0.0),
                "max_encashable_days": float(leave_type.max_encashable_days or 0.0), "cap_remaining": None,
                "encashable": 0.0}
    available = balance_service.available_days(db, row, leave_type=leave_type)
    cap = encashment_math.annual_cap(leave_type.max_encashable_days, row.encashed_days)
    return {
        "has_balance": True, "available": available,
        "unused_carried": round(encashment_math.unused_carried(
            row.carried_days, row.used_days, row.pending_days, row.encashed_carried_days), 2),
        "already_encashed": float(row.encashed_days or 0.0),
        "non_encashable_days": float(leave_type.non_encashable_days or 0.0),
        "max_encashable_days": float(leave_type.max_encashable_days or 0.0),
        "cap_remaining": None if cap is None else round(cap, 2),
        "encashable": encashment_math.encashable_days(
            available=available, carried_days=row.carried_days, used_days=row.used_days,
            pending_days=row.pending_days, reason_kind=reason_kind,
            non_encashable_days=leave_type.non_encashable_days, max_encashable_days=leave_type.max_encashable_days,
            already_encashed=row.encashed_days, encashed_carried=row.encashed_carried_days),
    }


def preview(db: Session, employee: Employee, leave_type: LeaveType, year: int, reason_kind: int) -> dict:
    """Chỉ đọc (không cấp quỹ, không khóa): số liệu hiện lên form trước khi lập phiếu."""
    return compute(db, get_row(db, employee, leave_type, year), leave_type, reason_kind)
