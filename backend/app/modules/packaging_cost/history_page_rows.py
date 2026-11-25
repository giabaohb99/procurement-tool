"""Trang dòng của Lịch sử mua hàng (duoc-CR-784): xếp theo đúng giá trị đang hiện, lấy khóa các dòng của trang rồi mới tính chi tiết.

Tách khỏi `history_service.py` (số gộp + ô chọn). HAI BƯỚC cố ý: MySQL tính hết cột chọn (kể cả hai truy vấn con tương quan "lần" và
"giá liền trước") cho MỌI dòng đã nối trước khi xếp + cắt trang — ở chế độ sản phẩm là hơn 55 nghìn dòng (đo 3,2 s trên 11,6 nghìn dòng
sổ x 1.000 định mức). Bước 1 chỉ lấy khóa (id sổ giá + sản phẩm / thành phần) của trang, bước 2 tính chi tiết đúng các dòng đó.
"""
from sqlalchemy import and_, case, func, inspect, select, tuple_
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql.util import ClauseAdapter

from app.core.packaging_price_codes import LedgerLineStage, PriceSourceType, is_open_po_line
from app.core.sort_order import build_blank_last_order
from app.modules.product.model import Product
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.supplier.model import Supplier

from .last_prices_service import supplier_label
from .numbers import iso, num

#  Ba khóa cuối chỉ có ở chế độ sản phẩm (cột Mã SP / Tên sản phẩm / Thành phần); chế độ mã gặp chúng thì rơi về `date` giảm.
PRODUCT_SORT_KEYS = ("hh_code", "hh_name", "role")
SORT_KEYS = ("date", "code", "name", "supplier", "warehouse", "qty", "price", "amount", "vat", "source", *PRODUCT_SORT_KEYS)
#  Giá trị mua hiện ra: thành tiền Misa khi có, không thì giá x SL; dòng đơn giá 0 không có giá trị (NULL, xuống cuối khi xếp).
AMOUNT_EXPR = case((L.price > 0, func.coalesce(L.amount, L.price * L.qty)))
#  Khóa xếp "Nguồn" theo ĐÚNG nhãn đang hiện (`price_source_text`): 1 Lịch sử mua hàng (lần mua đã chốt của ERP + dữ liệu cũ) < 2 Dòng đơn
#  mua hàng (ĐMH đang mở) < 3 Sổ Misa — cùng thứ tự bản cũ khi nguồn 1 / 2 còn tách theo `source_type`.
SOURCE_RANK_EXPR = case((L.source_type == int(PriceSourceType.MISA), 3),
                        ((L.source_type == int(PriceSourceType.PO_LINE)) & (L.line_stage == int(LedgerLineStage.OPEN)), 2), else_=1)


def supplier_name_expr():
    """Tên nhà cung cấp hiện ra: tên chép theo dòng sổ (nguồn Misa) thắng, rồi tên ở `tab_supplier`; trống thì None."""
    return func.coalesce(func.nullif(func.trim(L.supplier_name), ""), Supplier.name)


def retarget(alias, cond):
    """Chuyển điều kiện phạm vi dựng trên `ProductPriceLedger` sang bí danh của nó (hai truy vấn con)."""
    return ClauseAdapter(inspect(alias).selectable).traverse(cond)


def join_pairs(query, pairs):
    """Nối sổ giá với truy vấn con theo mã (cặp hoặc số cặp) khi ở chế độ sản phẩm; chế độ mã giữ nguyên truy vấn."""
    return query if pairs is None else query.join(pairs, pairs.c.code == L.product_code)


def build_order(sort_by: str, sort_dir: str, pairs=None) -> list:
    """ORDER BY theo ĐÚNG giá trị đang hiện; ô trống xuống cuối, khóa phụ cố định (luật §8).

    Chế độ sản phẩm: một dòng sổ giá hiện ở nhiều sản phẩm nên khóa phụ là (mã sản phẩm, thành phần, id) — `id` một mình không
    phân biệt các dòng cùng lần mua. Mặc định ngày -> mã sản phẩm -> thành phần như bản mẫu.
    """
    product = pairs is not None
    if sort_by not in SORT_KEYS or (sort_by in PRODUCT_SORT_KEYS and not product):
        sort_by, sort_dir = "date", "desc"
    desc = sort_dir == "desc"
    tail = [pairs.c.hh_code.asc(), pairs.c.role.asc()] if product else []
    if sort_by == "date":      # cùng thứ tự "lần mua gần nhất" của `price_state_service`: ngày, doc_id, id
        day = [L.price_date.desc() if desc else L.price_date.asc()]
        rest = [(c.desc() if desc else c.asc()) for c in (L.doc_id, L.id)]
        return day + tail + rest
    supplier_name = func.coalesce(func.nullif(func.trim(L.supplier_name), ""), func.nullif(func.trim(Supplier.name), ""),
                                  L.supplier_code)
    columns = {"code": (L.product_code, True), "name": (Product.name, True), "supplier": (supplier_name, True),
               "warehouse": (func.nullif(func.trim(L.warehouse_name), ""), True),
               "qty": (L.qty, False), "price": (L.price, False), "amount": (AMOUNT_EXPR, False),
               "vat": (L.vat, False), "source": (SOURCE_RANK_EXPR, False)}
    if product:
        columns |= {"hh_code": (pairs.c.hh_code, True), "hh_name": (pairs.c.hh_name, True), "role": (pairs.c.role, False)}
    expr, is_text = columns[sort_by]
    return [*build_blank_last_order(expr, sort_dir, is_text=is_text), *tail, L.id.desc()]


