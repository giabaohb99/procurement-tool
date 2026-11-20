"""Bảng giá VTBB: mỗi mã vật tư một dòng — giá cũ / mới / chênh, số sản phẩm dùng, báo giá, ngưỡng (duoc-CR-784, phase 04).

SÁU truy vấn cố định: (1) các cột mã thành phần của định mức (số sản phẩm dùng + danh sách mã), (2) mã có báo giá,
(3–6) bốn truy vấn của `get_price_states`. Tính hết trong bộ nhớ (~3.000 mã), lọc + XẾP tại máy chủ rồi mới cắt trang —
luật §8: ô trống luôn xuống CUỐI cả hai chiều, khóa phụ là mã.
"""
from datetime import date

from sqlalchemy.orm import Session

from app.core.packaging_price_codes import CostWarning
from app.modules.product.model import Product
from app.modules.product_price.model import ProductPriceQuote
from app.modules.product_price.price_state_service import PriceState, get_price_states

from .cost_service import fold_text, price_warnings
from .impact_service import OTHER_GROUP, PART_COLUMNS
from .model import PackagingBom
from .numbers import iso, num
from .sorting import sort_blank_last

BREACH = (int(CostWarning.BELOW_FLOOR), int(CostWarning.ABOVE_CEILING))
#  khóa cột được phép xếp (whitelist) — khóa lạ bị bỏ qua, xếp theo mã
SORT_KEYS = {"code", "name", "group", "unit", "old", "new", "diff", "pct", "usage", "purchase_count", "last_date",
             "last_purchase_price", "last_purchase_date", "prev_purchase_price",
             "min", "max", "floor", "ceiling", "quote_price", "quote_from"}
TEXT_KEYS = {"name", "group", "unit"}


def _row(st: PriceState, usage: int) -> dict:
    diff = (st.new - st.old) if st.new is not None and st.old is not None else None
    quote = {"price": num(st.quote.price), "valid_from": iso(st.quote.valid_from), "supplier_code": st.quote.supplier_code} \
        if st.quote else None
    warnings = [int(w) for w in price_warnings(st, st.new, st.p1.unit if st.p1 else "")]
    return {"code": st.code, "name": st.name, "group": st.group or OTHER_GROUP, "unit": st.unit,
            "old": num(st.old), "new": num(st.new), "diff": num(diff),
            "pct": num(diff / st.old, 6) if diff is not None and st.old else None, "usage": usage,
            #  lần mua CÓ GIÁ gần nhất / lần trước đó (luật giá > 0 của `get_price_states`) — không thêm truy vấn
            "last_purchase_price": num(st.p1.price) if st.p1 else None,
            "last_purchase_date": iso(st.p1.date) if st.p1 else None,
            "prev_purchase_price": num(st.p2.price) if st.p2 else None,
            "purchase_count": st.purchase_count, "last_date": iso(st.last_date), "min": num(st.min), "max": num(st.max),
            "floor": num(st.floor), "ceiling": num(st.ceiling), "quote": quote, "warnings": warnings,
            "quote_price": quote["price"] if quote else None, "quote_from": quote["valid_from"] if quote else None}


def sort_rows(rows: list[dict], sort_by: str, sort_dir: str, allowed: set[str] = SORT_KEYS) -> list[dict]:
    """Ô trống xuống CUỐI cả hai chiều; khóa phụ là mã (xếp ổn định: xếp mã tăng trước rồi mới xếp khóa chính).
    `allowed` = khóa cột được phép xếp của màn gọi (mặc định: của Bảng giá); khóa lạ → xếp theo mã."""
    key = sort_by if sort_by in allowed else "code"

    def value(row: dict):
        v = row.get(key)
        return fold_text(v) if key in TEXT_KEYS and isinstance(v, str) else v

    return sort_blank_last(rows, value, lambda r: r["code"], desc=sort_dir == "desc")


def _component_usage(db: Session) -> tuple[dict[str, int], set[str]]:
    """`(số sản phẩm dùng mỗi mã thành phần, mã có báo giá)` — hai truy vấn, dựng tập mã VTBB."""
    usage: dict[str, int] = {}
    for row in db.query(*[getattr(PackagingBom, c) for c in PART_COLUMNS]).all():
        for code in {c for c in row if c}:
            usage[code] = usage.get(code, 0) + 1
    quoted = {c for (c,) in db.query(ProductPriceQuote.product_code).distinct().all()}
    return usage, quoted


