"""Hai việc nền của cụm nhật ký, đợt P6 (bao-CR-448).

- `system_log.detect_anomalies` — mỗi 15 phút, quét cửa sổ 30 phút vừa qua và
  báo chuông quản trị. Logic ở `anomaly.py`.
- `system_log.cleanup_expired` — mỗi đêm 03:50, SAU việc đóng gói tháng (03:00
  ngày 1) và sau việc dọn GET (03:40): xóa bốn bảng nhật ký quá 16 tháng, chỉ
  tháng nào đã có gói R2. Logic ở `retention.py`.

Cả hai cùng nếp với `request_log.cleanup`: chưa nối R2 thì việc dọn tự tắt và
nói ra bằng `status: skipped` chứ không ném lỗi — máy dev không có R2 là chuyện
thường, còn làm đỏ bảng việc nền mỗi đêm thì ba hôm sau không ai đọc nữa.
"""
import logging
from datetime import datetime

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.storage import is_remote_storage_ready

from .anomaly import run_detection
from .retention import cleanup_expired

log = logging.getLogger("app.system_log.tasks")


@celery_app.task(name="system_log.detect_anomalies")
def detect_anomalies_task() -> dict:
    """Quét dấu hiệu bất thường trong cửa sổ vừa qua, báo chuông quản trị."""
    db = SessionLocal()
    try:
        return run_detection(db)
    finally:
        db.close()


@celery_app.task(name="system_log.cleanup_expired")
def cleanup_expired_logs_task(months: int = 0, dry_run: bool = False) -> dict:
    """Dọn bốn bảng nhật ký quá hạn 16 tháng (theo tháng, gói xong mới xóa).

    `months` để chạy tay với hạn khác; `dry_run=True` chỉ đếm và kiểm gói.
    """
    if not is_remote_storage_ready() and not dry_run:
        log.info("Bỏ qua dọn nhật ký 16 tháng: chưa cấu hình R2 nên chưa có bản sao ngoài máy.")
        return {"status": "skipped", "reason": "no_remote_archive", "deleted": {}}
    db = SessionLocal()
    try:
        result = cleanup_expired(db, now=datetime.now(), months=months, dry_run=dry_run)
        log.info("Dọn nhật ký quá %s tháng: %s", months or "16", result)
        return result
    finally:
        db.close()
