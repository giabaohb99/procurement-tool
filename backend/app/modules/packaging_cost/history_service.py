"""Lịch sử mua hàng của cụm Giá bao bì: từng lần mua của một / nhiều mã VTBB, hoặc của các thành phần trong định mức
của một / nhiều sản phẩm (duoc-CR-784, tab "Lịch sử mua hàng" của bản mẫu `histRows` + `renderLast5`).

Đọc THẲNG sổ giá `tab_product_price_ledger` (cả hai nguồn: lịch sử mua + dòng ĐMH đã duyệt chưa hoàn thành, trường
`source_type` để giao diện đánh dấu "ĐMH đang mở"). Lịch sử là bản chụp bất biến — không có đường sửa giá ở đây.

Số truy vấn CỐ ĐỊNH (tối đa 5) bất kể số mã / số dòng / bộ lọc:
  1. (chỉ chế độ sản phẩm) cột mã thành phần của định mức -> mã + vai trò;
  2. số gộp trên TOÀN BỘ tập đã lọc (số lần mua, tổng SL, giá bình quân gia quyền, min / max, số NCC, khoảng ngày);
  3. nhà cung cấp có trong phạm vi mã (cho ô chọn, chưa áp `q` / nhà cung cấp);
  4. trang dòng: nối tên sản phẩm / nhà cung cấp / số ĐMH, kèm giá của lần mua có giá liền trước và số thứ tự lần mua
     (hai truy vấn con tương quan chạy trên chỉ mục phủ `ix_ppl_code_latest`, chỉ cho các dòng của trang);
  5. (đúng một mã) các điểm giá cho biểu đồ, tối đa SERIES_CAP điểm gần nhất.
Phạm vi pháp nhân (`scope_cond`) áp cho MỌI truy vấn kể cả hai truy vấn con; mốc sổ Misa (`product_price/misa_cutoff.py`) gộp
vào cùng điều kiện đó — không thêm truy vấn (truy vấn con vô hướng đọc `tab_setting` nằm trong WHERE). Tên nhà cung cấp: tên chép
theo dòng sổ (`supplier_name`, nguồn Misa) thắng tên ở `tab_supplier`. Kho (`warehouse_name`) chép theo dòng sổ, tìm được
bằng `q`, xếp được (`sort_by=warehouse`). Giá 0 vẫn hiện trong bảng (cờ qua `price == 0`)
nhưng không tính vào giá bình quân / min / max / biểu đồ. Lọc + xếp + phân trang tại máy chủ (luật §8).
"""
from datetime import date

from sqlalchemy import and_, case, func, inspect, or_, select, tuple_, union
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql.util import ClauseAdapter

from app.core.export_xlsx import MAX_ROWS
from app.core.packaging_price_codes import PackagingRole
from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.modules.product.model import Product
from app.modules.product_price.misa_cutoff import with_misa_cutoff
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.product_price.model import ProductPriceQuote
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.supplier.model import Supplier

from .cost_service import fold_text
from .impact_service import PART_COLUMNS
from .last_prices_service import supplier_label
from .model import PackagingBom
from .numbers import iso, num

MAX_CODES = 200
SERIES_CAP = 1000
SORT_KEYS = ("date", "code", "name", "supplier", "warehouse", "qty", "price", "amount", "vat", "source")
_ROLES = list(PackagingRole)          # cùng thứ tự với PART_COLUMNS


def component_roles(db: Session, hh_codes: list[str]) -> dict[str, list[int]]:
    """`{mã thành phần: [vai trò]}` của các sản phẩm đã chọn (rỗng = mọi sản phẩm có định mức). MỘT truy vấn."""
    query = db.query(*[getattr(PackagingBom, c) for c in PART_COLUMNS])
    if hh_codes:
        query = query.filter(PackagingBom.hh_code.in_(hh_codes))
    roles: dict[str, set[int]] = {}
    for row in query.all():
        for role, code in zip(_ROLES, row):
            if code:
                roles.setdefault(code, set()).add(int(role))
    return {code: sorted(found) for code, found in roles.items()}


