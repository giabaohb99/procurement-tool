"""Lưu trữ nhật ký thao tác (audit) định kỳ.

Chính sách: GIỮ VĨNH VIỄN audit trong CSDL (không xóa — phục vụ truy vết/tranh chấp).
Hằng tháng xuất một bản sao audit của THÁNG TRƯỚC ra R2 (jsonl.gz) để lưu trữ độc lập,
tiện trích xuất khi cần mà không phải truy vấn DB. KHÔNG xóa dòng nào khỏi DB.

Key R2: {env}/audit-archive/{YYYY-MM}.jsonl.gz  (env theo STORAGE_PREFIX: prod/dev).
"""
import gzip
import io
import json
from datetime import datetime, timedelta

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.storage import env_prefix, upload_fileobj

from .model import AuditLog


def _month_bounds(ref: datetime) -> tuple[datetime, datetime, str]:
    """Mốc đầu/cuối của THÁNG TRƯỚC so với ref, và nhãn 'YYYY-MM'."""
    first_this = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # lùi 1 ngày để rơi vào tháng trước, rồi lấy ngày 1 của tháng đó
    last_prev = first_this - timedelta(days=1)
    start = last_prev.replace(day=1)
    return start, first_this, f"{start:%Y-%m}"


@celery_app.task(name="audit.archive")
def archive_audit_task(month: str | None = None) -> dict:
    """Xuất audit của tháng trước ra R2. Trả về số dòng + key. Không xóa dữ liệu.

    month='YYYY-MM' (tùy chọn) để xuất thủ công 1 tháng cụ thể.
    """
    db = SessionLocal()
    try:
        if month:
            y, m = (int(x) for x in month.split("-"))
            start = datetime(y, m, 1)
            end = datetime(y + (m // 12), (m % 12) + 1, 1)
            label = f"{start:%Y-%m}"
        else:
            start, end, label = _month_bounds(datetime.now())

        rows = (db.query(AuditLog)
                .filter(AuditLog.created_at >= start, AuditLog.created_at < end)
                .order_by(AuditLog.id.asc()).all())
        if not rows:
            return {"status": "empty", "month": label, "rows": 0}

        buf = io.StringIO()
        for r in rows:
            buf.write(json.dumps({
                "id": r.id, "entity": r.entity, "entity_id": r.entity_id,
                "action": r.action, "message": r.message or "",
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }, ensure_ascii=False) + "\n")
        gz = gzip.compress(buf.getvalue().encode("utf-8"), compresslevel=6)
        key = f"{env_prefix()}/audit-archive/{label}.jsonl.gz"
        upload_fileobj(io.BytesIO(gz), key, "application/gzip")
        return {"status": "success", "month": label, "rows": len(rows),
                "key": key, "size": len(gz)}
    except Exception as e:  # noqa: BLE001
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
