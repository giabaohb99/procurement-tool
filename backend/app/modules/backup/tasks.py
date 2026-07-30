"""Celery task sao lưu CSDL — chạy ở worker (theo lịch beat hoặc bấm tay)."""
import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from . import service


@celery_app.task(name="backup.run")
def run_backup_task(source: str = "auto", actor_id: int = 0) -> dict:
    db = SessionLocal()
    try:
        rec = service.run_backup(db, actor_id=actor_id, source=source)
        return {"status": "success", "id": rec.id, "key": rec.file_key, "size": rec.size_bytes}
    except Exception as e:  # noqa: BLE001
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
