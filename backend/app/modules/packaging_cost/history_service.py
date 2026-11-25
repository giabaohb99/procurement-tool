"""Lịch sử mua hàng của cụm Giá bao bì: từng lần mua của một / nhiều mã VTBB, hoặc của các thành phần trong định mức
của một / nhiều sản phẩm (duoc-CR-784, tab "Lịch sử mua hàng" của bản mẫu `histRows` + `renderLast5` + `renderHistBySP`).

Đọc THẲNG sổ giá `tab_product_price_ledger` (dòng ĐMH đang mở + đã chốt, lịch sử cũ, sổ Misa; trường `is_open` /
`line_stage` để giao diện đánh dấu "ĐMH đang mở"). Lịch sử là bản chụp bất biến — không có đường sửa giá ở đây.

Số truy vấn CỐ ĐỊNH (tối đa 5) bất kể số mã / số dòng / bộ lọc:
  1. số gộp trên TOÀN BỘ tập đã lọc (số lần mua, tổng SL, tổng giá trị, giá bình quân gia quyền, min / max, số NCC, khoảng ngày);
  2. nhà cung cấp có trong phạm vi mã (cho ô chọn, chưa áp `q` / nhà cung cấp);
  3. khóa các dòng của trang: đã lọc + xếp + cắt trang, chỉ id sổ giá (kèm sản phẩm / thành phần ở chế độ sản phẩm);
  4. chi tiết đúng các dòng đó (`history_page_rows.py`): nối tên sản phẩm / nhà cung cấp / số ĐMH, kèm giá của lần mua có giá liền
     trước và số thứ tự lần mua (hai truy vấn con tương quan chạy trên chỉ mục phủ `ix_ppl_code_latest`, chỉ cho dòng của trang);
  5. (đúng một mã) các điểm giá cho biểu đồ, tối đa SERIES_CAP điểm gần nhất.
CHẾ ĐỘ SẢN PHẨM (`history_product_pairs.py`): mỗi dòng = một lần mua x một cặp (sản phẩm, mã thành phần của định mức), nối thẳng
trong SQL (một lần mua của mã dùng ở 275 sản phẩm = 275 dòng, như bản mẫu), xếp mặc định ngày -> mã sản phẩm -> thành phần; không có
biểu đồ. Số truy vấn vẫn như trên (cặp là truy vấn con, không thêm truy vấn). SỐ GỘP + ô chọn nhà cung cấp KHÔNG nối ra hàng chục
nghìn dòng đã nhân: cộng có trọng số theo số cặp của từng mã (`history_product_pairs.build_pair_counts`) — cùng kết quả, đọc ~1/5 số dòng.

LẦN (`seq`): thứ tự lần mua của mã trên TOÀN BỘ lịch sử trong phạm vi pháp nhân (không phụ thuộc bộ lọc), 1 = lần mua GẦN NHẤT
(bản mẫu `lan: i + 1` trên danh sách mới -> cũ). GIÁ TRỊ MUA (`amount`) = thành tiền Misa khi có (`ledger.amount`), không thì giá x số
lượng; dòng đơn giá 0 không có giá trị (None). Tổng giá trị + giá bình quân gia quyền cộng đúng giá trị này.
Phạm vi pháp nhân (`scope_cond`) áp cho MỌI truy vấn kể cả hai truy vấn con; mốc sổ Misa (`product_price/misa_cutoff.py`) gộp
vào cùng điều kiện đó — không thêm truy vấn (truy vấn con vô hướng đọc `tab_setting` nằm trong WHERE). Tên nhà cung cấp: tên chép
theo dòng sổ (`supplier_name`, nguồn Misa) thắng tên ở `tab_supplier`. Kho (`warehouse_name`) chép theo dòng sổ, tìm được
bằng `q`, xếp được (`sort_by=warehouse`). Giá 0 vẫn hiện trong bảng (cờ qua `price == 0`)
nhưng không tính vào giá bình quân / min / max / biểu đồ. Lọc + xếp + phân trang tại máy chủ (luật §8).
"""
from datetime import date

