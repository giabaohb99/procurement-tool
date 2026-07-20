"""Celery task chạy import ở worker: cập nhật trạng thái + đếm + log, xong bắn chuông."""
import traceback
from datetime import datetime
from io import BytesIO

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.storage import download_bytes
from app.modules.attachment.model import StoredFile
from app.modules.notification.model import Notification

from . import po_import, survey_import
from .model import ImportBatch, ImportMode, ImportModule, ImportStatus

_MODULE_LABEL = {ImportModule.SURVEY: "Khảo sát", ImportModule.PURCHASE_ORDER: "Đơn mua hàng"}


@celery_app.task(name="import_tool.run_import")
def run_import(batch_id: int) -> dict:
    db = SessionLocal()
    try:
        batch = db.get(ImportBatch, batch_id)
        if not batch:
            return {"error": "batch not found"}
        batch.status = ImportStatus.RUNNING
        batch.started_at = datetime.utcnow()
        db.commit()

        sf = db.get(StoredFile, batch.file_id)
        if not sf:
            raise RuntimeError("Không tìm thấy file đã lưu")
        import openpyxl
        wb = openpyxl.load_workbook(BytesIO(download_bytes(sf.file_key)), data_only=True, read_only=False)

        if batch.module == ImportModule.SURVEY:
            survey_import.run(db, batch, wb, apply=(batch.mode == ImportMode.APPLY))
        elif batch.module == ImportModule.PURCHASE_ORDER:
            po_import.run(db, batch, wb, apply=(batch.mode == ImportMode.APPLY))
        else:
            raise RuntimeError("Module import chưa hỗ trợ")

        db.refresh(batch)
        _notify(db, batch, ok=True)
        return {"status": "done", "created": batch.created_count, "updated": batch.updated_count,
                "error": batch.error_count}
    except Exception as e:  # noqa: BLE001
        db.rollback()
        b = db.get(ImportBatch, batch_id)
        if b:
            b.status = ImportStatus.FAILED
            b.error_summary = f"{e}\n{traceback.format_exc()[-2000:]}"
            b.finished_at = datetime.utcnow()
            db.commit()
            _notify(db, b, ok=False)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def _notify(db, batch, ok: bool) -> None:
    label = _MODULE_LABEL.get(batch.module, "")
    mode = "chạy thử" if batch.mode == ImportMode.DRY_RUN else "ghi"
    if ok:
        title = f"Import {label} ({mode}) xong"
        body = f"{batch.created_count} tạo · {batch.updated_count} cập nhật · {batch.error_count} lỗi"
    else:
        title = f"Import {label} lỗi"
        body = "Xem chi tiết log để xử lý"
    db.add(Notification(user_id=batch.created_by, title=title, body=body,
                        link=f"/import-batches/{batch.id}", created_by=batch.created_by))
    db.commit()