def _universe_codes():
    """Mọi mã VTBB của cụm giá: thành phần của định mức ∪ mã có báo giá (cùng tập với "Giá mua gần nhất" phạm vi bom)."""
    parts = [select(getattr(PackagingBom, c)).where(getattr(PackagingBom, c) != "") for c in PART_COLUMNS]
    return union(*parts, select(ProductPriceQuote.product_code))


def _supplier_name_expr():
    """Tên nhà cung cấp hiện ra: tên chép theo dòng sổ (nguồn Misa) thắng, rồi tên ở `tab_supplier`; trống thì None."""
    return func.coalesce(func.nullif(func.trim(L.supplier_name), ""), Supplier.name)


def _retarget(alias, cond):
    """Chuyển điều kiện phạm vi dựng trên `ProductPriceLedger` sang bí danh của nó (hai truy vấn con)."""
    return ClauseAdapter(inspect(alias).selectable).traverse(cond)


def _text_match(needle: str) -> list:
    """Điều kiện tìm chữ: mã, tên sản phẩm, mã / tên nhà cung cấp, tên kho (LIKE có thoát ký tự đặc biệt)."""
    return [L.product_code.contains(needle, autoescape=True), L.supplier_code.contains(needle, autoescape=True),
            L.product_code.in_(select(Product.code).where(Product.name.contains(needle, autoescape=True))),
            L.supplier_name.contains(needle, autoescape=True), L.warehouse_name.contains(needle, autoescape=True),
            L.supplier_code.in_(select(Supplier.code).where(Supplier.name.contains(needle, autoescape=True)))]


def _conds(codes: list[str] | None, *, q: str = "", suppliers: list[str] | None = None, date_from: date | None = None,
           date_to: date | None = None, scope_cond=None, skip_text_filters: bool = False) -> list:
    """Điều kiện lọc sổ giá. `codes=None` = toàn bộ mã VTBB. `skip_text_filters` bỏ `q` + nhà cung cấp (ô chọn nhà cung cấp)."""
    conds = [L.product_code.in_(codes) if codes is not None else L.product_code.in_(_universe_codes())]
    if date_from is not None:
        conds.append(L.price_date >= date_from)
    if date_to is not None:
        conds.append(L.price_date <= date_to)
    if scope_cond is not None:
        conds.append(scope_cond)
    if not skip_text_filters:
        if q.strip():
            conds.append(or_(*_text_match(q.strip())))
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


def _stats(db: Session, conds: list) -> dict:
    """Số liệu của các thẻ tóm tắt, gom trong MỘT câu SQL (thẻ của bản mẫu HTML, duoc-CR-784)."""
    priced = L.price > 0
    row = db.execute(select(
        func.count(L.id), func.coalesce(func.sum(case((priced, 1), else_=0)), 0), func.coalesce(func.sum(L.qty), 0),
        func.coalesce(func.sum(case((priced, L.price * L.qty), else_=0)), 0),
        func.coalesce(func.sum(case((priced, L.qty), else_=0)), 0),
        func.min(case((priced, L.price))), func.max(case((priced, L.price))),
        func.count(func.distinct(case((L.supplier_code != "", L.supplier_code)))),
        func.min(L.price_date), func.max(L.price_date), func.count(func.distinct(L.product_code)),
        func.max(func.nullif(func.trim(L.unit), "")),
        _edge_price(conds, latest=False), _edge_price(conds, latest=True)).where(*conds)).one()
    (count, priced_count, qty_total, amount_priced, qty_priced, low, high, supplier_count, first, last, code_count,
     unit, first_price, last_price) = row
    #  Giá bình quân GIA QUYỀN = tổng tiền / tổng số lượng của các lần mua CÓ GIÁ; chưa có số lượng thì không có số.
    weighted = float(amount_priced) / float(qty_priced) if qty_priced and float(qty_priced) > 0 else None
    return {"purchase_count": int(count), "priced_count": int(priced_count), "qty_total": num(qty_total, 3),
            "weighted_avg": num(weighted), "min": num(low), "max": num(high), "supplier_count": int(supplier_count),
            "first_date": iso(first), "last_date": iso(last),
            #  Tổng giá trị mua = cộng (giá x số lượng) của các lần CÓ GIÁ, như bản mẫu HTML.
            "amount_total": num(amount_priced), "code_count": int(code_count or 0),
            "unit": unit if count else "", "first_price": num(first_price), "last_price": num(last_price)}


