"""Hạ tầng import: lưu file, tạo/đọc batch, ghi log, đếm kết quả."""
import uuid

from sqlalchemy.orm import Session

from app.core.storage import upload_fileobj
from app.modules.attachment.model import StoredFile

from .model import ImportBatch, ImportLog, ImportStatus, LogLevel

# tăng đếm theo level của log
_LEVEL_COUNTER = {
    LogLevel.WARNING: "warning_count",
    LogLevel.REVIEW: "review_count",
    LogLevel.ERROR: "error_count",
}


def save_upload(db: Session, upload_file, user_id: int) -> StoredFile:
    """Lưu file .xlsx lên storage (dùng chung StoredFile) — worker đọc lại qua file_key."""
    f = upload_file
    f.file.seek(0, 2); size = f.file.tell(); f.file.seek(0)
    key = f"import/{uuid.uuid4().hex}_{f.filename}"
    url = upload_fileobj(f.file, key, f.content_type or "")
    sf = StoredFile(filename=f.filename or "import.xlsx", file_key=key, url=url,
                    content_type=f.content_type or "", size=size,
                    created_by=user_id, updated_by=user_id)
    db.add(sf); db.commit(); db.refresh(sf)
    return sf


def create_batch(db: Session, module: int, mode: int, sf: StoredFile, user_id: int) -> ImportBatch:
    b = ImportBatch(module=module, mode=mode, filename=sf.filename, file_id=sf.id,
                    file_size=sf.size or 0, sheet_info="", error_summary="",
                    status=ImportStatus.QUEUED, created_by=user_id, updated_by=user_id)
    db.add(b); db.commit(); db.refresh(b)
    return b


def add_log(db: Session, batch: ImportBatch, sheet: str, row_no: int, level: int,
            category: str, message: str, ref_key: str = "", target_code: str = "", raw: str = "") -> None:
    """Ghi 1 dòng log + tăng đếm theo level (INFO không tính vào cảnh báo/lỗi)."""
    db.add(ImportLog(batch_id=batch.id, sheet=sheet, row_no=row_no, level=int(level),
                     category=category, message=message[:60000], ref_key=ref_key[:120],
                     target_code=target_code[:50], raw=raw[:60000], created_by=batch.created_by))
    col = _LEVEL_COUNTER.get(level)
    if col:
        setattr(batch, col, (getattr(batch, col) or 0) + 1)


def list_batches(db: Session, module: int | None, status: int | None, pg: dict):
    q = db.query(ImportBatch)
    if module:
        q = q.filter(ImportBatch.module == module)
    if status is not None:
        q = q.filter(ImportBatch.status == status)
    total = q.count()
    items = q.order_by(ImportBatch.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def get_batch(db: Session, bid: int) -> ImportBatch | None:
    return db.get(ImportBatch, bid)


def get_logs(db: Session, batch_id: int, level: int | None, pg: dict):
    q = db.query(ImportLog).filter(ImportLog.batch_id == batch_id)
    if level is not None:
        q = q.filter(ImportLog.level == level)
    total = q.count()
    items = (q.order_by(ImportLog.level.desc(), ImportLog.id.asc())
             .offset(pg["offset"]).limit(pg["limit"]).all())
    return total, items
