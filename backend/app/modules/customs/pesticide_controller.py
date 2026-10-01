"""API mục «Thuốc BVTV» của Tra cứu thị trường (29/09/2026).

Hai khóa quyền:
  · ĐỌC = `customs_price.read` — ai xem được Tra cứu thị trường (mục này là một phần của màn đó);
  · SỬA = `customs_pesticide` (duoc-CR-490): create / write / delete từng thuốc, và nạp lại cả
    danh mục từ tệp (`write` — nạp còn gắn lại hoạt chất cho MỌI dòng hàng hải quan). Tách khỏi
    `customs_price` giống `customs_regulation`: người nạp tờ khai không nhất thiết giữ danh mục.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import (pesticide_edit_service, pesticide_reader, pesticide_related_service,
               pesticide_service)
from .pesticide_schema import PesticideIn

ENTITY = "customs_price"
EDIT_ENTITY = "customs_pesticide"
#  Tệp JSON của bản cào ~18 MB (Excel ~3,4 MB). Trần 30 MB: đủ cho nguồn lớn dần mà JSON đã
#  giải ra vẫn nằm gọn trong trần bộ nhớ 2 GB của container api.
MAX_UPLOAD_BYTES = 30 * 1024 * 1024

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
    """Thay TOÀN BỘ danh mục bằng tệp `thuoc-bvtv.json` / `thuoc-bvtv.xlsx` của bản cào."""
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Tệp quá lớn (tối đa 30 MB)")
    try:
        records = pesticide_reader.read_file(file.filename or "", content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    result = pesticide_service.replace_catalog(db, records, user.id, file.filename or "")
    return success(result, f"Đã nạp {result['pesticides']:,} thuốc BVTV".replace(",", "."))