def _supplier_options(db: Session, conds: list) -> list[dict]:
    rows = db.execute(select(L.supplier_code, func.max(_supplier_name_expr())).select_from(L)
                      .outerjoin(Supplier, Supplier.code == L.supplier_code)
                      .where(*conds, L.supplier_code != "").group_by(L.supplier_code)).all()
    options = [{"code": code, "name": supplier_label(name, code)} for code, name in rows]
    return sorted(options, key=lambda o: (fold_text(o["name"]), o["code"]))


def _order(sort_by: str, sort_dir: str) -> list:
    """ORDER BY theo ĐÚNG giá trị đang hiện; ô trống xuống cuối, khóa phụ `id` (luật §8)."""
    if sort_by not in SORT_KEYS:
        sort_by, sort_dir = "date", "desc"
    desc = sort_dir == "desc"
    if sort_by == "date":      # cùng thứ tự "lần mua gần nhất" của `price_state_service`: ngày, doc_id, id
        return [(c.desc() if desc else c.asc()) for c in (L.price_date, L.doc_id)] + [L.id.desc() if desc else L.id.asc()]
    supplier_name = func.coalesce(func.nullif(func.trim(L.supplier_name), ""), func.nullif(func.trim(Supplier.name), ""),
                                  L.supplier_code)
    expr, is_text = {"code": (L.product_code, True), "name": (Product.name, True), "supplier": (supplier_name, True),
                     "warehouse": (func.nullif(func.trim(L.warehouse_name), ""), True),
                     "qty": (L.qty, False), "price": (L.price, False), "amount": (L.price * L.qty, False),
                     "vat": (L.vat, False), "source": (L.source_type, False)}[sort_by]
    return with_stable_tiebreak(build_blank_last_order(expr, sort_dir, is_text=is_text), L.id)


def _before(alias):
    """Lần mua của `alias` đứng TRƯỚC dòng ngoài (ngày, doc_id, id nhỏ hơn)."""
    return and_(alias.product_code == L.product_code,
                tuple_(alias.price_date, alias.doc_id, alias.id) < tuple_(L.price_date, L.doc_id, L.id))


def _page_rows(db: Session, conds: list, order: list, scope_cond, limit: int, offset: int):
    prev, ordinal = aliased(L), aliased(L)
    scope_prev = [_retarget(prev, scope_cond)] if scope_cond is not None else []
    scope_ord = [_retarget(ordinal, scope_cond)] if scope_cond is not None else []
    prev_price = (select(prev.price).where(_before(prev), prev.price > 0, *scope_prev)
                  .order_by(prev.price_date.desc(), prev.doc_id.desc(), prev.id.desc()).limit(1).scalar_subquery())
    seq = select(func.count(ordinal.id)).where(_before(ordinal), *scope_ord).scalar_subquery()
    query = (select(L.id, L.price_date, L.product_code, L.supplier_code, L.qty, L.unit, L.price, L.vat, L.source_type,
                    L.doc_id, Product.name, Product.item_group, _supplier_name_expr(), L.warehouse_name,
                    PurchaseOrder.code, prev_price, seq)
             .select_from(L).outerjoin(Product, Product.code == L.product_code)
             .outerjoin(Supplier, Supplier.code == L.supplier_code).outerjoin(PurchaseOrder, PurchaseOrder.id == L.doc_id)
             .where(*conds).order_by(*order).limit(limit).offset(offset))
    return db.execute(query).all()


