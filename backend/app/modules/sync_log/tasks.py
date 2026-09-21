"""Chuông sáng của quyển sổ đồng bộ — dòng lỗi quá một ngày mà chưa ai vá.

Vì sao cần. Ba vòng chạy nền của app đặt xe cũ đều tự chạy lại phần hỏng, nên
gần như mọi sự cố tự lành trong vòng mười phút. Đúng vì thế mà những dòng KHÔNG
tự lành lại nguy hiểm nhất: chúng nằm im trong sổ, không ai mở màn hình ra xem,
và bên app cũ vẫn tưởng phiếu đã sang ERP. Một lần mỗi sáng là đủ để chúng không
chìm luôn.

Vì sao 08:00 chứ không phải nhịp phút. Người nhận chuông không trực đêm, mà việc
xử một dòng lỗi luôn là việc tay (mở phiếu bên app cũ xem nó hỏng chỗ nào). Bắn
lúc vừa tới bàn làm việc thì chuông còn được đọc; bắn 3 giờ sáng thì tới sáng nó
đã nằm dưới hai chục cái khác.

Cách đếm "chưa ai vá" ở `service.find_stale_failures` — đọc phần ghi chú ở đó
trước khi sửa ngưỡng, vì nó không đơn thuần là lọc theo trạng thái.
"""
import logging

from sqlalchemy.orm import Session

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from .constants import SyncGrain
from .model import SyncLog
from .service import STALE_FAILURE_HOURS, find_stale_failures

log = logging.getLogger("app.sync_log.tasks")

#: Số nhóm liệt kê thẳng trong thân chuông. Dài hơn thì cắt và đếm phần còn lại
#: — chuông là lời mời mở màn hình, không phải bản báo cáo.
ALERT_MAX_LINES = 5

#: Màn sổ đồng bộ, đã cài sẵn ô lọc trạng thái *Lỗi* (mã 4) để người bấm vào là
#: thấy đúng thứ chuông vừa nói.
ALERT_LINK = "/system/sync-logs?status=4"


def find_alert_recipients(db: Session) -> list[int]:
    """Ai nhận chuông: mọi tài khoản ĐỌC được sổ đồng bộ — đúng nhóm bấm được
    nút *Chạy lại*. Không có ai như thế thì lùi về vai trò `admin`, để cảnh báo
    không rơi vào hư không mà không ai hay.
    """
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import User, UserRole

    role_ids = [row[0] for row in
                db.query(Permission.role_id)
                .filter(Permission.entity == "sync_log",
                        Permission.can_read.is_(True)).all()]
    if not role_ids:
        role_ids = [row[0] for row in db.query(Role.id).filter(Role.code == "admin").all()]
    if not role_ids:
        return []
    rows = (db.query(User.id).join(UserRole, UserRole.user_id == User.id)
            .filter(UserRole.role_id.in_(role_ids), User.is_active.is_(True))
            .distinct().all())
    return [int(row[0]) for row in rows]


def _group_key(row: SyncLog) -> tuple[str, str, str]:
    """Gom dòng lỗi theo THỨ NGƯỜI TA SẼ ĐI XỬ, không theo từng dòng.

    Một phiếu hỏng rồi bị bấm chạy lại ba lần là bốn dòng lỗi nhưng chỉ MỘT việc
    phải làm. Đếm theo dòng thì con số trong chuông phóng đại đúng những chỗ đã
    có người cố gắng.
    """
    if row.grain == int(SyncGrain.RUN):
        return (row.source_label, row.job_label or "(không rõ việc)", f"run:{row.id}")
    return (row.source_label, row.entity_label or "(không rõ đối tượng)",
            row.legacy_id or f"row:{row.id}")


def build_alert_body(rows: list[SyncLog], hours: int) -> str:
    """Thân chuông: tổng số, rồi vài nhóm lớn nhất."""
    groups: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        source_label, kind_label, item = _group_key(row)
        groups.setdefault((source_label, kind_label), set()).add(item)

    total_items = sum(len(items) for items in groups.values())
    ordered = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    lines = [f"- {source} / {kind}: {len(items)} mục"
             for (source, kind), items in ordered[:ALERT_MAX_LINES]]
    if len(ordered) > ALERT_MAX_LINES:
        lines.append(f"- … và {len(ordered) - ALERT_MAX_LINES} nhóm khác")

    head = (f"Sổ đồng bộ đang có {total_items} mục lỗi quá {hours} giờ mà chưa "
            f"có lượt nào chạy lại thành công ({len(rows)} dòng sổ).")
    tail = ("Mở Hệ thống › Sổ đồng bộ, lọc trạng thái Lỗi để xem nguyên văn lỗi "
            "và bấm Chạy lại.")
    return "\n".join([head, *lines, tail])


def run_stale_failure_alert(db: Session, hours: int = STALE_FAILURE_HOURS) -> dict:
    """Quét sổ, có dòng nào chưa vá thì bắn chuông. Tách khỏi vỏ Celery để bài
    kiểm gọi thẳng được."""
    rows = find_stale_failures(db, hours=hours)
    if not rows:
        return {"stale": 0, "notified": 0}

    from app.modules.notification.model import Notification

    recipients = find_alert_recipients(db)
    body = build_alert_body(rows, hours)
    title = f"Đồng bộ: {len(rows)} dòng lỗi quá {hours} giờ chưa xử"
    for user_id in recipients:
        db.add(Notification(user_id=user_id, title=title, body=body, link=ALERT_LINK))
    db.commit()
    log.info("Cảnh báo sổ đồng bộ: %s dòng lỗi, báo cho %s người.",
             len(rows), len(recipients))
    return {"stale": len(rows), "notified": len(recipients)}


@celery_app.task(name="sync_log.alert_stale_failures")
def alert_stale_failures_task() -> dict:
    db = SessionLocal()
    try:
        return run_stale_failure_alert(db)
    except Exception as e:  # noqa: BLE001 — chuông hỏng không được kéo theo gì khác
        db.rollback()
        log.exception("Không quét được dòng lỗi tồn của sổ đồng bộ")
        return {"status": "failed", "error": str(e)[:200]}
    finally:
        db.close()
