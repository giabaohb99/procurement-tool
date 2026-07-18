from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import get_current_user, user_has_permission
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success
from app.core.storage import download_bytes
from app.modules.attachment.model import StoredFile

from . import service
from .model import ImportModule
from .tasks import run_import

router = APIRouter(prefix="/api/imports", tags=["import"])


def _ent(module: int) -> str:
    return "survey" if module == ImportModule.SURVEY else "purchase_order"


def _guard(db, user, module: int, action: str):
    if not user_has_permission(db, user, _ent(module), action):
        raise HTTPException(403, "Không có quyền import mục này")


def _guard_view(db, user):
    if not (user_has_permission(db, user, "survey", "read")
            or user_has_permission(db, user, "purchase_order", "read")):
        raise HTTPException(403, "Không có quyền xem import")


def _batch_out(db, b) -> dict:
    return {"id": b.id, "module": b.module, "mode": b.mode, "filename": b.filename,
            "file_id": b.file_id, "file_size": b.file_size, "status": b.status,
            "sheet_info": b.sheet_info, "total_rows": b.total_rows,
            "created_count": b.created_count, "updated_count": b.updated_count, "skipped_count": b.skipped_count,
            "warning_count": b.warning_count, "error_count": b.error_count, "review_count": b.review_count,
            "error_summary": b.error_summary, "created_at": b.created_at, "created_by": b.created_by,
            "created_by_name": resolve_actor(db, b.created_by),
            "started_at": b.started_at, "finished_at": b.finished_at}


def _log_out(lg) -> dict:
    return {"id": lg.id, "sheet": lg.sheet, "row_no": lg.row_no, "level": lg.level,
            "category": lg.category, "message": lg.message, "ref_key": lg.ref_key, "target_code": lg.target_code}


@router.post("")
def upload_import(module: int = Form(...), mode: int = Form(0), file: UploadFile = File(...),
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Upload .xlsx -> lưu file -> tạo batch -> đẩy Celery task (trả batch_id ngay)."""
    _guard(db, user, module, "create")
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(400, "Chỉ nhận file .xlsx")
    sf = service.save_upload(db, file, user.id)
    batch = service.create_batch(db, module, mode, sf, user.id)
    run_import.delay(batch.id)
    return success(_batch_out(db, batch), "Đã nhận file — đang import nền, sẽ báo khi xong", 201)


@router.get("")
def list_imports(module: int | None = Query(None), status: int | None = Query(None),
                 pg: dict = Depends(pagination), db: Session = Depends(get_db), user=Depends(get_current_user)):
    _guard_view(db, user)
    total, items = service.list_batches(db, module, status, pg)
    return success({"total": total, "items": [_batch_out(db, b) for b in items]})


@router.get("/{bid}")
def get_import(bid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _guard_view(db, user)
    b = service.get_batch(db, bid)
    if not b:
        raise HTTPException(404, "Không tìm thấy lần import")
    return success(_batch_out(db, b))


@router.get("/{bid}/logs")
def get_import_logs(bid: int, level: int | None = Query(None),
                    pg: dict = Depends(pagination), db: Session = Depends(get_db), user=Depends(get_current_user)):
    _guard_view(db, user)
    total, items = service.get_logs(db, bid, level, pg)
    return success({"total": total, "items": [_log_out(x) for x in items]})


@router.get("/{bid}/file")
def download_import_file(bid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _guard_view(db, user)
    b = service.get_batch(db, bid)
    if not b or not b.file_id:
        raise HTTPException(404, "Không có file")
    sf = db.get(StoredFile, b.file_id)
    if not sf:
        raise HTTPException(404, "Không tìm thấy file đã lưu")
    data = download_bytes(sf.file_key)
    return Response(content=data,
                    media_type=sf.content_type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{sf.filename}"'})