def _item(r, roles: dict[str, list[int]]) -> dict:
    (row_id, day, code, supplier_code, qty, unit, price, vat, source_type, doc_id, name, group, supplier, warehouse,
     po_code, prev_price, ordinal) = r
    diff = float(price) - float(prev_price) if price and prev_price is not None else None
    return {"id": row_id, "date": iso(day), "code": code, "name": name or "", "group": group or "",
            "supplier_code": supplier_code, "supplier": supplier_label(supplier, supplier_code) if supplier_code else "",
            "warehouse": (warehouse or "").strip(), "qty": num(qty, 3), "unit": unit or "", "price": num(price),
            "vat": num(vat, 2),
            "amount": num(price * qty), "source_type": int(source_type), "doc_id": int(doc_id or 0),
            "po_code": po_code or "", "prev_price": num(prev_price), "diff": num(diff, 4),
            "pct": num(diff / float(prev_price), 6) if diff is not None and prev_price else None,
            "seq": int(ordinal or 0) + 1, "roles": roles.get(code, [])}


def _series(db: Session, conds: list) -> list[dict]:
    """Các điểm giá (chỉ lần mua CÓ GIÁ) cũ -> mới, tối đa SERIES_CAP điểm gần nhất."""
    rows = db.execute(select(L.price_date, L.price, L.supplier_code, L.qty, _supplier_name_expr()).select_from(L)
                      .outerjoin(Supplier, Supplier.code == L.supplier_code).where(*conds, L.price > 0)
                      .order_by(L.price_date.desc(), L.doc_id.desc(), L.id.desc()).limit(SERIES_CAP)).all()
    return [{"date": iso(d), "price": num(p), "supplier_code": s, "supplier": supplier_label(n, s) if s else "",
             "qty": num(q, 3)} for d, p, s, q, n in reversed(rows)]


def _empty() -> dict:
    zero = {"purchase_count": 0, "priced_count": 0, "qty_total": 0, "weighted_avg": None, "min": None, "max": None,
            "supplier_count": 0, "first_date": None, "last_date": None, "amount_total": 0, "code_count": 0, "unit": "",
            "first_price": None, "last_price": None}
    return {"items": [], "total": 0, "stats": zero, "series": None, "suppliers": []}


def build_history(db: Session, *, mode: str = "code", codes: list[str] | None = None, hh_codes: list[str] | None = None,
                  q: str = "", suppliers: list[str] | None = None, date_from: date | None = None,
                  date_to: date | None = None, sort_by: str = "date", sort_dir: str = "desc", page: int | None = 1,
                  page_size: int = 50, scope_cond=None) -> dict:
    """`{items, total, stats, series, suppliers}`. `page=None` = lấy đủ (xuất Excel; chặn ở MAX_ROWS + 1 dòng).

    `mode=code`: `codes` rỗng = mọi mã VTBB. `mode=product`: mã thành phần của các `hh_codes` (rỗng = mọi sản phẩm có
    định mức), mỗi dòng kèm `roles` (mã `PackagingRole`); sản phẩm chưa có định mức nào thì kết quả rỗng.
    `series` chỉ có khi tập mã đã chọn đúng MỘT mã (biểu đồ diễn biến đơn giá), ngược lại `None`.
    """
    scope_cond = with_misa_cutoff(scope_cond)      # mốc sổ Misa: dòng Misa tới mốc + nguồn 1 / 2 sau mốc (chưa có mốc = như cũ)
    roles: dict[str, list[int]] = {}
    explicit = [c for c in (codes or []) if c] if mode == "code" else None
    if mode == "product":
        roles = component_roles(db, [c for c in (hh_codes or []) if c])
        if hh_codes:
            if not roles:
                return _empty()
            explicit = sorted(roles)
    conds = _conds(explicit or None, q=q, suppliers=suppliers, date_from=date_from, date_to=date_to, scope_cond=scope_cond)
    scope_conds = _conds(explicit or None, date_from=date_from, date_to=date_to, scope_cond=scope_cond,
                         skip_text_filters=True)
    stats = _stats(db, conds)
    offset, limit = ((page - 1) * page_size, page_size) if page is not None else (0, MAX_ROWS + 1)
    rows = _page_rows(db, conds, _order(sort_by, sort_dir), scope_cond, limit, offset) if stats["purchase_count"] else []
    return {"items": [_item(r, roles) for r in rows], "total": stats["purchase_count"], "stats": stats,
            "series": _series(db, conds) if explicit and len(explicit) == 1 and stats["priced_count"] else None,
            "suppliers": _supplier_options(db, scope_conds)}