from sqlalchemy import case, func, literal, null, or_, select, union
from sqlalchemy.orm import Session

from app.core.export_xlsx import MAX_ROWS
from app.modules.product.model import Product
from app.modules.product_price.misa_cutoff import with_misa_cutoff
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.product_price.model import ProductPriceQuote
from app.modules.supplier.model import Supplier

from .cost_service import fold_text
from .history_page_rows import (  # noqa: F401  (SORT_KEYS: nơi khác import từ đây)
    AMOUNT_EXPR, PRODUCT_SORT_KEYS, SORT_KEYS, build_order, join_pairs, load_page_rows, row_to_item, supplier_name_expr)
from .history_product_pairs import build_bom_pairs, build_pair_counts, count_bom_products, pair_text_conds
from .last_prices_service import supplier_label
from .bom_parts_service import component_codes_query
from .numbers import iso, num

MAX_CODES = 200
SERIES_CAP = 1000


def _universe_codes():
    """Mọi mã VTBB của cụm giá: thành phần của định mức ∪ mã có báo giá (cùng tập với "Giá mua gần nhất" phạm vi bom)."""
    return union(component_codes_query(), select(ProductPriceQuote.product_code))


def _ledger_text_match(needle: str) -> list:
    """Điều kiện tìm chữ ở cấp DÒNG SỔ GIÁ: mã, tên vật tư, mã / tên nhà cung cấp, tên kho (LIKE có thoát ký tự đặc biệt)."""
    return [L.product_code.contains(needle, autoescape=True), L.supplier_code.contains(needle, autoescape=True),
            L.product_code.in_(select(Product.code).where(Product.name.contains(needle, autoescape=True))),
            L.supplier_name.contains(needle, autoescape=True), L.warehouse_name.contains(needle, autoescape=True),
            L.supplier_code.in_(select(Supplier.code).where(Supplier.name.contains(needle, autoescape=True)))]


def _conds(codes: list[str] | None, *, q: str = "", suppliers: list[str] | None = None, date_from: date | None = None,
           date_to: date | None = None, scope_cond=None, skip_text_filters: bool = False, pairs=None, counts=None) -> list:
    """Điều kiện lọc sổ giá. `codes=None` = toàn bộ mã VTBB. `skip_text_filters` bỏ `q` + nhà cung cấp (ô chọn nhà cung cấp).
    Chế độ sản phẩm: `pairs` (trang dòng, nối từng cặp) hoặc `counts` (số gộp, nối số cặp mỗi mã — `build_pair_counts`); tập mã đã bị
    phép nối giới hạn nên không thêm điều kiện mã. Chữ tìm khớp ở cấp cặp thì `counts.c.m > 0` (có ít nhất một cặp khớp)."""
    conds = ([] if pairs is not None or counts is not None
             else [L.product_code.in_(codes) if codes is not None else L.product_code.in_(_universe_codes())])
    if date_from is not None:
        conds.append(L.price_date >= date_from)
    if date_to is not None:
        conds.append(L.price_date <= date_to)
    if scope_cond is not None:
        conds.append(scope_cond)
    if not skip_text_filters:
        if q.strip():
            needle = q.strip()
            pair_level = (pair_text_conds(pairs, needle) if pairs is not None
                          else [counts.c.m > 0] if counts is not None else [])
            conds.append(or_(*pair_level, *_ledger_text_match(needle)))
        wanted = [s for s in (suppliers or []) if s]
        if wanted:
            conds.append(L.supplier_code.in_(wanted))
    return conds


def _edge_price(conds: list, *, latest: bool):
    """Giá của lần mua CÓ GIÁ đầu tiên / gần nhất trong tập lọc (cùng thứ tự ngày, doc_id, id của danh sách).

    `correlate(None)`: câu con đứng riêng, không bị SQLAlchemy nối vào bảng sổ giá của câu ngoài (cùng bảng `L`).
    """
    order = [L.price_date, L.doc_id, L.id]
    return (select(L.price).where(*conds, L.price > 0)
            .order_by(*[c.desc() if latest else c.asc() for c in order]).limit(1).correlate(None).scalar_subquery())

