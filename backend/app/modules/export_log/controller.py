from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import get_current_user, user_has_permission
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success
from app.core.storage import download_bytes
from app.modules.attachment.model import StoredFile

from . import service
from .registry import EXPORT_ADAPTERS, is_exportable

router = APIRouter(prefix="/api/exports", tags=["export"])


def _content_disposition(filename: str) -> str:
    """An toàn cho tên file có dấu tiếng Việt (RFC 5987)."""
    ascii_name = (filename or "").encode("ascii", "ignore").decode() or "export"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename or 'export')}"


def _log_out(db, x) -> dict:
    return {"id": x.id, "entity": x.entity,
            "entity_label": EXPORT_ADAPTERS.get(x.entity, {}).get("label", x.entity),
            "module": EXPORT_ADAPTERS.get(x.entity, {}).get("module", ""),
            "fmt": x.fmt, "row_count": x.row_count, "filename": x.filename,
            "file_size": x.file_size, "has_file": bool(x.file_id), "filter_summary": x.filter_summary,
            "created_at": x.created_at, "created_by": x.created_by,
            "created_by_name": resolve_actor(db, x.created_by)}


def _guard_view(db, user):
    if not (service.can_view_any(db, user) or user_has_permission(db, user, "setting", "read")):
        raise HTTPException(403, "Không có quyền xem nhật ký Xuất")


@router.get("")
def list_exports(entity: str | None = Query(None), fmt: str | None = Query(None),
                 date_from: str | None = Query(None), date_to: str | None = Query(None),
                 created_by_name: str | None = Query(None),
                 pg: dict = Depends(pagination), db: Session = Depends(get_db), user=Depends(get_current_user)):
    _guard_view(db, user)
    total, items = service.list_exports(db, entity, fmt, date_from, date_to, created_by_name, pg)
    return success({"total": total, "items": [_log_out(db, x) for x in items],
                    "creators": service.distinct_creators(db)})


@router.get("/entities")
def list_entities(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Các bảng người dùng được phép xuất — đổ vào ô chọn của hộp thoại Xuất."""
    return success(service.available_entities(db, user))


@router.get("/run")
def run_export(entity: str = Query(...), format: str = Query("xlsx"),
               db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Xuất một bảng ra CSV/XLSX (theo phạm vi dữ liệu) + ghi nhật ký, trả file tải về."""
    if not is_exportable(entity):
        raise HTTPException(400, "Bảng này chưa hỗ trợ xuất")
    if format not in ("csv", "xlsx"):
        raise HTTPException(400, "Định dạng chỉ nhận csv hoặc xlsx")
    if not user_has_permission(db, user, entity, "export"):
        raise HTTPException(403, f"Không có quyền xuất {entity}")
    content, filename, media, _n = service.run_export(db, user, entity, format)
    return Response(content=content, media_type=media,
                    headers={"Content-Disposition": _content_disposition(filename)})


@router.get("/{bid}")
def get_export(bid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Chi tiết một lần xuất. Đặt SAU /entities và /run để không nuốt hai path đó."""
    _guard_view(db, user)
    x = service.get_export(db, bid)
    if not x:
        raise HTTPException(404, "Không tìm thấy lần xuất")
    return success(_log_out(db, x))


@router.get("/{bid}/file")
def download_export_file(bid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tải lại đúng file đã xuất (ảnh chụp lúc xuất, không sinh lại)."""
    _guard_view(db, user)
    x = service.get_export(db, bid)
    if not x or not x.file_id:
        raise HTTPException(404, "Không có file")
    sf = db.get(StoredFile, x.file_id)
    if not sf:
        raise HTTPException(404, "Không tìm thấy file đã lưu")
    try:
        data = download_bytes(sf.file_key)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Không đọc được file từ kho lưu trữ")
    return Response(content=data,
                    media_type=sf.content_type or "application/octet-stream",
                    headers={"Content-Disposition": _content_disposition(sf.filename)})
