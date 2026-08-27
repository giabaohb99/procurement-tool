from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import get_current_user, user_has_permission
from app.core.base_controller import pagination
from app.core.config import settings
from app.core.database import get_db
from app.core.response import success
from app.core.storage import download_bytes
from app.modules.attachment.model import StoredFile

from . import service
from .catalog_import import ImportValidationError
from .model import ImportMode, ImportStatus
from .tasks import precheck_headers, run_import, workbook_from_bytes

router = APIRouter(prefix="/api/imports", tags=["import"])


def _content_disposition(filename: str) -> str:
    """Content-Disposition attachment an toàn cho tên file có dấu tiếng Việt (RFC 5987).
    Header HTTP chỉ nhận Latin-1 → tên có ký tự tiếng Việt phải encode, nếu không sẽ 500."""
    ascii_name = (filename or "").encode("ascii", "ignore").decode() or "download.xlsx"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename or 'download.xlsx')}"


def _guard(db, user, action: str):
    if not user_has_permission(db, user, "import", action):
        raise HTTPException(403, "Không có quyền thao tác Import")


def _guard_view(db, user):
    if not user_has_permission(db, user, "import", "read"):
        raise HTTPException(403, "Không có quyền xem Import")


def _batch_out(db, b) -> dict:
    return {"id": b.id, "module": b.module, "mode": b.mode, "filename": b.filename,
            "file_id": b.file_id, "file_size": b.file_size, "status": b.status,
            "sheet_info": b.sheet_info, "total_rows": b.total_rows,
            "created_count": b.created_count, "updated_count": b.updated_count,
            "deleted_count": b.deleted_count, "skipped_count": b.skipped_count,
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
    """Upload .xlsx/.csv -> lưu file -> tạo batch -> đẩy Celery task (trả batch_id ngay)."""
    _guard(db, user, "create")
    name = (file.filename or "").lower()
    if not name.endswith(".xlsx") and not name.endswith(".csv"):
        raise HTTPException(400, "Chỉ nhận file .xlsx hoặc .csv")

    # Kiểm tra file có ĐÚNG bảng không NGAY tại đây (đồng bộ): sai thì báo lỗi luôn
    # cho hộp thoại upload, KHÔNG lưu file, KHÔNG tạo batch.
    raw = file.file.read()
    file.file.seek(0)
    try:
        precheck_headers(module, workbook_from_bytes(file.filename or "", raw))
    except ImportValidationError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Không đọc được file — kiểm tra lại định dạng .xlsx/.csv")

    sf = service.save_upload(db, file, user.id)
    batch = service.create_batch(db, module, mode, sf, user.id)
    run_import.delay(batch.id)
    return success(_batch_out(db, batch), "Đã nhận file — đang import nền, sẽ báo khi xong", 201)


@router.get("")
def list_imports(request: Request, module: int | None = Query(None), status: int | None = Query(None),
                 mode: int | None = Query(None), subsystem: str | None = Query(None),
                 date_from: str | None = Query(None), date_to: str | None = Query(None),
                 created_by_name: str | None = Query(None), filename: str | None = Query(None),
                 pg: dict = Depends(pagination), db: Session = Depends(get_db), user=Depends(get_current_user)):
    _guard_view(db, user)
    total, items = service.list_batches(db, request, module, status, mode, date_from, date_to,
                                        created_by_name, filename, subsystem, pg)
    creators = service.distinct_creators(db)
    return success({"total": total, "items": [_batch_out(db, b) for b in items], "creators": creators})


@router.get("/template")
def download_template(module: int = Query(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tải file .xlsx mẫu (đúng bộ cột) cho một đối tượng danh mục. Đặt TRƯỚC /{bid}
    để 'template' không bị bắt làm bid (int) → 422."""
    _guard_view(db, user)
    from . import catalog_import, doc_import
    if catalog_import.is_catalog_module(module):
        data = catalog_import.build_template(module)
        sheet = catalog_import.ADAPTERS[module]["sheet"]
    elif doc_import.is_doc_module(module):
        data = doc_import.build_template(module)
        sheet = doc_import.DOC_ADAPTERS[module]["sheet"]
    else:
        raise HTTPException(400, "Đối tượng này chưa có file mẫu")
    fname = f"mau_import_{sheet.replace(' ', '_').lower()}.xlsx"
    return Response(content=data,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": _content_disposition(fname)})


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


@router.delete("/dev/surveys")
def dev_delete_surveys(ids: str = Query(""), all_imported: bool = Query(False),
                       db: Session = Depends(get_db), user=Depends(get_current_user)):
    """DEV-ONLY: xóa phiếu khảo sát theo ids (vd '97,98,99') hoặc toàn bộ phiếu do import tạo
    (all_imported=true). Chỉ chạy khi DEV_MODE=true — bỏ qua guard trạng thái để dọn data test."""
    if not settings.DEV_MODE:
        raise HTTPException(403, "API dev-only — DEV_MODE đang tắt")
    from app.modules.survey import service as survey_service
    from app.modules.survey.model import Survey
    if all_imported:
        sids = [s.id for s in db.query(Survey).filter(Survey.import_key != "").all()]
    else:
        sids = [int(x) for x in ids.split(",") if x.strip().isdigit()]
    n = 0
    for sid in sids:
        if db.get(Survey, sid):
            survey_service.delete_survey(db, sid, user.id); n += 1
    return success({"deleted": n, "ids": sids}, f"Đã xóa {n} phiếu (dev)")


@router.post("/{bid}/revert")
def revert_import(bid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Hoàn tác 1 batch đã ghi: phiếu mới -> xoá, phiếu cũ -> khôi phục snapshot."""
    b = service.get_batch(db, bid)
    if not b:
        raise HTTPException(404, "Không tìm thấy lần import")
    _guard(db, user, "delete")
    res = service.revert_batch(db, b, user.id)
    if not res.get("ok"):
        raise HTTPException(400, res.get("message", "Không thể hoàn tác"))
    return success(_batch_out(db, b), res["message"])


@router.post("/{bid}/commit")
def commit_import(bid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Ghi thật từ một bản CHẠY THỬ: tạo batch APPLY dùng lại đúng file, chạy nền."""
    b = service.get_batch(db, bid)
    if not b:
        raise HTTPException(404, "Không tìm thấy lần import")
    _guard(db, user, "create")
    if b.mode != ImportMode.DRY_RUN:
        raise HTTPException(400, "Chỉ ghi thật được từ bản chạy thử")
    if b.status != ImportStatus.DONE:
        raise HTTPException(400, "Bản chạy thử chưa hoàn tất, không thể ghi thật")
    new = service.commit_dry_run(db, b, user.id)
    run_import.delay(new.id)
    return success(_batch_out(db, new), "Đang ghi thật dữ liệu — sẽ báo khi xong", 201)


@router.get("/{bid}/file")
def download_import_file(bid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _guard_view(db, user)
    b = service.get_batch(db, bid)
    if not b or not b.file_id:
        raise HTTPException(404, "Không có file")
    sf = db.get(StoredFile, b.file_id)
    if not sf:
        raise HTTPException(404, "Không tìm thấy file đã lưu")
    try:
        data = download_bytes(sf.file_key)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Không đọc được file từ kho lưu trữ")
    return Response(content=data,
                    media_type=sf.content_type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": _content_disposition(sf.filename)})
