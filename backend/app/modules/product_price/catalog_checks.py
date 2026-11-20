"""Chốt chặn dữ liệu chung của báo giá / ngưỡng giá / định mức bao bì (duoc-CR-784): mã phải có trong danh mục.

Trả 422 kèm câu tiếng Việt (không phải 500 / 400 chung chung). Mỗi hàm gom MỘT truy vấn cho cả danh sách mã.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.product.model import Product
from app.modules.supplier.model import Supplier


def known_product_codes(db: Session, codes) -> set[str]:
    wanted = {c for c in (codes or []) if c}
    if not wanted:
        return set()
    return {r[0] for r in db.query(Product.code).filter(Product.code.in_(wanted)).all()}


def ensure_products_exist(db: Session, codes, label: str = "Mã sản phẩm") -> None:
    """Mọi mã (bỏ mã rỗng) phải có trong `tab_product`; thiếu thì 422 liệt kê mã thiếu."""
    wanted = sorted({c for c in (codes or []) if c})
    known = known_product_codes(db, wanted)     # MỘT truy vấn cho cả danh sách
    missing = [c for c in wanted if c not in known]
    if missing:
        raise HTTPException(422, f"{label} không có trong danh mục sản phẩm: {', '.join(missing[:10])}")


def ensure_supplier_ok(db: Session, supplier_code: str | None) -> None:
    """Mã NCC rỗng được; có thì phải có trong `tab_supplier`."""
    code = (supplier_code or "").strip()
    if code and db.query(Supplier.id).filter(Supplier.code == code).first() is None:
        raise HTTPException(422, f"Mã nhà cung cấp không có trong danh mục: {code}")


def reject_null(values: dict, keys: tuple[str, ...]) -> None:
    """Cột bắt buộc gửi `null` lên khi sửa → 422 (không để MySQL báo NOT NULL thành 500)."""
    bad = [k for k in keys if k in values and values[k] is None]
    if bad:
        raise HTTPException(422, f"Không được để trống: {', '.join(bad)}")


def product_info(db: Session, codes) -> dict[str, tuple[str, str]]:
    """`{mã: (tên, ĐVT)}` của các mã có trong danh mục — một truy vấn cho cả trang."""
    wanted = {c for c in (codes or []) if c}
    if not wanted:
        return {}
    return {c: (n or "", u or "") for c, n, u in
            db.query(Product.code, Product.name, Product.unit).filter(Product.code.in_(wanted)).all()}
