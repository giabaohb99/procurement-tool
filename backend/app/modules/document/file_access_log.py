"""NHẬT KÝ MỞ / TẢI TỆP ĐÍNH KÈM VĂN BẢN + cảnh báo khi bất thường.

Không có cách nào chặn người xem chụp lại màn hình (xem `attachment-viewer-dialog.tsx`).
Thứ thay thế được là **biết ai đã mở cái gì, lúc nào** — và khi một người mở/tải
dồn dập bất thường thì báo ngay cho người quản lý, đừng đợi tới lúc tài liệu đã
nằm ngoài công ty mới đi dựng lại.

Ba phần, cố ý tách rời:

  1. **Ghi** — mỗi lượt mở/tải một dòng `tab_audit_log` trên chính VĂN BẢN, nên
     nó hiện thẳng trong sổ nhật ký của văn bản đó, không phải đi tra bảng khác.
  2. **Đếm** — bao nhiêu lượt của cùng một người trong cửa sổ vừa qua.
  3. **Báo** — vượt ngưỡng thì gửi chuông cho người được chỉ định.

⚠️ Ghi nhật ký **không được làm hỏng việc mở tệp**. Người dùng có quyền, tệp có
thật, mà bấm vào lại báo lỗi chỉ vì bảng nhật ký trục trặc là đổi một phiền toái
nhỏ lấy một sự cố lớn. Nên toàn bộ phần này chạy trong `try/except` ở chỗ gọi.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.app_settings import get as setting
from app.core.audit import record, resolve_actor
from app.modules.notification.model import Notification

from .model import Document

LOGGER = logging.getLogger(__name__)

ACTION_VIEW = "view_file"
ACTION_DOWNLOAD = "download_file"
#  Dòng đánh dấu "đã báo rồi" — dùng luôn nhật ký làm chỗ nhớ, khỏi đẻ bảng mới
#  chỉ để chống gửi trùng.
ACTION_ALERT = "file_alert"

ACTION_LABELS = {ACTION_VIEW: "Mở xem", ACTION_DOWNLOAD: "Tải về"}


def log_and_alert(db: Session, doc: Document, user, action: str, file_name: str) -> None:
    """Ghi một lượt mở/tải, rồi báo nếu người này đang mở dồn dập bất thường."""
    record(db, user.id, "document", doc.id, action,
           f"{ACTION_LABELS.get(action, action)} tệp «{file_name}»")

    threshold = int(setting("doc_file_alert_threshold") or 0)
    if threshold <= 0:  # 0 = tắt hẳn phần cảnh báo
        return

    minutes = int(setting("doc_file_alert_window_min") or 10)
    since = _window_start(db, minutes)
    access_count = _count_accesses(db, user.id, since)
    if access_count < threshold:
        return
    if _already_alerted_in_window(db, user.id, since):
        #  Đã báo một lần trong cửa sổ này rồi. Không báo lại mỗi lượt tiếp theo:
        #  người nhận sẽ tắt tiếng chuông, và lần sau có chuyện thật thì không ai
        #  nhìn nữa.
        return

    _raise_alert(db, doc, user, access_count, minutes)


def _window_start(db: Session, minutes: int) -> datetime:
    """Mốc đầu cửa sổ, đo bằng ĐỒNG HỒ CỦA CSDL.

    ⚠️ KHÔNG dùng `datetime.utcnow()` của Python. `created_at` do CSDL ghi
    (`server_default=func.now()` ở `core/base_model.py`), nên nếu máy chủ CSDL
    chạy giờ Việt Nam mà đây lấy giờ UTC thì cửa sổ lệch **7 tiếng** — và lệch
    đúng chiều gây **báo động giả**: bảy tiếng hoạt động bị đếm như thể xảy ra
    trong mười phút. Ở máy lập trình hai đồng hồ tình cờ trùng nhau (container
    chạy UTC) nên lỗi này không lộ ra khi thử.

    Hỏi thẳng CSDL thì hai vế của phép so luôn cùng một đồng hồ, khỏi phụ thuộc
    cấu hình múi giờ của từng môi trường.
    """
    now = db.execute(select(func.now())).scalar()
    if isinstance(now, str):  # SQLite trả chuỗi
        now = datetime.fromisoformat(now)
    return (now or datetime.now()) - timedelta(minutes=minutes)


def _count_accesses(db: Session, user_id: int, since: datetime) -> int:
    from app.modules.audit.model import AuditLog

    return (db.query(AuditLog)
            .filter(AuditLog.entity == "document",
                    AuditLog.action.in_((ACTION_VIEW, ACTION_DOWNLOAD)),
                    AuditLog.created_by == user_id,
                    AuditLog.created_at >= since)
            .count())


def _already_alerted_in_window(db: Session, user_id: int, since: datetime) -> bool:
    from app.modules.audit.model import AuditLog

    return (db.query(AuditLog.id)
            .filter(AuditLog.entity == "document",
                    AuditLog.action == ACTION_ALERT,
                    AuditLog.entity_id == user_id,
                    AuditLog.created_at >= since)
            .first()) is not None


def _raise_alert(db: Session, doc: Document, user, access_count: int, minutes: int) -> None:
    name = resolve_actor(db, user.id)
    title = f"Bất thường: {name} mở {access_count} tệp trong {minutes} phút"
    body = (
        f"{name} vừa mở hoặc tải {access_count} tệp đính kèm văn bản trong {minutes} phút gần đây. "
        f"Tệp gần nhất thuộc văn bản «{doc.doc_code or doc.issue_number or doc.title}». "
        f"Mở sổ nhật ký của văn bản để xem chi tiết."
    )

    recipients = alert_recipients(db)
    for uid in recipients:
        #  Không tự báo cho chính người đang thao tác: cảnh báo là để người khác
        #  biết, còn họ thì đã biết mình vừa làm gì.
        if uid == user.id:
            continue
        db.add(Notification(user_id=uid, title=title, body=body,
                            link=f"/document/documents/{doc.id}", created_by=0))

    #  `entity_id` = id NGƯỜI bị cảnh báo (không phải id văn bản): chống gửi trùng
    #  tra theo người, mà một người thì mở nhiều văn bản khác nhau.
    record(db, 0, "document", user.id, ACTION_ALERT,
           f"{title} — đã báo cho {len(recipients)} người")


def alert_recipients(db: Session) -> list[int]:
    """Ai nhận cảnh báo.

    Ưu tiên danh sách khai tay ở Cấu hình hệ thống (`doc_file_alert_recipients`,
    ngăn cách bằng dấu phẩy, nhận email hoặc mã nhân viên). Bỏ trống thì tự suy:
    **mọi tài khoản có quyền ĐỌC văn bản ở phạm vi toàn hệ** — tức quản trị và
    văn thư cấp tập đoàn, cùng nhóm "giữ sổ" ở `revoke_access.py`.

    Vì sao có đường tự suy: khai tay mà quên khai thì cảnh báo rơi vào hư không
    và không ai biết là nó đang không chạy.
    """
    manual_list = (setting("doc_file_alert_recipients") or "").strip()
    if manual_list:
        return _by_list(db, manual_list)
    return _by_system_permission(db)


def _by_list(db: Session, raw: str) -> list[int]:
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    keys = [part.strip() for part in raw.split(",") if part.strip()]
    if not keys:
        return []
    rows = (db.query(User.id)
            .outerjoin(Employee, Employee.id == User.employee_id)
            .filter(User.is_active.is_(True),
                    User.email.in_(keys) | Employee.code.in_(keys))
            .all())
    return [row[0] for row in rows]


def _by_system_permission(db: Session) -> list[int]:
    from app.modules.role.model import Permission
    from app.modules.user.model import User, UserRole

    role_ids = [row[0] for row in
                db.query(Permission.role_id)
                .filter(Permission.entity == "document",
                        Permission.can_read.is_(True),
                        Permission.scope == "all")
                .all()]
    if not role_ids:
        return []
    rows = (db.query(User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .filter(UserRole.role_id.in_(role_ids), User.is_active.is_(True))
            .distinct()
            .all())
    return [row[0] for row in rows]
