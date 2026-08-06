"""Lịch sử mua hàng — 2 route (theo SP / theo NCC) dùng chung 1 service.

Tách 2 route để quyền đúng ngữ nghĩa: xem lịch sử ở màn Sản phẩm cần `product.read`,
ở màn NCC cần `supplier.read`. Không áp `apply_scope` — mọi user có quyền đọc đều thấy
toàn bộ lịch sử (đã chốt trong thiết kế: dữ liệu tham chiếu giá nội bộ).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import PurchaseHistoryOut

router = APIRouter(tags=["purchase_history"])


def _payload(total: int, items) -> dict:
    return {"total": total, "items": [PurchaseHistoryOut.model_validate(i).model_dump() for i in items]}


@router.get("/api/products/{code}/purchase-history")
def product_purchase_history(
    code: str,
    search: str = Query("", description="Tìm gần đúng theo Mã PO / NCC / Tên SP / Công ty"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("product", "read")),
):
    total, items = service.list_history(db, pg, product_code=code, search=search)
    return success(_payload(total, items))


@router.get("/api/suppliers/{code}/purchase-history")
def supplier_purchase_history(
    code: str,
    search: str = Query("", description="Tìm gần đúng theo Mã PO / NCC / Tên SP / Công ty"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("supplier", "read")),
):
    total, items = service.list_history(db, pg, supplier_code=code, search=search)
    return success(_payload(total, items))
