"""CHUÔNG BÁO KHI CA ĐƯỢC XẾP / ĐỔI (duoc-CR-761, Q4) — MỘT chuông cho mỗi nhân sự bị đổi trong một lượt ghi.

Gộp theo lượt (không theo từng ngày) để xếp ca cả tuần chỉ rung một lần: nội dung nêu khoảng ngày nhỏ nhất – lớn nhất bị
đổi. KHÔNG chuông cho chính người bấm (HR tự xếp ca cho mình không tự báo mình). Chạy SAU khi ca đã commit; lỗi chuông chỉ
ghi log, không làm hỏng việc xếp ca (cùng lề lối `vehicle_booking/notify.py`).

Liên kết `/me` = Trang cá nhân của chính người nhận, nơi có thẻ "Ca làm việc" (giao diện cần `/me` trong `V2_PREFIXES` của
`shared/notifications/notification-link.ts` thì bấm chuông mới điều hướng).
"""
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.modules.notification.model import Notification
from app.modules.user.model import User

logger = logging.getLogger("app.work_schedule")

LINK = "/me"
TITLE = "Ca làm việc của bạn vừa được cập nhật"


def _span_text(days: set[date]) -> str:
    """"ngày 18/11" hoặc "ngày 18/11–20/11" (kèm năm khi khoảng vắt qua hai năm)."""
    first, last = min(days), max(days)
    if first == last:
        return f"ngày {first:%d/%m}"
    if first.year != last.year:
        return f"ngày {first:%d/%m/%Y}–{last:%d/%m/%Y}"
    return f"ngày {first:%d/%m}–{last:%d/%m}"


def notify_shift_changes(db: Session, actor, dates_by_employee: dict[int, set[date]]) -> int:
    """Tạo chuông cho các tài khoản đang hoạt động của từng nhân sự bị đổi; trả số chuông đã tạo (0 nếu lỗi / không ai)."""
    changed = {emp: days for emp, days in dates_by_employee.items() if emp and days}
    if not changed:
        return 0
    try:
        users = (db.query(User).filter(User.employee_id.in_(list(changed)), User.is_active.is_(True),
                                       User.id != actor.id).all())
        if not users:
            return 0
        who = resolve_actor(db, actor.id)
        for user in users:
            body = f"Ca làm việc của bạn {_span_text(changed[user.employee_id])} vừa được cập nhật bởi {who}."
            db.add(Notification(user_id=user.id, title=TITLE, body=body, link=LINK, created_by=actor.id))
        db.commit()
        return len(users)
    except Exception:  # noqa: BLE001 — chuông không được làm hỏng nghiệp vụ đã commit
        db.rollback()
        logger.exception("Không tạo được chuông báo ca làm việc cho %s nhân sự", len(changed))
        return 0
