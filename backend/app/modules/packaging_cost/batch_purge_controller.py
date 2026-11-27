"""API xóa dữ liệu theo LÔ NHẬP của cụm Giá NVL sản xuất (duoc-CR-784, phase 07) — hai đường dưới `/api/imports/{id}`.

Gác KÉP: quyền xem Import (`import.read`) VÀ quyền xóa trên khóa của MÀN giữ dữ liệu của lô (bao-CR-792, 27/11/2026: mỗi màn
một khóa, thay khóa chung `packaging_cost`) — xem `DELETE_KEY_BY_MODULE`. Logic ở `batch_purge_service.py`.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, user_has_permission
from app.core.database import get_db
from app.core.response import success
from app.modules.import_tool import service as import_service
from app.modules.import_tool.model import ImportModule

from . import batch_purge_service as svc

router = APIRouter(prefix="/api/imports", tags=["import"])

#  Loại lô -> (khóa của màn giữ dữ liệu, tên màn trong câu 403).
DELETE_KEY_BY_MODULE = {
    int(ImportModule.PACKAGING_BOM): ("packaging_bom", "Định mức bao bì"),
    int(ImportModule.PACKAGING_QUOTE): ("packaging_price_list", "Bảng giá VTBB"),
    int(ImportModule.PACKAGING_MISA): ("packaging_history", "Lịch sử mua hàng"),
}


class PurgeBody(BaseModel):
    include_edited: bool = False       # true = xóa luôn dòng đã bị sửa tay sau khi nhập


def _load_batch(db: Session, user, bid: int):
    """Kiểm quyền rồi nạp lô. Quyền kiểm TRƯỚC khi tra lô để người không có quyền không dò được id nào tồn tại.

    Hai bước: chưa có quyền xóa trên khóa NÀO trong ba khóa thì 403 ngay (chưa tra lô); nạp lô xong mới kiểm ĐÚNG khóa theo
    loại lô. Lô không thuộc ba loại đi tiếp để `batch_purge_service` trả 400 như cũ.
    """
    if not user_has_permission(db, user, "import", "read"):
        raise HTTPException(403, "Không có quyền xem Import")
    if not any(user_has_permission(db, user, key, "delete") for key, _ in DELETE_KEY_BY_MODULE.values()):
        raise HTTPException(403, "Xóa dữ liệu theo lô cần quyền xóa ở Định mức bao bì, Bảng giá VTBB hoặc Lịch sử mua hàng")
    batch = import_service.get_batch(db, bid)
    if not batch:
        raise HTTPException(404, "Không tìm thấy lần import")
    key, screen = DELETE_KEY_BY_MODULE.get(int(batch.module), ("", ""))
    if key and not user_has_permission(db, user, key, "delete"):
        raise HTTPException(403, f"Xóa dữ liệu của lô này cần quyền xóa ở {screen}")
    return batch


@router.get("/{bid}/purge-preview")
def get_purge_preview(bid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Xem trước xóa theo lô: số dòng sẽ xóa, số dòng đã sửa tay sau khi nhập (tách riêng).

    Quyền: `import.read` + quyền xóa theo loại lô (`packaging_bom.delete` cho lô định mức, `packaging_price_list.delete` cho lô
    báo giá, `packaging_history.delete` cho lô Sổ Misa). Lỗi 400 nếu lô không phải Định mức / Báo giá / Sổ Misa, là bản chạy thử
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
