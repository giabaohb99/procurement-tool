"""API mục «Thuốc BVTV» của Tra cứu thị trường (29/09/2026).

Hai khóa quyền:
  · ĐỌC = `customs_price.read` — ai xem được Tra cứu thị trường (mục này là một phần của màn đó);
  · SỬA = `customs_pesticide` (duoc-CR-490): create / write / delete từng thuốc, và nạp lại cả
    danh mục từ tệp (`write` — nạp còn gắn lại hoạt chất cho MỌI dòng hàng hải quan). Tách khỏi
    `customs_price` giống `customs_regulation`: người nạp tờ khai không nhất thiết giữ danh mục.
"""
import os

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import (pesticide_edit_service, pesticide_export_service, pesticide_merge_service,
               pesticide_reader, pesticide_related_service, pesticide_service)
from .pesticide_schema import PesticideIn

ENTITY = "customs_price"
EDIT_ENTITY = "customs_pesticide"
XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

router = APIRouter(prefix="/api/customs/pesticides", tags=["customs"])


@router.get("")
def list_pesticides(q: str = "", status: int | None = Query(None, ge=0, le=9),
                    pest_group: str = "", sector: str = "", banned_only: bool = False,
                    banned_regulation_id: int | None = Query(None, ge=1),
                    pg: dict = Depends(pagination),
                    db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    total, items = pesticide_service.list_pesticides(db, q, status, pest_group, sector,
                                                     pg["offset"], pg["limit"], banned_only,
                                                     banned_regulation_id)
    return success({"total": total, "items": items})


@router.get("/options")
def get_options(db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(pesticide_service.options(db))


@router.get("/export")
def export_pesticides(scope: str = Query("page", pattern="^(page|all)$"),
                      q: str = "", status: int | None = Query(None, ge=0, le=9),
                      pest_group: str = "", sector: str = "", banned_only: bool = False,
                      banned_regulation_id: int | None = Query(None, ge=1),
                      pg: dict = Depends(pagination),
                      db: Session = Depends(get_db), user=Depends(require(ENTITY, "export"))):
    """Xuất Excel mục «Thuốc BVTV» — đặt TRƯỚC `/{pesticide_id}` để "export" không bị nuốt làm id.

    `scope=all` = cả danh mục, nạp lại được ngay bằng «Nạp danh mục» (xem `pesticide_export_
    service`). `scope=page` = đúng trang đang lọc/xem, dùng để đối chiếu — KHÔNG nhằm nạp lại.
    """
    path, filename = pesticide_export_service.export_to_tempfile(
        db, user, scope, q, status, pest_group, sector, banned_only, banned_regulation_id,
        pg["page"], pg["offset"], pg["limit"])
    return FileResponse(path, filename=filename, media_type=XLSX_MEDIA,
                        background=BackgroundTask(os.remove, path))


@router.get("/{pesticide_id}/related")
def get_related_pesticides(pesticide_id: int,
                           limit: int = Query(pesticide_related_service.RELATED_LIMIT, ge=1,
                                              le=pesticide_related_service.MAX_RELATED_LIMIT),
                           db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """«Sản phẩm khác cùng công ty» + «Thuốc cùng hoạt chất» của trang chi tiết (01/10/2026)."""
    return success(pesticide_related_service.related_pesticides(db, pesticide_id, limit))


@router.get("/{pesticide_id}")
def get_pesticide(pesticide_id: int, db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "read"))):
    return success(pesticide_service.get_pesticide(db, pesticide_id))


@router.post("")
def create_pesticide(body: PesticideIn, db: Session = Depends(get_db),
                     user=Depends(require(EDIT_ENTITY, "create"))):
    return success(pesticide_edit_service.create_pesticide(db, body, user.id), "Đã thêm thuốc BVTV")


@router.patch("/{pesticide_id}")
def update_pesticide(pesticide_id: int, body: PesticideIn, db: Session = Depends(get_db),
                     user=Depends(require(EDIT_ENTITY, "write"))):
    return success(pesticide_edit_service.update_pesticide(db, pesticide_id, body, user.id),
                   "Đã lưu thuốc BVTV")


@router.delete("/{pesticide_id}")
def delete_pesticide(pesticide_id: int, db: Session = Depends(get_db),
                     user=Depends(require(EDIT_ENTITY, "delete"))):
    pesticide_edit_service.delete_pesticide(db, pesticide_id, user.id)
    return success(None, "Đã xóa thuốc BVTV")


@router.post("/import")
def import_catalog(file: UploadFile = File(...), db: Session = Depends(get_db),
                   user=Depends(require(EDIT_ENTITY, "write"))):
    """Nạp danh mục từ tệp `thuoc-bvtv.json`/`thuoc-bvtv.xlsx` của bản cào, HOẶC tệp hệ thống
    tự xuất (C1, 02/10/2026): tệp xuất TOÀN BỘ / bản cào gốc → THAY TOÀN BỘ như trước giờ; tệp
    xuất THEO TRANG (sheet ẩn `_xuat` scope=page — `pesticide_export_marker`) → chỉ CẬP NHẬT
    đúng thuốc có trong tệp, không đụng phần còn lại (`pesticide_merge_service`)."""
    content = file.file.read(pesticide_reader.MAX_UPLOAD_BYTES + 1)
    if len(content) > pesticide_reader.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Tệp quá lớn (tối đa 30 MB)")
    try:
        records, mode = pesticide_reader.read_file_with_mode(file.filename or "", content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if mode == "merge":
        result = pesticide_merge_service.merge_catalog(db, records, user.id, file.filename or "")
        updated_fmt = f"{result['updated']:,}".replace(",", ".")
        added_fmt = f"{result['added']:,}".replace(",", ".")
        message = f"Đã cập nhật {updated_fmt} thuốc (thêm mới {added_fmt}), giữ nguyên phần còn lại"
    else:
        result = pesticide_service.replace_catalog(db, records, user.id, file.filename or "")
        pesticides_fmt = f"{result['pesticides']:,}".replace(",", ".")
        message = f"Đã thay toàn bộ danh mục: {pesticides_fmt} thuốc"
    return success(result, message)
