"""Việc nền của phân hệ hải quan — bao-CR-698: dọn nhật ký từng dòng của lô nạp (hằng đêm 02:45);
bao-CR-699: gộp dòng hàng trùng (ngày 1 và 16 lúc 03:30)."""
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from app.core import app_settings

from . import line_merge, read_cache
from .row_log_cleanup import cleanup

log = logging.getLogger("app.customs.tasks")


@celery_app.task(name="customs.cleanup_row_logs")
def cleanup_row_logs_task(days: int | None = None) -> dict:
    """`days` để chạy tay với hạn khác; mặc định lấy `customs_row_log_keep_days` (0 = tắt)."""
    db = SessionLocal()
    try:
        return cleanup(db, days=days)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.exception("Dọn nhật ký dòng hải quan hỏng")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="customs.merge_duplicate_lines")
def merge_duplicate_lines_task(dry_run: bool = False) -> dict:
    """Gộp dòng hàng trùng (`line_merge`). Công tắc customs_line_merge_enabled tắt thì bỏ qua; `dry_run` chỉ đếm."""
    if not app_settings.get("customs_line_merge_enabled") and not dry_run:
        return {"status": "disabled"}
    db = SessionLocal()
    try:
        result = line_merge.run(db, dry_run=dry_run)
        if not dry_run:
            read_cache.clear()   # bao-CR-718: gộp xóa dòng mà MAX(id) không đổi — số đếm đã đệm phải tính lại
        return result
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.exception("Gộp dòng hải quan trùng hỏng")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


#  bao-CR-718 — lô xuất toàn bộ: MỖI TỆP MỘT LẦN CHẠY. Xong một tệp thì tự hẹn tệp kế sau vài giây (countdown), nên
#  task không giữ worker quá một tệp và việc khác chen được giữa hai tệp — không cần hàng đợi / worker riêng.
@celery_app.task(name="customs.export_batch_part")
def export_batch_part_task(batch_id: int) -> dict:
    from . import line_export
    from .constants import EXPORT_FILE_PAUSE_SECONDS
    db = SessionLocal()
    try:
        more = line_export.run_next_part(db, batch_id)
    except Exception as e:  # noqa: BLE001
        log.exception("Lô xuất tra cứu thị trường #%s hỏng", batch_id)
        line_export.mark_failed(db, batch_id, f"Lỗi khi ghi tệp: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
    if more:
        export_batch_part_task.apply_async(args=[batch_id], countdown=EXPORT_FILE_PAUSE_SECONDS)
    return {"status": "success", "batch_id": batch_id, "more": more}


@celery_app.task(name="customs.cleanup_export_batches")
def cleanup_export_batches_task() -> dict:
    """Hằng đêm: lô xuất kẹt quá `EXPORT_STALE_HOURS` giờ thì đánh hỏng; lô quá `customs_export_keep_days` thì xóa tệp."""
    from . import line_export
    db = SessionLocal()
    try:
        return line_export.cleanup(db)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.exception("Dọn lô xuất tra cứu thị trường hỏng")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