def _weight(counts, q: str):
    """Trọng số của một dòng sổ giá khi nối `counts`: số dòng đã nhân theo sản phẩm. Dòng khớp chữ tìm ở cấp sổ giá hiện ở MỌI cặp
    (`n`), còn không thì chỉ ở các cặp khớp (`m`). Chế độ mã không có trọng số (None)."""
    if counts is None:
        return None
    if not q.strip():
        return counts.c.n
    return case((or_(*_ledger_text_match(q.strip())), counts.c.n), else_=counts.c.m)


def _stats(db: Session, conds: list, counts=None, weight=None, fg_codes: list[str] | None = None) -> dict:
    """Số liệu của các thẻ tóm tắt, gom trong MỘT câu SQL (thẻ của bản mẫu HTML, duoc-CR-784).

    Chế độ sản phẩm (`counts` + `weight`): mọi số đếm / tổng theo DÒNG đã nhân theo sản phẩm (đúng "Số dòng lịch sử" của bản mẫu) —
    tính bằng cách cộng có trọng số trên dòng sổ giá thay vì nối ra hàng chục nghìn dòng; giá đầu / cuối không có nghĩa khi trộn
    nhiều mã nên để trống; thêm `product_count` = số sản phẩm có định mức trong phạm vi chọn.
    """
    product = counts is not None
    priced = L.price > 0

    def total(expr):                                    # tổng có trọng số (chế độ mã: tổng thường)
        return func.sum(expr * weight if product else expr)

    first_price = null() if product else _edge_price(conds, latest=False)
    last_price = null() if product else _edge_price(conds, latest=True)
    products = count_bom_products(fg_codes or []) if product else literal(0)
    query = select(
        func.sum(weight) if product else func.count(L.id), func.coalesce(total(case((priced, 1), else_=0)), 0),
        func.coalesce(total(L.qty), 0), func.coalesce(total(AMOUNT_EXPR), 0),
        func.coalesce(total(case((priced, L.qty), else_=0)), 0),
        func.min(case((priced, L.price))), func.max(case((priced, L.price))),
        func.count(func.distinct(case((L.supplier_code != "", L.supplier_code)))),
        func.min(L.price_date), func.max(L.price_date), func.count(func.distinct(L.product_code)),
        func.max(func.nullif(func.trim(L.unit), "")), first_price, last_price, products).select_from(L)
    row = db.execute(join_pairs(query, counts).where(*conds)).one()
    (count, priced_count, qty_total, amount_priced, qty_priced, low, high, supplier_count, first, last, code_count,
     unit, first_price, last_price, product_count) = row
    count = count or 0
    #  Giá bình quân GIA QUYỀN = tổng giá trị / tổng số lượng của các lần mua CÓ GIÁ; chưa có số lượng thì không có số.
    weighted = float(amount_priced) / float(qty_priced) if qty_priced and float(qty_priced) > 0 else None
    return {"purchase_count": int(count), "priced_count": int(priced_count), "qty_total": num(qty_total, 3),
            "weighted_avg": num(weighted), "min": num(low), "max": num(high), "supplier_count": int(supplier_count),
            "first_date": iso(first), "last_date": iso(last),
            #  Tổng giá trị mua = cộng giá trị (thành tiền Misa, không thì giá x SL) của các lần CÓ GIÁ, như bản mẫu HTML.
            "amount_total": num(amount_priced), "code_count": int(code_count or 0),
            "unit": unit if count else "", "first_price": num(first_price), "last_price": num(last_price),
            "product_count": int(product_count or 0)}


def _supplier_options(db: Session, conds: list, counts=None) -> list[dict]:
    query = (select(L.supplier_code, func.max(supplier_name_expr())).select_from(L)
             .outerjoin(Supplier, Supplier.code == L.supplier_code))
    rows = db.execute(join_pairs(query, counts).where(*conds, L.supplier_code != "").group_by(L.supplier_code)).all()
    options = [{"code": code, "name": supplier_label(name, code)} for code, name in rows]
    return sorted(options, key=lambda o: (fold_text(o["name"]), o["code"]))

