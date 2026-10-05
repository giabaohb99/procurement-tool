"""Việc nền của chiều ERP -> app cũ (P3, bao-CR-596).

- `datxe.push_outbound`  — bộ nghe ORM giao sau mỗi lần commit phiếu (`outbound_listener.py`).
- `datxe.retry_outbound` — lưới đỡ 10 phút một lần: gửi lại phiếu có dòng sổ gửi đi đang
  *chờ*/*lỗi* mà chưa có lần gửi thành công nào sau đó, và quét phiếu sửa trong 48 giờ qua
  để vá ca bộ nghe đã commit mà việc gửi chưa kịp giao (tiến trình chết giữa hai bước).
- `datxe.backfill_outbound` — chạy TAY một lần lúc mới bật công tắc: gửi mọi phiếu đang có.

Công tắc tắt thì cả ba kết thúc ngay, không ghi gì.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.modules.sync_log.constants import SyncDirection, SyncGrain, SyncStatus
from app.modules.sync_log.model import SyncLog
from app.modules.sync_log.registry import SOURCE_DATXE
from app.modules.sync_log.service import finish_skipped

from .outbound import MODEL, is_outbound_enabled, push_outbound

LOGGER = logging.getLogger(__name__)

#: Trần số phiếu một vòng gửi lại. Hơn thế thì vấn đề không còn ở từng phiếu.
MAX_RETRY_PER_RUN = 50

#: Cửa sổ quét phiếu vừa sửa để vá ca rơi giữa commit và giao việc.
RECONCILE_HOURS = 48


def _stuck_targets(db) -> list[tuple[str, int]]:
    """(entity, id phiếu) có dòng gửi đi *chờ*/*lỗi* MỚI HƠN lần gửi thành công cuối."""
    base = (SyncLog.source == SOURCE_DATXE,
            SyncLog.grain == int(SyncGrain.RECORD),
            SyncLog.direction == int(SyncDirection.OUTBOUND),
            SyncLog.local_id > 0)
    last_ok = dict(
        ((entity, local_id), newest) for entity, local_id, newest in db.execute(
            select(SyncLog.entity, SyncLog.local_id, func.max(SyncLog.id))
            .where(*base, SyncLog.status == int(SyncStatus.SUCCESS))
            .group_by(SyncLog.entity, SyncLog.local_id)))
    open_rows = db.execute(
        select(SyncLog.entity, SyncLog.local_id, func.max(SyncLog.id))
        .where(*base, SyncLog.status.in_([int(SyncStatus.PENDING), int(SyncStatus.FAILED),
                                          int(SyncStatus.RUNNING)]))
        .group_by(SyncLog.entity, SyncLog.local_id)).all()
    return [(entity, int(local_id)) for entity, local_id, newest in open_rows
            if newest > last_ok.get((entity, local_id), 0)]


def _close_superseded(db, entity: str, local_id: int) -> None:
    """Dòng *chờ* do nút «Chạy lại» đẻ ra: lượt gửi mới đã thay nó, đóng lại cho khỏi treo."""
    for row in db.execute(select(SyncLog).where(
            SyncLog.source == SOURCE_DATXE,
            SyncLog.direction == int(SyncDirection.OUTBOUND),
            SyncLog.entity == entity, SyncLog.local_id == local_id,
            SyncLog.status == int(SyncStatus.PENDING))).scalars():
        finish_skipped(db, row, "Đã gửi lại bằng ảnh chụp mới ở vòng gửi lại", local_id=local_id)


def retry_outbound(db) -> dict:
    stats = {"stuck": 0, "reconciled": 0, "sent": 0, "unchanged": 0, "failed": 0}
    if not is_outbound_enabled():
        stats["status"] = "off"
        return stats
    targets = _stuck_targets(db)
    stats["stuck"] = len(targets)

    #  Chỉ vá PHIẾU TẠO TRÊN ERP chưa sang app cũ (`legacy_id` rỗng). Phiếu có sẵn bên app cũ
    #  thì KHÔNG quét theo mốc sửa: mốc đó nhảy cả khi chiều NHẬN ghi vào, và đẩy lại chúng là
    #  gửi ngược sang app cũ đúng thứ vừa nhận từ nó — thứ duy nhất phải gửi là thao tác của
    #  người dùng ERP, mà thao tác đó đã có bộ nghe ORM và dòng sổ lỗi ở trên lo.
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=RECONCILE_HOURS)
    for entity, model in MODEL.items():
        for (row_id,) in db.execute(select(model.id).where(
                model.updated_at >= since,
                (model.legacy_id.is_(None)) | (model.legacy_id == ""))):
            if (entity, int(row_id)) not in targets:
                targets.append((entity, int(row_id)))
                stats["reconciled"] += 1

    for entity, local_id in targets[:MAX_RETRY_PER_RUN * 4]:
        result = push_outbound(db, entity, local_id)
        status = result.get("status")
        if status == "sent":
            stats["sent"] += 1
        elif status in ("unchanged", "not_sendable"):
            stats["unchanged"] += 1
        elif status in ("failed", "valve"):
            stats["failed"] += 1
        if status in ("sent", "unchanged"):
            _close_superseded(db, entity, local_id)
        if stats["sent"] + stats["failed"] >= MAX_RETRY_PER_RUN:
            break
    return stats


def backfill_outbound(db, entity: str = "") -> dict:
    """Gửi mọi phiếu TẠO TRÊN ERP chưa có bên app cũ (bỏ nháp). Chạy tay một lần khi mới bật
    công tắc. Phiếu đến từ app cũ thì bên đó đã có, không gửi lại."""
    stats = {"sent": 0, "unchanged": 0, "failed": 0, "skipped": 0}
    if not is_outbound_enabled():
        stats["status"] = "off"
        return stats
    for name, model in MODEL.items():
        if entity and name != entity:
            continue
        for (row_id,) in db.execute(select(model.id).where(
                (model.legacy_id.is_(None)) | (model.legacy_id == "")).order_by(model.id)):
            status = push_outbound(db, name, int(row_id)).get("status")
            key = status if status in stats else "skipped"
            stats[key] += 1
    return stats


def _run(fn, *args):
    db = SessionLocal()
    try:
        return fn(db, *args)
    except Exception as exc:  # noqa: BLE001 — việc nền hỏng không được kéo theo gì khác
        db.rollback()
        LOGGER.exception("datxe outbound: việc nền hỏng")
        return {"status": "failed", "error": str(exc)[:200]}
    finally:
        db.close()


@celery_app.task(name="datxe.push_outbound")
def push_outbound_task(entity: str, local_id: int) -> dict:
    return _run(lambda db: push_outbound(db, entity, int(local_id)))


@celery_app.task(name="datxe.retry_outbound")
def retry_outbound_task() -> dict:
    return _run(retry_outbound)


@celery_app.task(name="datxe.backfill_outbound")
def backfill_outbound_task(entity: str = "") -> dict:
    return _run(lambda db: backfill_outbound(db, entity))