def _keep(row: dict, needle: str, group: str) -> bool:
    """Bộ lọc chữ của Bảng giá: `q` khớp mã hoặc tên, `group` khớp đúng nhóm — cùng một luật cho đường đầy đủ và đường nhanh."""
    if needle and needle not in fold_text(row["code"]) and needle not in fold_text(row["name"]):
        return False
    return not group.strip() or fold_text(row["group"]) == fold_text(group)


def build_price_list(db: Session, *, q: str = "", group: str = "", scope: str = "bom", breach_only: bool = False,
                     date_from: date | None = None, date_to: date | None = None, sort_by: str = "code",
                     sort_dir: str = "asc", scope_cond=None, new_only: bool = False) -> list[dict]:
    """Toàn bộ dòng đã lọc + xếp (chưa cắt trang). `scope`: `bom` = mã thành phần ∪ mã có báo giá; `all` = thêm mọi mã
    có trong sổ giá. `new_only` = chế độ nhẹ của ô chọn mã (chỉ `new`, xem `get_price_states`): các cột cũ / chênh / min / max
    / số lần mua KHÔNG đáng tin ở chế độ này."""
    usage, quoted = _component_usage(db)
    codes = None if scope == "all" else set(usage) | quoted
    states = get_price_states(db, codes, date_from=date_from, date_to=date_to, scope_cond=scope_cond, also=set(usage) | quoted,
                              new_only=new_only)
    needle = fold_text(q)
    rows = [r for r in (_row(st, usage.get(code, 0)) for code, st in states.items()) if _keep(r, needle, group)]
    if breach_only:
        rows = [r for r in rows if any(w in BREACH for w in r["warnings"])]
    return sort_rows(rows, sort_by, sort_dir)


#  Khóa xếp chỉ phụ thuộc DANH MỤC (không cần giá): xếp + lọc + cắt trang xong rồi mới tính giá cho đúng các mã của trang.
STATIC_SORT_KEYS = {"code", "name", "group", "unit"}


def build_price_list_page(db: Session, *, page: int, page_size: int, q: str = "", group: str = "", scope: str = "bom",
                          breach_only: bool = False, date_from: date | None = None, date_to: date | None = None,
                          sort_by: str = "code", sort_dir: str = "asc", scope_cond=None) -> tuple[list[dict], int]:
    """`(dòng của trang, tổng số dòng sau lọc)` — màn hình Bảng giá.

    ĐƯỜNG NHANH khi `scope=bom`, không `breach_only` và xếp theo cột danh mục (`code, name, group, unit` — mặc định của màn):
    lọc + xếp + cắt trang trên khung danh mục (một truy vấn `tab_product`) RỒI mới tính giá cho đúng các mã của trang, nên sổ giá
    có lớn đến đâu cũng chỉ chạm vài chục mã. Còn lại (xếp theo số, chỉ mã vi phạm ngưỡng, `scope=all`) buộc phải tính giá cả
    tập rồi mới xếp: đường đầy đủ `build_price_list`. Hai đường cho CÙNG kết quả (có bài kiểm đối chiếu).
    """
    start = (page - 1) * page_size
    if scope != "bom" or breach_only or sort_by not in STATIC_SORT_KEYS:
        rows = build_price_list(db, q=q, group=group, scope=scope, breach_only=breach_only, date_from=date_from, date_to=date_to,
                                sort_by=sort_by, sort_dir=sort_dir, scope_cond=scope_cond)
        return rows[start:start + page_size], len(rows)

    usage, quoted = _component_usage(db)
    universe = set(usage) | quoted
    info = {c: (n or "", g or "", u or "") for c, n, g, u in
            db.query(Product.code, Product.name, Product.item_group, Product.unit).filter(Product.code.in_(universe or {""})).all()}
    needle = fold_text(q)
    frame = []
    for code in universe:
        name, grp, unit = info.get(code, ("", "", ""))
        row = {"code": code, "name": name, "group": grp or OTHER_GROUP, "unit": unit}
        if _keep(row, needle, group):
            frame.append(row)
    frame = sort_rows(frame, sort_by, sort_dir)
    page_codes = [r["code"] for r in frame[start:start + page_size]]
    states = get_price_states(db, set(page_codes), date_from=date_from, date_to=date_to, scope_cond=scope_cond,
                              also=set(page_codes))
    return [_row(states[c], usage.get(c, 0)) for c in page_codes], len(frame)