def _series(db: Session, conds: list) -> list[dict]:
    """Các điểm giá (chỉ lần mua CÓ GIÁ) cũ -> mới, tối đa SERIES_CAP điểm gần nhất."""
    rows = db.execute(select(L.price_date, L.price, L.supplier_code, L.qty, supplier_name_expr()).select_from(L)
                      .outerjoin(Supplier, Supplier.code == L.supplier_code).where(*conds, L.price > 0)
                      .order_by(L.price_date.desc(), L.doc_id.desc(), L.id.desc()).limit(SERIES_CAP)).all()
    return [{"date": iso(d), "price": num(p), "supplier_code": s, "supplier": supplier_label(n, s) if s else "",
             "qty": num(q, 3)} for d, p, s, q, n in reversed(rows)]


def build_history(db: Session, *, mode: str = "code", codes: list[str] | None = None, fg_codes: list[str] | None = None,
                  q: str = "", suppliers: list[str] | None = None, date_from: date | None = None,
                  date_to: date | None = None, sort_by: str = "date", sort_dir: str = "desc", page: int | None = 1,
                  page_size: int = 50, scope_cond=None) -> dict:
    """`{items, total, stats, series, suppliers}`. `page=None` = lấy đủ (xuất Excel; chặn ở MAX_ROWS + 1 dòng).

    `mode=code`: `codes` rỗng = mọi mã VTBB. `mode=product`: mã thành phần của các `fg_codes` (rỗng = mọi sản phẩm có
    định mức), mỗi dòng = một lần mua x một (sản phẩm, thành phần) kèm `fg_code` / `fg_name` / `role` (mã `PackagingRole`);
    sản phẩm chưa có định mức nào thì kết quả rỗng. `series` chỉ có ở chế độ mã khi tập mã đã chọn đúng MỘT mã (biểu đồ diễn
    biến đơn giá), ngược lại `None`.
    """
    scope_cond = with_misa_cutoff(scope_cond)      # mốc sổ Misa: dòng Misa tới mốc + nguồn 1 / 2 sau mốc (chưa có mốc = như cũ)
    product = mode == "product"
    fg_list = [c for c in (fg_codes or []) if c] if product else []
    pairs = build_bom_pairs(fg_list) if product else None
    #  Số gộp / ô chọn nhà cung cấp cộng có trọng số theo số cặp mỗi mã (không nối từng cặp); trang dòng mới nối từng cặp.
    counts = build_pair_counts(pairs, q.strip()) if product else None
    options_counts = build_pair_counts(pairs) if product else None
    explicit = None if product else [c for c in (codes or []) if c]
    text = {"q": q, "suppliers": suppliers, "date_from": date_from, "date_to": date_to, "scope_cond": scope_cond}
    conds = _conds(explicit or None, **text, counts=counts)
    stats = _stats(db, conds, counts, _weight(counts, q), fg_list)
    offset, limit = ((page - 1) * page_size, page_size) if page is not None else (0, MAX_ROWS + 1)
    order = build_order(sort_by, sort_dir, pairs)
    rows = (load_page_rows(db, _conds(explicit or None, **text, pairs=pairs), order, scope_cond, limit, offset, pairs,
                       with_names=sort_by in ("name", "supplier"))
            if stats["purchase_count"] else [])
    scope_conds = _conds(explicit or None, date_from=date_from, date_to=date_to, scope_cond=scope_cond,
                         skip_text_filters=True, counts=options_counts)
    return {"items": [row_to_item(r) for r in rows], "total": stats["purchase_count"], "stats": stats,
            "series": _series(db, conds) if explicit and len(explicit) == 1 and stats["priced_count"] else None,
            "suppliers": _supplier_options(db, scope_conds, options_counts)}

