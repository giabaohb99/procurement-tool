"""NGÀY CẤM NGHỈ (duoc-CR-715) — tìm khoảng cấm mà một đơn nghỉ đụng phải, và chốt chặn ở lượt duyệt cuối.

Luật (chép ý Leave Block List của ERPNext, nhưng chặn ở DUYỆT chứ không ở LẬP):
  · LẬP / SỬA / GỬI: không chặn. `find_conflicts` chỉ để giao diện hiện khung vàng cảnh báo (`block_conflicts`);
  · DUYỆT CHẶNG CUỐI: còn xung đột thì `ensure_approvable` ném 422 trừ khi người bấm có vai trò miễn
    (`leave_block_exempt_roles` ở Cài đặt nhân sự) hoặc là quản trị.

Khớp theo NGƯỜI NGHỈ (pháp nhân / phòng của họ; `0` = mọi), không theo người lập hộ. Đơn nhiều khoảng ngày thì khoảng
nào giao cũng tính — KHE giữa các khoảng không dính (đọc khoảng qua `period_spans`, không đọc bao ngoài của đầu đơn).
"""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.privilege_escalation import SYSTEM_ADMIN_ROLE_CODE
from app.modules.approval.entity_hooks import HookVeto
from app.modules.role.model import Role
from app.modules.user.model import UserRole

from .catalog_model import LeaveBlockPeriod
from .period_spans import PeriodView


def find_conflicts(db: Session, employee, periods: Iterable[PeriodView]) -> list[LeaveBlockPeriod]:
    """Các dòng cấm đang bật mà người nghỉ `employee` đụng phải với BẤT KỲ khoảng nào của đơn. MỘT truy vấn."""
    spans = [(p.from_date, p.to_date) for p in periods if p.from_date and p.to_date]
    if employee is None or not spans:
        return []
    company_id = getattr(employee, "company_id", 0) or 0
    department_id = getattr(employee, "department_id", 0) or 0
    overlaps = or_(*[and_(LeaveBlockPeriod.from_date <= end, LeaveBlockPeriod.to_date >= start)
                     for start, end in spans])
    return (
        db.query(LeaveBlockPeriod)
        .filter(LeaveBlockPeriod.is_active.is_(True),
                LeaveBlockPeriod.company_id.in_({0, company_id}),
                LeaveBlockPeriod.department_id.in_({0, department_id}),
                overlaps)
        .order_by(LeaveBlockPeriod.from_date, LeaveBlockPeriod.id)
        .all()
    )


def dump_conflicts(rows: Iterable[LeaveBlockPeriod]) -> list[dict]:
    """Dạng trả ra giao diện: `{id, from_date, to_date, reason}`."""
    return [{"id": r.id, "from_date": r.from_date, "to_date": r.to_date, "reason": r.reason or ""}
            for r in rows]


def exempt_roles() -> set[str]:
    """Mã vai trò được duyệt qua ngày cấm (khai ở Cài đặt nhân sự) — quản trị hệ thống luôn được."""
    raw = str(app_settings.get("leave_block_exempt_roles") or "")
    return {code.strip() for code in raw.split(",") if code.strip()} | {SYSTEM_ADMIN_ROLE_CODE}


def can_override_block(db: Session, user_id: int) -> bool:
    """Tài khoản này có vai trò được miễn không (một truy vấn)."""
    if not user_id:
        return False
    hit = (db.query(Role.id)
           .join(UserRole, UserRole.role_id == Role.id)
           .filter(UserRole.user_id == user_id, Role.code.in_(exempt_roles()))
           .first())
    return hit is not None


def _text(row: LeaveBlockPeriod) -> str:
    span = (f"{row.from_date:%d/%m/%Y}" if row.from_date == row.to_date
            else f"{row.from_date:%d/%m/%Y} – {row.to_date:%d/%m/%Y}")
    return f"{span} ({row.reason})" if row.reason else span


def ensure_approvable(db: Session, employee, periods: Iterable[PeriodView], approver_user_id: int) -> None:
    """Chặn (422) lượt duyệt cuối khi đơn đụng ngày cấm nghỉ và người duyệt không được miễn.

    Ném `HookVeto` (là `HTTPException` 422) để bộ máy duyệt KHÔNG nuốt lỗi như các lỗi hook khác — xem
    `entity_hooks.fire`. Gọi TRƯỚC khi trừ quỹ nên không để lại trạng thái dở.
    """
    conflicts = find_conflicts(db, employee, periods)
    if not conflicts or can_override_block(db, approver_user_id):
        return
    raise HookVeto(
        422,
        "Đơn nghỉ này rơi vào ngày cấm nghỉ: " + "; ".join(_text(r) for r in conflicts)
        + ". Chưa duyệt được — nhờ người có vai trò được miễn (Cài đặt nhân sự › Nghỉ phép) duyệt, "
          "hoặc trả đơn về để người nghỉ đổi ngày.")
