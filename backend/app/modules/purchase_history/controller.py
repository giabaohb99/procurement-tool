"""Lịch sử mua hàng — 2 route (theo SP / theo NCC) dùng chung 1 service.

Tách 2 route để quyền đúng ngữ nghĩa: xem lịch sử ở màn Sản phẩm cần `product.read`,
ở màn NCC cần `supplier.read`. Không áp `apply_scope` — mọi user có quyền đọc đều thấy
toàn bộ lịch sử (đã chốt trong thiết kế: dữ liệu tham chiếu giá nội bộ).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require, user_has_permission
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import PurchaseHistoryOut

router = APIRouter(tags=["purchase_history"])


def _payload(total: int, items, hien_ncc: bool = True) -> dict:
    """`hien_ncc=False` -> xóa tên/mã NCC khỏi payload (người xem không có quyền supplier.read)."""
    rows = [PurchaseHistoryOut.model_validate(i).model_dump() for i in items]
    if not hien_ncc:
        for r in rows:
            r["supplier_code"] = ""
            r["supplier_name"] = ""
    return {"total": total, "items": rows}


@router.get("/api/products/{code}/purchase-history")
def product_purchase_history(
    code: str,
    search: str = Query("", description="Tìm gần đúng theo Mã PO / NCC / Tên SP / Công ty"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("product", "read")),
):
    # Màn này chỉ đòi `product.read` (người YÊU CẦU cũng vào được để tham chiếu giá cũ),
    # nhưng NCC là thông tin riêng của khối thu mua -> ai không có `supplier.read` thì
    # không được thấy. Chặn ở BACKEND chứ không chỉ ẩn cột: ẩn ở giao diện thì gọi thẳng
    # API vẫn đọc được nguyên tên NCC.
    hien_ncc = user_has_permission(db, user, "supplier", "read")
    total, items = service.list_history(db, pg, product_code=code, search=search,
                                        tim_theo_ncc=hien_ncc)
    return success(_payload(total, items, hien_ncc))


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
