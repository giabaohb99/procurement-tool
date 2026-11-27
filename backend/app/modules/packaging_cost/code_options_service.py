"""duoc-CR-784 — tên nhà cung cấp theo mã cho ô chọn mã (27/11/2026): gõ tên NCC vào ô là ra các mã từng mua của NCC đó.

Hai câu SQL cố định, không theo số mã: một câu lấy các cặp (mã, mã NCC, tên NCC chép theo dòng) khác nhau trong sổ giá có giá,
một câu tra tên của các mã NCC trong danh mục. Dòng Misa mang sẵn tên (mã Misa không nằm trong `tab_supplier`).
"""
from sqlalchemy.orm import Session

from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.supplier.model import Supplier

#  Đủ để tìm, không phình gói trả về: mã mua của rất nhiều NCC chỉ giữ chừng này tên.
MAX_NAMES_PER_CODE = 20


def supplier_names_by_code(db: Session, scope_cond=None) -> dict[str, str]:
    """`{mã: "tên NCC 1 · tên NCC 2 …"}` của mọi mã có lần mua có giá trong phạm vi người xem (pháp nhân)."""
    query = db.query(L.product_code, L.supplier_code, L.supplier_name).filter(L.price > 0)
    if scope_cond is not None:
        query = query.filter(scope_cond)
    pairs = query.distinct().all()
    supplier_codes = {sc for _, sc, _ in pairs if sc}
    names = dict(db.query(Supplier.code, Supplier.name).filter(Supplier.code.in_(supplier_codes or {""})).all())
    by_code: dict[str, list[str]] = {}
    for code, supplier_code, row_name in pairs:
        name = (row_name or names.get(supplier_code) or supplier_code or "").strip()
        bucket = by_code.setdefault(code, [])
        if name and name not in bucket and len(bucket) < MAX_NAMES_PER_CODE:
            bucket.append(name)
    return {code: " · ".join(sorted(items)) for code, items in by_code.items() if items}
