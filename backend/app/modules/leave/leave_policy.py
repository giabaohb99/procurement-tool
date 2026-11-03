"""Luật CHẶN ĐƠN NGHỈ LÙI NGÀY của trang Cài đặt nhân sự (duoc-CR-713, chép ý `restrict_backdated_leave_application`
+ `role_allowed_to_create_backdated_leave_application` của HR Settings ERPNext).

Một nơi duy nhất đọc hai khóa `leave_restrict_backdated` / `leave_backdated_roles`; `request_service` gọi
`ensure_not_backdated` ở ba nhịp LẬP · SỬA · GỬI DUYỆT. Nhịp gửi duyệt cũng phải chặn: nháp lập hôm qua cho hôm nay,
để tới mai mới gửi, thì lúc gửi nó đã thành đơn lùi ngày.

"Hôm nay" là ngày Việt Nam (`vn_today`) — container chạy UTC, `date.today()` lệch ngày từ 00:00 tới 06:59 giờ VN.
"""
from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.privilege_escalation import SYSTEM_ADMIN_ROLE_CODE
from app.core.vn_time import vn_today
from app.modules.role.model import Role
from app.modules.user.model import UserRole

from .period_spans import PeriodView


def allowed_backdate_roles() -> set[str]:
    """Mã vai trò được miễn (khai ở Cài đặt nhân sự) — quản trị hệ thống luôn được miễn."""
    raw = str(app_settings.get("leave_backdated_roles") or "")
    return {code.strip() for code in raw.split(",") if code.strip()} | {SYSTEM_ADMIN_ROLE_CODE}


def can_backdate(db: Session, user_ids: Iterable[int]) -> bool:
    """Một trong các tài khoản này có vai trò được lập đơn lùi ngày không (một truy vấn)."""
    ids = [uid for uid in user_ids if uid]
    if not ids:
        return False
    hit = (
        db.query(Role.id)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id.in_(ids), Role.code.in_(allowed_backdate_roles()))
        .first()
    )
    return hit is not None


def same_periods(old: Iterable[PeriodView], new: Iterable[PeriodView]) -> bool:
    """Hai danh sách khoảng có cùng ngày + buổi không (bỏ qua số ngày, id) — sửa lý do / đính kèm thì không đổi."""
    key = lambda items: sorted((p.from_date, p.to_date, p.from_session, p.to_session) for p in items)  # noqa: E731
    return key(old) == key(new)


def ensure_not_backdated(db: Session, user, periods: Iterable[PeriodView], creator_id: int = 0) -> None:
    """Chặn (422) khi công tắc BẬT, đơn có khoảng bắt đầu trước hôm nay và không ai được miễn.

    «Được miễn» = người đang thao tác HOẶC người đã lập đơn (`creator_id`) có vai trò miễn: Nhân sự lập hộ một đơn
    lùi ngày cho nhân viên thì nhân viên đó vẫn gửi duyệt được tờ đơn ấy (rà mã CR-713).
    """
    if not app_settings.get("leave_restrict_backdated"):
        return
    starts = [period.from_date for period in periods if period.from_date]
    if not starts:
        return
    earliest = min(starts)
    today = vn_today()
    if earliest >= today or can_backdate(db, [user.id, creator_id]):
        return
    raise HTTPException(
        422,
        f"Không lập được đơn nghỉ cho ngày đã qua ({earliest:%d/%m/%Y}). Cài đặt nhân sự đang chặn đơn lùi ngày — "
        "nhờ phòng Nhân sự lập hộ nếu cần.",
    )