def _after(alias):
    """Lần mua của `alias` đứng SAU dòng ngoài (ngày, doc_id, id lớn hơn) — mới hơn nó."""
    return and_(alias.product_code == L.product_code,
                tuple_(alias.price_date, alias.doc_id, alias.id) > tuple_(L.price_date, L.doc_id, L.id))


def _before(alias):
    """Lần mua của `alias` đứng TRƯỚC dòng ngoài (ngày, doc_id, id nhỏ hơn)."""
    return and_(alias.product_code == L.product_code,
                tuple_(alias.price_date, alias.doc_id, alias.id) < tuple_(L.price_date, L.doc_id, L.id))


def _load_page_keys(db: Session, conds: list, order: list, limit: int, offset: int, pairs, with_names: bool) -> list:
    """Bước 1 của trang dòng: CHỈ khóa của các dòng thuộc trang, đã lọc + xếp (id sổ giá, kèm sản phẩm / thành phần ở chế độ sản phẩm).

    Cố ý tách khỏi bước 2: MySQL tính hết cột chọn (kể cả các truy vấn con tương quan lần / giá liền trước) cho MỌI dòng đã nối
    TRƯỚC khi xếp + cắt trang — hơn 55 nghìn dòng x hai truy vấn con ở chế độ sản phẩm. Tách ra thì chúng chỉ chạy cho dòng của trang.
    `with_names`: chỉ nối tên vật tư / nhà cung cấp khi khóa xếp cần.
    """
    cols = [L.id] + ([pairs.c.hh_code, pairs.c.hh_name, pairs.c.role] if pairs is not None else [])
    query = join_pairs(select(*cols).select_from(L), pairs)
    if with_names:
        query = query.outerjoin(Product, Product.code == L.product_code).outerjoin(Supplier, Supplier.code == L.supplier_code)
    return db.execute(query.where(*conds).order_by(*order).limit(limit).offset(offset)).all()


def _load_page_details(db: Session, ids: list[int], scope_cond) -> dict:
    """Bước 2: chi tiết các dòng sổ giá của trang (theo id) — nối tên / nhà cung cấp / số ĐMH, giá lần có giá liền trước và lần mua."""
    prev, newer = aliased(L), aliased(L)
    scope_prev = [retarget(prev, scope_cond)] if scope_cond is not None else []
    scope_new = [retarget(newer, scope_cond)] if scope_cond is not None else []
    prev_price = (select(prev.price).where(_before(prev), prev.price > 0, *scope_prev)
                  .order_by(prev.price_date.desc(), prev.doc_id.desc(), prev.id.desc()).limit(1).scalar_subquery())
    #  Lần = số lần mua MỚI HƠN của cùng mã + 1: lần gần nhất là lần 1 (bản mẫu HTML), không phụ thuộc bộ lọc.
    seq = select(func.count(newer.id)).where(_after(newer), *scope_new).scalar_subquery()
    query = (select(L.id, L.price_date, L.product_code, L.supplier_code, L.qty, L.unit, L.price, L.vat, L.source_type, L.line_stage,
                    L.doc_id, Product.name, Product.item_group, supplier_name_expr(), L.warehouse_name,
                    PurchaseOrder.code, prev_price, seq, AMOUNT_EXPR).select_from(L)
             .outerjoin(Product, Product.code == L.product_code).outerjoin(Supplier, Supplier.code == L.supplier_code)
             .outerjoin(PurchaseOrder, PurchaseOrder.id == L.doc_id).where(L.id.in_(ids)))
    return {r[0]: r for r in db.execute(query).all()}


def load_page_rows(db: Session, conds: list, order: list, scope_cond, limit: int, offset: int, pairs=None,
               with_names: bool = False) -> list:
    """Các dòng của trang theo thứ tự `order`, mỗi dòng ghép đủ cột cho `row_to_item` (chế độ mã: sản phẩm / thành phần trống)."""
    keys = _load_page_keys(db, conds, order, limit, offset, pairs, with_names)
    if not keys:
        return []
    details = _load_page_details(db, list({k[0] for k in keys}), scope_cond)
    return [(*details[k[0]], *(k[1:] if pairs is not None else ("", "", None))) for k in keys]


def row_to_item(r) -> dict:
    (row_id, day, code, supplier_code, qty, unit, price, vat, source_type, line_stage, doc_id, name, group, supplier, warehouse,
     po_code, prev_price, ordinal, amount, hh_code, hh_name, role) = r
    diff = float(price) - float(prev_price) if price and prev_price is not None else None
    return {"id": row_id, "date": iso(day), "code": code, "name": name or "", "group": group or "",
            "supplier_code": supplier_code, "supplier": supplier_label(supplier, supplier_code) if supplier_code else "",
            "warehouse": (warehouse or "").strip(), "qty": num(qty, 3), "unit": unit or "", "price": num(price),
            "vat": num(vat, 2),
            "amount": num(amount, 2), "source_type": int(source_type), "line_stage": int(line_stage),
            #  Cờ "ĐMH đang mở" cho giao diện (v1 + v2 + bản in): dòng ĐMH chưa hoàn thành, giá còn có thể đổi.
            "is_open": is_open_po_line(source_type, line_stage), "doc_id": int(doc_id or 0),
            "po_code": po_code or "", "prev_price": num(prev_price), "diff": num(diff, 4),
            "pct": num(diff / float(prev_price), 6) if diff is not None and prev_price else None,
            "seq": int(ordinal or 0) + 1,
            #  Chế độ sản phẩm: sản phẩm + thành phần của dòng (chế độ mã: "" / None).
            "hh_code": hh_code or "", "hh_name": hh_name or "", "role": int(role) if role else None}
