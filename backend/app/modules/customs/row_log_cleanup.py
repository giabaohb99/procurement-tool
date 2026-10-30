"""Dọn nhật ký TỪNG DÒNG của lô nạp hải quan — bao-CR-698.

`row_log.write_row_logs` ghi mỗi dòng tệp một dòng `tab_import_log` (category `customs_row`), kể cả dòng
"Đã có" / "Trùng" bị bỏ qua: hai đợt nạp 26-27/10/2026 đẩy bảng lên 1,56 triệu dòng / 529 MB và bản sao lưu
từ 20 MB lên 128 MB. Số đếm của lô đã nằm sẵn ở `ImportBatch` (created_count + sheet_info.existing_rows /
duplicate_rows), nên chi tiết từng dòng loại thường chỉ cần trong vài tuần đầu để rà.

Luật dọn (A1 / đại ca chốt 30/10):
  · XÓA: Thêm mới, Đã có, Trùng cũ hơn `customs_row_log_keep_days` ngày (mặc định 7, 0 = tắt);
  · GIỮ vĩnh viễn: Lỗi, Ghi đè, Xóa, Bỏ qua, và dòng Thêm mới "nghi sửa giá" (chị Mi còn rà).
Xóa theo lô nhỏ như `system_log.retention._delete_month`, có trần số lô mỗi đêm.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, delete, not_, select
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.logging_policy import CLEANUP_BATCH_SIZE, CLEANUP_MAX_BATCHES
from app.modules.import_tool.model import ImportLog, ImportRowStatus

from .row_log import CATEGORY

log = logging.getLogger("app.customs.row_log_cleanup")

PRUNABLE = (int(ImportRowStatus.NEW), int(ImportRowStatus.EXISTING), int(ImportRowStatus.DUPLICATE))
SUSPECT_MARK = "nghi sửa giá"


def keep_days() -> int:
    """Số ngày giữ; 0 (hoặc âm) = tắt dọn."""
    return max(0, int(app_settings.get("customs_row_log_keep_days") or 0))


def prunable_condition(cutoff: datetime):
    return and_(ImportLog.category == CATEGORY, ImportLog.row_status.in_(PRUNABLE), ImportLog.created_at < cutoff,
                not_(and_(ImportLog.row_status == int(ImportRowStatus.NEW),
                          ImportLog.message.like(f"%{SUSPECT_MARK}%"))))


def cleanup(db: Session, *, now: datetime | None = None, days: int | None = None,
            max_batches: int = CLEANUP_MAX_BATCHES) -> dict:
    days = keep_days() if days is None else max(0, int(days))
    if not days:
        return {"status": "disabled", "deleted": 0}
    cutoff = (now or datetime.now()) - timedelta(days=days)
    condition = prunable_condition(cutoff)
    deleted = batches = 0
    while batches < max_batches:
        ids = [r[0] for r in db.execute(select(ImportLog.id).where(condition).order_by(ImportLog.id.asc())
                                        .limit(CLEANUP_BATCH_SIZE))]
        if not ids:
            break
        db.execute(delete(ImportLog).where(ImportLog.id.in_(ids)))
        db.commit()
        deleted += len(ids)
        batches += 1
    capped = batches >= max_batches
    if capped:
        log.warning("Dọn nhật ký dòng hải quan chạm trần %s lô, đêm sau dọn tiếp.", max_batches)
    log.info("Dọn nhật ký dòng hải quan quá %s ngày: xóa %s dòng.", days, deleted)
    return {"status": "partial" if capped else "success", "deleted": deleted, "keep_days": days,
            "cutoff": cutoff.isoformat()}
