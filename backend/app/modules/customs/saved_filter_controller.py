"""bao-CR-496 — hai đường API thêm cho màn Tra cứu giá hải quan.

  · `/api/customs/saved-filters`          — bộ lọc đã lưu, riêng từng tài khoản (F07);
  · `/api/customs/imports/{bid}/rows`     — nhật ký TỪNG DÒNG của lô nạp + tổng theo kết cục (F01).

Khóa quyền: `customs_price.read` là đủ cho cả hai — đọc được màn thì lưu được bộ lọc của
mình và xem được lô đã nạp (đường `/imports/{bid}/logs` cũ cũng chỉ đòi `read`). Tách tệp
khỏi `controller.py` vì bao-CR-493 đang sửa tệp đó — gộp không đụng nhau.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success
from app.modules.import_tool import service as import_service
from app.modules.import_tool.model import IMPORT_ROW_STATUS_LABELS, ImportModule, ImportRowStatus

from . import row_log
from . import saved_filter_service as filters
from .schema import SavedFilterCreate, SavedFilterOut, SavedFilterUpdate

ENTITY = "customs_price"

router = APIRouter(prefix="/api/customs", tags=["customs"])


# ── Bộ lọc đã lưu ───────────────────────────────────────────────────────────────────────────
def _out(obj) -> dict:
    return SavedFilterOut.model_validate(obj).model_dump()


@router.get("/saved-filters")
def list_saved_filters(db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success({"items": [_out(x) for x in filters.list_for(db, user.id)],
                    "max_per_user": filters.MAX_PER_USER})


@router.post("/saved-filters")
def create_saved_filter(body: SavedFilterCreate, db: Session = Depends(get_db),
                        user=Depends(require(ENTITY, "read"))):
    obj = filters.create(db, user.id, body.name, body.params)
    return success(_out(obj), "Đã lưu bộ lọc")


@router.patch("/saved-filters/{fid}")
def update_saved_filter(fid: int, body: SavedFilterUpdate, db: Session = Depends(get_db),
                        user=Depends(require(ENTITY, "read"))):
    obj = filters.update(db, user.id, fid, body.name, body.params)
    return success(_out(obj), "Đã cập nhật bộ lọc")


@router.delete("/saved-filters/{fid}")
def delete_saved_filter(fid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    filters.delete(db, user.id, fid)
    return success(None, "Đã xóa bộ lọc")


# ── Nhật ký từng dòng của lô ────────────────────────────────────────────────────────────────
def _get_customs_batch(db: Session, bid: int):
    b = import_service.get_batch(db, bid)
    if not b or b.module != ImportModule.CUSTOMS_DECLARATION:
        raise HTTPException(404, "Không tìm thấy lô nạp dữ liệu hải quan")
    return b


@router.get("/imports/{bid}/rows/summary")
def batch_row_summary(bid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    _get_customs_batch(db, bid)
    counts = row_log.count_rows(db, bid)
    counts["labels"] = {int(s): IMPORT_ROW_STATUS_LABELS[s] for s in ImportRowStatus if s != ImportRowStatus.NONE}
    return success(counts)


@router.get("/imports/{bid}/rows")
def batch_rows(bid: int, row_status: int | None = Query(None, ge=1, le=3), pg: dict = Depends(pagination),
               db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    _get_customs_batch(db, bid)
    total, items = row_log.list_rows(db, bid, row_status, pg)
    return success({"total": total, "items": items, "page": pg["page"], "page_size": pg["page_size"]})
