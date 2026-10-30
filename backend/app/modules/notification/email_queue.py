"""Thư theo mẫu gửi SAU KHI GIAO DỊCH COMMIT, qua worker Celery (duoc-CR-681).

Vì sao không dùng `email_template_service.send_event_email`: hàm đó cần `BackgroundTasks` của FastAPI,
thiếu thì gửi SMTP NGAY trong request — và còn tự `commit()`. Bộ máy duyệt mở việc ở sâu bên trong một
giao dịch (gửi duyệt, duyệt chặng trước, sửa luồng…), không có `BackgroundTasks` trong tay và không được
commit giữa chừng. Ở đây:

1. Ghi `EmailLog` (trạng thái `pending`) bằng CHÍNH phiên đang chạy — chỉ `flush`, không commit.
2. Gắn một lần `after_commit` lên phiên: commit xong mới đẩy từng thư sang task `notification.send_email`.
   Giao dịch bị hủy thì dòng `EmailLog` mất theo, hàng đợi bị xóa ở `after_rollback` — không thư ma.
3. Đẩy sang worker lỗi (Redis chết) thì ghi log, dòng `EmailLog` nằm `pending` để tra — không làm hỏng
   nghiệp vụ, cùng luật "thư là phụ" với mọi nơi khác.

Tôn trọng: mẫu tắt (`enabled=False`), luật loại trừ email theo người / phòng / công ty, người không có địa chỉ.
"""
from __future__ import annotations

import logging

from sqlalchemy import event
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_QUEUE_KEY = "cr681_email_queue"
_HOOKED_KEY = "cr681_email_queue_hooked"


def dispatch(job: dict) -> None:
    """Đẩy MỘT thư sang worker. Tách hàm riêng để bộ test thay bằng bộ ghi (không chạm Redis thật)."""
    from .tasks import send_email_task

    send_email_task.delay(job["log_id"], job["to_email"], job["subject"], job["html"])


def _flush(session: Session) -> None:
    #  ⚠️ SQLAlchemy 2.0 phát `after_commit` cả khi NHẢ một savepoint (`begin_nested`) — lúc đó giao dịch
    #  ngoài vẫn đang mở, đẩy thư bây giờ là worker đọc `EmailLog` chưa commit (review lượt 2, đã dò thật).
    #  Chỉ đẩy khi commit giao dịch NGOÀI CÙNG. Đã dò SQLAlchemy 2.0.35: trong sự kiện, `in_transaction()`
    #  luôn True (kể cả commit ngoài cùng) — phải hỏi `in_nested_transaction()`: True = savepoint.
    if session.in_nested_transaction():
        return
    jobs = session.info.pop(_QUEUE_KEY, [])
    for job in jobs:
        try:
            dispatch(job)
        except Exception:  # noqa: BLE001 — thư là phụ; dòng EmailLog còn `pending` để tra
            logger.exception("Không đẩy được thư %s (EmailLog #%s) sang worker", job.get("event"), job.get("log_id"))


def _drop(session: Session) -> None:
    #  Hủy một SAVEPOINT cũng phát `after_rollback`: xóa cả hàng đợi lúc đó là mất thư của giao dịch ngoài
    #  (vẫn commit sau). Chỉ xóa khi giao dịch ngoài cùng bị hủy. Thư của riêng savepoint bị hủy vẫn nằm
    #  trong hàng, nhưng dòng `EmailLog` của nó đã mất → worker không thấy dòng thì bỏ qua (`send_smtp_email`).
    if session.in_nested_transaction():
        return
    session.info.pop(_QUEUE_KEY, None)


def _ensure_hooked(session: Session) -> None:
    if session.info.get(_HOOKED_KEY):
        return
    event.listen(session, "after_commit", _flush)
    event.listen(session, "after_rollback", _drop)
    session.info[_HOOKED_KEY] = True


def queue_event_email(db: Session, event_code: str, recipients: list, context: dict) -> int:
    """Xếp thư mẫu `event_code` cho `recipients` (đối tượng `User`), gửi sau commit. Trả số thư đã xếp."""
    from . import email_exclusion_service
    from .email_template_service import get_effective
    from .model import EmailLog
    from .service import get_user_display_name, render_template

    eff = get_effective(db, event_code)
    if eff is None or not eff["enabled"]:
        return 0
    recipients = email_exclusion_service.filter_recipients(db, [r for r in recipients if r], event_code)
    actor_id = int(context.get("actor_id") or 0)
    seen: set[str] = set()
    queued = 0
    for user in recipients:
        to_email = (getattr(user, "email", "") or "").strip()[:255]
        #  Chống trùng theo ĐỊA CHỈ: hai tài khoản chung một hộp thư không nhận hai thư.
        if not to_email or to_email.lower() in seen:
            continue
        seen.add(to_email.lower())
        ctx = {**context, "recipient_name": get_user_display_name(db, user) or ""}
        #  Cắt vừa `String(255)`: mẫu do quản trị sửa (vd thêm `{{ purpose }}`) có thể dài hơn — để MySQL
        #  từ chối thì lượt `flush` hỏng kéo theo CẢ giao dịch duyệt (review lượt 2).
        subject = render_template(eff["subject"], ctx)[:255]
        html = render_template(eff["body_html"], ctx)
        log = EmailLog(event=event_code, to_email=to_email, subject=subject, status="pending", created_by=actor_id)
        db.add(log)
        db.flush()
        _ensure_hooked(db)
        db.info.setdefault(_QUEUE_KEY, []).append(
            {"event": event_code, "log_id": log.id, "to_email": to_email, "subject": subject, "html": html})
        queued += 1
    return queued
