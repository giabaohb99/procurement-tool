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


def _attach_invoice_names(db: Session, rows: list[dict]) -> None:
    """Cột «Tên trên hóa đơn» của popup lịch sử (bao-CR-522).

    Lần mua đi qua ĐMH trên hệ chụp sẵn tên đó vào `extra.invoice_name`. Dòng DỮ LIỆU CŨ (nạp
    từ Excel, `source='legacy'`) không có cột này trong tệp gốc — lùi về tên trên hóa đơn đang khai
    ở DANH MỤC sản phẩm, gắn cờ `invoice_name_from_catalog` để giao diện ghi rõ là số danh mục
    chứ không phải tên đã xuất trên hóa đơn lần đó. MỘT truy vấn cho cả trang.
    """
    from app.modules.product.model import Product

    missing = {r["product_code"] for r in rows
               if not (r.get("extra") or {}).get("invoice_name") and r.get("product_code")}
    catalog = dict(db.query(Product.code, Product.invoice_name)
                   .filter(Product.code.in_(missing)).all()) if missing else {}
    for r in rows:
        own = ((r.get("extra") or {}).get("invoice_name") or "").strip()
        fallback = (catalog.get(r.get("product_code")) or "").strip()
        r["invoice_name"] = own or fallback
        r["invoice_name_from_catalog"] = bool(not own and fallback)


def _payload(db: Session, total: int, items, show_supplier: bool = True) -> dict:
    """`hien_ncc=False` -> xóa tên/mã NCC khỏi payload (người xem không có quyền supplier.read)."""
    rows = [PurchaseHistoryOut.model_validate(i).model_dump() for i in items]
    _attach_invoice_names(db, rows)
    if not show_supplier:
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
    show_supplier = user_has_permission(db, user, "supplier", "read")
    total, items = service.list_history(db, pg, product_code=code, search=search,
                                        search_by_supplier=show_supplier)
    return success(_payload(db, total, items, show_supplier))


@router.get("/api/suppliers/{code}/purchase-history")
def supplier_purchase_history(
    code: str,
    search: str = Query("", description="Tìm gần đúng theo Mã PO / NCC / Tên SP / Công ty"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("supplier", "read")),
):
    total, items = service.list_history(db, pg, supplier_code=code, search=search)
    return success(_payload(db, total, items))
