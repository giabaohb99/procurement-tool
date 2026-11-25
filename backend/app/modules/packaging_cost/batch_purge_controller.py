"""API xóa dữ liệu theo LÔ NHẬP của cụm Giá NVL sản xuất (duoc-CR-784, phase 07) — hai đường dưới `/api/imports/{id}`.

Gác KÉP: quyền xem Import (`import.read`) VÀ quyền xóa ở Giá bao bì (`packaging_cost.delete`). Logic ở `batch_purge_service.py`.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, user_has_permission
from app.core.database import get_db
from app.core.response import success
from app.modules.import_tool import service as import_service

from . import batch_purge_service as svc

router = APIRouter(prefix="/api/imports", tags=["import"])


class PurgeBody(BaseModel):
    include_edited: bool = False       # true = xóa luôn dòng đã bị sửa tay sau khi nhập


def _load_batch(db: Session, user, bid: int):
    """Kiểm quyền rồi nạp lô. Quyền kiểm TRƯỚC khi tra lô để người không có quyền không dò được id nào tồn tại."""
    if not user_has_permission(db, user, "import", "read"):
        raise HTTPException(403, "Không có quyền xem Import")
    if not user_has_permission(db, user, "packaging_cost", "delete"):
        raise HTTPException(403, "Xóa dữ liệu theo lô cần quyền xóa ở Giá bao bì")
    batch = import_service.get_batch(db, bid)
    if not batch:
        raise HTTPException(404, "Không tìm thấy lần import")
    return batch


@router.get("/{bid}/purge-preview")
def get_purge_preview(bid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Xem trước xóa theo lô: số dòng sẽ xóa, số dòng đã sửa tay sau khi nhập (tách riêng).

    Quyền: `import.read` + `packaging_cost.delete`. Lỗi 400 nếu lô không phải Định mức / Báo giá / Sổ Misa, là bản chạy thử
    hoặc chưa hoàn tất; 404 khi không có lô.
    """
    batch = _load_batch(db, user, bid)
    try:
        return success(svc.preview(db, batch))
    except svc.BatchPurgeError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/{bid}/purge")
def purge_batch_data(bid: int, body: PurgeBody, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Xóa dữ liệu của lô nhập (định mức kèm thành phần / báo giá / dòng sổ Misa kèm tính lại mốc Misa).

    `include_edited=false` (mặc định) giữ lại dòng đã sửa tay sau khi nhập. Ghi nhật ký thao tác. Quyền như bước xem trước.
    """
    batch = _load_batch(db, user, bid)
    try:
        res = svc.purge(db, batch, user.id, include_edited=body.include_edited)
    except svc.BatchPurgeError as e:
        raise HTTPException(400, str(e)) from e
    return success(res, res["message"])
