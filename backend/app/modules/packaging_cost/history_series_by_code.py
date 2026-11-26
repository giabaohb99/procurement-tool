"""Biểu đồ giá của Lịch sử mua hàng chế độ "Theo mã sản phẩm" khi chọn ĐÚNG MỘT sản phẩm (duoc-CR-784, 26/11/2026): mỗi mã thành
phần của định mức (chai, nắp, nhãn, nhãn thùng, thùng — mã nào có lần mua CÓ GIÁ) một đường giá cũ -> mới.

Đúng MỘT truy vấn cho mọi mã thành phần: hàm cửa sổ `row_number()` chia theo mã cắt ở `cap` điểm GẦN NHẤT của từng mã (cùng trần
với biểu đồ một mã `series`), nên số truy vấn không phụ thuộc số mã. Điều kiện lọc là điều kiện của chính trang dòng (chữ tìm,
nhà cung cấp, khoảng ngày, phạm vi pháp nhân + mốc sổ Misa) — biểu đồ khớp bảng bên dưới. Một dòng sổ giá nối được nhiều cặp (cùng mã
ở hai vai trò / hai tên sản phẩm) chỉ ra MỘT điểm, vai trò nhỏ nhất thắng (như bảng) — gom ở truy vấn con theo id dòng sổ giá.
"""
from sqlalchemy import Subquery, func, select
from sqlalchemy.orm import Session

from app.modules.product.model import Product
from app.modules.product_price.model import ProductPriceLedger as L

from .history_page_rows import join_pairs
from .numbers import iso, num


def build_series_by_code(db: Session, pairs: Subquery, conds: list, cap: int) -> list[dict]:
    """`[{code, name, role, points: [{date, price}]}]` xếp theo vai trò (chai -> thùng) rồi mã; điểm cũ -> mới.

    `conds` = điều kiện lọc dựng với `pairs=` (chế độ sản phẩm); chỉ lấy lần mua giá > 0. Không có điểm nào thì danh sách rỗng.
    """
    hits = (join_pairs(select(L.id.label("ledger_id"), func.min(pairs.c.role).label("role")).select_from(L), pairs)
            .where(*conds, L.price > 0).group_by(L.id).subquery())
    ranked = (select(L.product_code.label("code"), L.price_date.label("day"), L.price.label("price"), hits.c.role.label("role"),
                     func.row_number().over(partition_by=L.product_code,
                                            order_by=[L.price_date.desc(), L.doc_id.desc(), L.id.desc()]).label("rn"))
              .select_from(L).join(hits, hits.c.ledger_id == L.id).subquery())
    rows = db.execute(select(ranked.c.code, Product.name, ranked.c.role, ranked.c.day, ranked.c.price)
                      .select_from(ranked).outerjoin(Product, Product.code == ranked.c.code).where(ranked.c.rn <= cap)
                      .order_by(ranked.c.role, ranked.c.code, ranked.c.day, ranked.c.rn.desc())).all()
    series: dict[str, dict] = {}
    for code, name, role, day, price in rows:
        entry = series.setdefault(code, {"code": code, "name": name or "", "role": int(role), "points": []})
        entry["points"].append({"date": iso(day), "price": num(price)})
    return list(series.values())
