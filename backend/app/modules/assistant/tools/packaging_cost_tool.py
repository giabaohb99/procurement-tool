"""Ba công cụ Giá bao bì cho Trợ lý web / bot / cổng MCP (duoc-CR-784): tác động giá, tra giá VTBB, chi phí bao bì sản phẩm.

Trả lời các câu như **chai CPT0075 lên 2.600 thì sản phẩm nào tăng chi phí bao nhiêu**, **giá mua gần nhất của nhãn NHG0713**,
**5 lần mua gần nhất của CPT0075**, **chi phí bao bì / chai của HH0417.1**.

Không tính lại gì: gọi đúng dịch vụ của màn Giá bao bì (`packaging_cost.impact_service.compute_impact`,
`product_overview_service.build_product_overview`, `cost_service.compute_product_cost`,
`product_price.price_state_service.get_price_states`, `latest_priced_query.latest_priced_by_code`) nên số khớp màn web.

Gác như màn web, MỖI công cụ theo khóa của MÀN có dữ liệu nó trả (bao-CR-792, 27/11/2026 — trước đó cả ba dùng khóa chung
`packaging_cost`; giá vốn bao bì là dữ liệu nhạy cảm, không có `read` thì `denied`):
  - `packaging_price_impact`  -> `packaging_impact` (màn Tác động giá bao bì);
  - `packaging_price_lookup`  -> `packaging_price_list` (màn Bảng giá VTBB: giá cũ / mới, báo giá, min / max, số sản phẩm dùng);
    phần `recent_purchases` (n lần mua gần nhất) là dữ liệu của màn Giá mua gần nhất nên chỉ kèm khi có thêm
    `packaging_last_price.read`, tính trong phạm vi của khóa đó;
  - `packaging_product_cost`  -> `packaging_product_summary` (màn Tổng hợp theo sản phẩm).
Phạm vi PHÁP NHÂN đo trên sổ giá (`last_prices_controller.view_scope` theo đúng khóa đó) — giá chỉ tính trên các dòng sổ người
hỏi được thấy. Định mức / báo giá là danh mục dùng chung, không lọc (như màn). Mã ngoài phạm vi và mã không tồn tại trả CÙNG
một hình: không có giá nào. Số truy vấn cố định theo lượt (không theo số mã / số sản phẩm).
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from . import packaging_cost_format as fmt
from .base import ToolContext, ToolSpec, denied

IMPACT_ENTITY = "packaging_impact"
PRICE_LIST_ENTITY = "packaging_price_list"
LAST_PRICE_ENTITY = "packaging_last_price"
PRODUCT_SUMMARY_ENTITY = "packaging_product_summary"
CODE_MAX_LEN = 50
Q_MAX_LEN = 100
MAX_IMPACT_CODES = 50
MAX_LOOKUP_CODES = 20
DEFAULT_ROWS = 20
MAX_ROWS = 50
DEFAULT_PURCHASES = 5
MAX_PURCHASES = 10
TRENDS = ("all", "up", "down", "flat", "missing")
DENIED_WHAT = "giá bao bì (cần quyền xem {screen} ở cụm Giá NVL sản xuất)"


def _scope(ctx: ToolContext, entity: str):
    """Điều kiện phạm vi pháp nhân trên sổ giá của người hỏi theo khóa `entity` — đúng hàm của màn web (None = thấy hết)."""
    from app.modules.packaging_cost.last_prices_controller import view_scope

    return view_scope(ctx.db, ctx.user, entity, "read")


def _clamp(value, default: int, lo: int, hi: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(n, hi))


def _codes(raw, cap: int) -> tuple[list[str], str]:
    """Danh sách mã (mảng hoặc chuỗi cách dấu phẩy) → mã đã bỏ khoảng trắng / trùng, giữ thứ tự. Trả `(mã, lỗi)`."""
    if raw is None or raw == "":
        return [], ""
    items = raw.split(",") if isinstance(raw, str) else raw if isinstance(raw, list) else None
    if items is None:
        return [], "codes phải là danh sách mã."
    codes = list(dict.fromkeys(str(c).strip() for c in items if str(c or "").strip()))
    if any(len(c) > CODE_MAX_LEN for c in codes):
        return [], f"Mã vật tư dài tối đa {CODE_MAX_LEN} ký tự."
    if len(codes) > cap:
        return [], f"Tối đa {cap} mã một lượt."
    return codes, ""


def _assumed(raw) -> tuple[dict[str, Decimal], str]:
    """Giá giả định: mảng `[{code, price}]` (khuyên dùng) hoặc đối tượng `{mã: giá}`. Giá >= 0."""
    if not raw:
        return {}, ""
    pairs = raw.items() if isinstance(raw, dict) else (
        [(r.get("code"), r.get("price")) for r in raw if isinstance(r, dict)] if isinstance(raw, list) else None)
    if pairs is None:
        return {}, "assumed_prices phải là danh sách {code, price}."
    out: dict[str, Decimal] = {}
    for code, price in pairs:
        code = str(code or "").strip()
        if not code:
            continue
        try:
            value = Decimal(str(price))
        except (InvalidOperation, ValueError):
            return {}, f"Giá giả định của {code[:CODE_MAX_LEN]} không phải số."
        if not value.is_finite() or value < 0:
            return {}, f"Giá giả định của {code[:CODE_MAX_LEN]} phải là số >= 0."
        out[code] = value
    return out, ""


def _validation_message(exc) -> str:
    first = (exc.errors() or [{}])[0]
    return str(first.get("msg") or "Tham số không hợp lệ.").removeprefix("Value error, ")


# ── 1. Tác động giá ─────────────────────────────────────────────────────────────
def packaging_price_impact(ctx: ToolContext, args: dict) -> dict:
    from pydantic import ValidationError

    from app.modules.packaging_cost.impact_schema import ImpactRequest
    from app.modules.packaging_cost.impact_service import compute_impact

    if not ctx.can(IMPACT_ENTITY):
        return denied(DENIED_WHAT.format(screen="Tác động giá bao bì"))
    codes, err = _codes(args.get("codes"), MAX_IMPACT_CODES)
    assumed, err2 = _assumed(args.get("assumed_prices"))
    if err or err2:
        return {"error": err or err2}
    codes = list(dict.fromkeys([*codes, *assumed]))          # mã chỉ có giá giả định cũng tính là mã đã chọn
    if not codes:
        return {"error": "Thiếu mã vật tư bao bì (codes) — vd CPT0075."}
    if len(codes) > MAX_IMPACT_CODES:
        return {"error": f"Tối đa {MAX_IMPACT_CODES} mã một lượt."}
    top_n = _clamp(args.get("top_n"), DEFAULT_ROWS, 1, MAX_ROWS)
    sort_dir = "asc" if str(args.get("sort_dir") or "").lower() == "asc" else "desc"
    try:
        body = ImpactRequest(codes=codes, assumed_prices=assumed, page=1, page_size=top_n, sort_by="diff_bottle",
                             sort_dir=sort_dir)
    except ValidationError as exc:
        return {"error": _validation_message(exc)}
    res = compute_impact(ctx.db, body.codes, dict(body.assumed_prices), scope_cond=_scope(ctx, IMPACT_ENTITY), page=1,
                         page_size=top_n,
                         sort_by="diff_bottle", sort_dir=sort_dir)
    items = [fmt.impact_product_row(r) for r in res["products"]]
    kpis = {k: res["kpis"][k] for k in ("selected_count", "assumed_count", "affected_products", "increased", "decreased",
                                         "max_increase_bottle", "max_increase_carton")}
    order = "tăng ít nhất / giảm nhiều nhất trước" if sort_dir == "asc" else "tăng nhiều nhất trước"
    return {"currency": fmt.CURRENCY, "price_basis": fmt.PRICE_BASIS, "price_rule": fmt.OLD_NEW_RULE,
            "selected": [fmt.selected_code_row(r) for r in res["selected"]], "kpis": kpis, "items": items,
            "total": res["products_total"], "page": 1, "page_size": top_n, "has_more": res["products_total"] > len(items),
            "url": fmt.IMPACT_URL,
            "note": (f"items = sản phẩm bị ảnh hưởng, xếp theo chênh lệch chi phí bao bì / chai ({order}); kpis tính trên "
                     "TOÀN BỘ sản phẩm bị ảnh hưởng. applied = giá giả định nếu có, không thì giá mới. Cần đủ danh sách thì "
                     "đưa người dùng url (màn Tác động giá) để chọn mã và xuất Excel.")}


# ── 2. Tra giá VTBB ─────────────────────────────────────────────────────────────
def _search_codes(db, q: str, limit: int) -> tuple[list[str], bool]:
    """Mã VTBB khớp chữ tìm (mọi từ đều có trong mã hoặc tên), chỉ trong tập mã có định mức / báo giá / sổ giá. Mã trùng
    đúng chữ tìm đứng đầu."""
    from sqlalchemy import and_, case, or_, select, union

    from app.modules.packaging_cost.bom_parts_service import component_codes_query
    from app.modules.product.model import Product
    from app.modules.product_price.model import ProductPriceLedger, ProductPriceQuote

    terms = q.split()
    universe = union(component_codes_query(), select(ProductPriceQuote.product_code), select(ProductPriceLedger.product_code))
    match = and_(*[or_(Product.code.contains(t, autoescape=True), Product.name.contains(t, autoescape=True)) for t in terms])
    rows = (db.query(Product.code).filter(match, Product.code.in_(select(universe.subquery().c[0])))
            .order_by(case((Product.code == q, 0), else_=1), Product.code).limit(limit + 1).all())
    codes = [c for (c,) in rows]
    return codes[:limit], len(codes) > limit


def _usage(db, codes: list[str]) -> dict[str, int]:
    """Số sản phẩm có định mức dùng mỗi mã (một truy vấn)."""
    from app.modules.packaging_cost.bom_parts_service import usage_by_code

    counted = usage_by_code(db, codes)
    return {code: counted.get(code, 0) for code in codes}


def _supplier_names(db, codes: set[str]) -> dict[str, str]:
    from app.modules.packaging_cost.last_prices_service import supplier_label
    from app.modules.supplier.model import Supplier

    names = dict(db.query(Supplier.code, Supplier.name).filter(Supplier.code.in_(codes or {""})).all())
    return {c: supplier_label(names.get(c), c) for c in codes}


def packaging_price_lookup(ctx: ToolContext, args: dict) -> dict:
    from app.modules.packaging_cost.cost_service import price_warnings
    from app.modules.product_price.latest_priced_query import latest_priced_by_code
    from app.modules.product_price.model import ProductPriceLedger
    from app.modules.product_price.price_state_service import get_price_states

    if not ctx.can(PRICE_LIST_ENTITY):
        return denied(DENIED_WHAT.format(screen="Bảng giá VTBB"))
    codes, err = _codes(args.get("codes"), MAX_LOOKUP_CODES)
    if err:
        return {"error": err}
    q = " ".join(str(args.get("q") or "").split())[:Q_MAX_LEN]
    limit = _clamp(args.get("limit"), 10, 1, MAX_LOOKUP_CODES)
    can_recent = ctx.can(LAST_PRICE_ENTITY)      # n lần mua gần nhất = dữ liệu của màn Giá mua gần nhất
    n = _clamp(args.get("purchases"), DEFAULT_PURCHASES, 0, MAX_PURCHASES) if can_recent else 0
    has_more = False
    if not codes:
        if not q:
            return {"error": "Cần mã vật tư bao bì (codes) hoặc chữ cần tìm (q)."}
        codes, has_more = _search_codes(ctx.db, q, limit)
    base = {"currency": fmt.CURRENCY, "price_basis": fmt.PRICE_BASIS, "price_rule": fmt.OLD_NEW_RULE}
    if not codes:
        return {**base, "items": [], "total": 0, "has_more": False,
                "note": f"Không có mã vật tư bao bì nào khớp '{q}'. Thử mã chính xác (vd CPT0075) hoặc từ khác."}
    states = get_price_states(ctx.db, set(codes), scope_cond=_scope(ctx, PRICE_LIST_ENTITY), also=set(codes))
    recent: dict = {}
    if n:
        scope = _scope(ctx, LAST_PRICE_ENTITY)
        conds = [ProductPriceLedger.price > 0, *([scope] if scope is not None else [])]
        recent = latest_priced_by_code(ctx.db, n, codes=set(codes), rank_conds=conds)
    rows_of = {c: (recent[c].rows[:n] if c in recent else []) for c in codes}
    sup_codes = {p.supplier_code for rows in rows_of.values() for p in rows if p.supplier_code}
    for st in states.values():
        sup_codes |= {x.supplier_code for x in (st.p1, st.p2, st.quote) if x is not None and x.supplier_code}
    suppliers = _supplier_names(ctx.db, sup_codes)
    usage = _usage(ctx.db, codes)
    items = [fmt.lookup_row(states[c], usage[c], rows_of[c], suppliers,
                            price_warnings(states[c], states[c].p1.unit if states[c].p1 else ""))
             for c in codes]
    no_data = [c for c in codes if states[c].new is None and not states[c].name]
    out = {**base, "items": items, "total": len(items), "has_more": has_more,
           "note": ("recent_purchases = các lần mua CÓ GIÁ gần nhất (mới nhất trước); purchase_count đếm mọi dòng sổ giá kể cả "
                    "giá 0; min / max trên mọi lần mua có giá. Mở history_url để xem đủ lịch sử và biểu đồ.")}
    if not can_recent:
        out["note"] = ("Không kèm recent_purchases: người hỏi chưa có quyền xem màn Giá mua gần nhất (nhờ quản trị cấp nếu cần). "
                       "min / max trên mọi lần mua có giá. Mở history_url để xem lịch sử nếu có quyền.")
    if no_data:
        out["no_data_codes"] = no_data
        out["note"] += " no_data_codes = mã không có trong danh mục và không có giá nào bạn được xem."
    if has_more:
        out["note"] += f" Còn mã khác khớp '{q}' — lọc hẹp chữ tìm hoặc truyền đúng mã."
    return out


# ── 3. Chi phí bao bì theo sản phẩm ─────────────────────────────────────────────
def _costs_of_products(db, fg_codes: list[str], scope) -> list[dict]:
    """Chi phí bao bì của ĐÚNG các mã hàng hóa đã hỏi — cùng các bước của `build_product_overview` (định mức → trạng thái giá
    của mọi thành phần → `compute_product_cost` → `product_row`) nhưng chỉ đọc định mức của các mã đó, nên rẻ."""
    from app.modules.packaging_cost.bom_parts_service import load_bom_rows
    from app.modules.packaging_cost.cost_service import compute_product_cost
    from app.modules.packaging_cost.impact_service import bom_codes, product_row
    from app.modules.product_price.price_state_service import get_price_states

    boms = load_bom_rows(db, fg_codes=fg_codes)
    if not boms:
        return []
    needed = set().union(*(bom_codes(b) for b in boms))
    states = get_price_states(db, needed, scope_cond=scope, also=needed, stats_codes=set())
    units = {c: s.p1.unit for c, s in states.items() if s.p1}
    names = {c: s.name for c, s in states.items()}
    return [product_row(b, compute_product_cost(b, states, None, units), names) for b in boms]


def packaging_product_cost(ctx: ToolContext, args: dict) -> dict:
    from app.modules.packaging_cost.product_overview_service import build_product_overview

    if not ctx.can(PRODUCT_SUMMARY_ENTITY):
        return denied(DENIED_WHAT.format(screen="Tổng hợp theo sản phẩm"))
    fg_codes, err = _codes(args.get("fg_codes"), MAX_LOOKUP_CODES)
    if err:
        return {"error": err.replace("Mã vật tư", "Mã hàng hóa")}
    q = " ".join(str(args.get("q") or "").split())[:Q_MAX_LEN]
    trend = str(args.get("trend") or "all").strip().lower()
    if trend not in TRENDS:
        return {"error": f"trend chỉ nhận: {', '.join(TRENDS)}."}
    limit = _clamp(args.get("limit"), DEFAULT_ROWS, 1, MAX_ROWS)
    page = _clamp(args.get("page"), 1, 1, 10000)
    base = {"currency": fmt.CURRENCY, "price_basis": fmt.PRICE_BASIS, "price_rule": fmt.OLD_NEW_RULE}
    scope = _scope(ctx, PRODUCT_SUMMARY_ENTITY)
    if fg_codes:
        rows = _costs_of_products(ctx.db, fg_codes, scope)
        found = {r["fg_code"] for r in rows}
        out = {**base, "items": [fmt.product_cost_row(r) for r in rows], "total": len(rows), "page": 1,
               "page_size": len(rows), "has_more": False, "url": fmt.PRODUCTS_URL,
               "note": "Chi phí bao bì / chai và / thùng theo giá cũ và giá mới (không giả định)."}
        missing = [c for c in fg_codes if c not in found]
        if missing:
            out["no_bom_codes"] = missing
            out["note"] += " no_bom_codes = mã hàng hóa chưa có định mức bao bì."
        return out
    #  Không có mã: lọc chữ / xu hướng trên toàn bộ sản phẩm có định mức — đúng hàm của tab Tổng hợp theo sản phẩm.
    sort_dir = "asc" if trend == "down" else "desc"
    res = build_product_overview(ctx.db, q=q, trend=trend, sort_by="diff_bottle", sort_dir=sort_dir, page=page,
                                 page_size=limit, scope_cond=scope)
    items = [fmt.product_cost_row(r) for r in res["items"]]
    return {**base, "items": items, "total": res["total"], "page": page, "page_size": limit,
            "has_more": page * limit < res["total"], "counts": res["counts"], "url": fmt.PRODUCTS_URL,
            "note": ("items xếp theo chênh lệch chi phí / chai (giảm nhiều nhất trước khi trend=down, còn lại tăng nhiều "
                     "nhất trước). counts = số sản phẩm theo xu hướng (up tăng, down giảm, flat không đổi, missing chưa "
                     "có giá) sau lọc q. has_more thì gọi lại với page kế tiếp hoặc lọc hẹp q.")}


_CODES_PARAM = {"type": "array", "items": {"type": "string", "maxLength": CODE_MAX_LEN}}

PACKAGING_PRICE_IMPACT_SPEC = ToolSpec(
    name="packaging_price_impact",
    description=("Tác động giá bao bì: chọn mã vật tư bao bì (chai, nắp, nhãn, nhãn thùng, thùng — vd CPT0075, NHG0713) kèm "
                 "giá giả định nếu có, trả các sản phẩm dùng mã đó và chi phí bao bì / chai, / thùng cũ so với mới. Dùng "
                 "cho câu kiểu chai CPT0075 lên 2.600 thì sản phẩm nào tăng chi phí bao nhiêu, nhãn X tăng giá ảnh hưởng "
                 "những sản phẩm nào. Có số tổng (số sản phẩm bị ảnh hưởng, tăng / giảm, tăng tối đa). Giá trước VAT, VND."),
    parameters={"type": "object", "properties": {
        "codes": {**_CODES_PARAM, "maxItems": MAX_IMPACT_CODES,
                  "description": f"Mã vật tư bao bì cần xét (1–{MAX_IMPACT_CODES} mã)."},
        "assumed_prices": {"type": "array", "maxItems": MAX_IMPACT_CODES,
                           "description": "Giá giả định (trước VAT) cho từng mã, bỏ trống = dùng giá mới hiện có.",
                           "items": {"type": "object", "properties": {
                               "code": {"type": "string", "maxLength": CODE_MAX_LEN},
                               "price": {"type": "number", "minimum": 0}}, "required": ["code", "price"]}},
        "top_n": {"type": "integer", "minimum": 1, "maximum": MAX_ROWS,
                  "description": f"Số sản phẩm trả về (mặc định {DEFAULT_ROWS})."},
        "sort_dir": {"type": "string", "enum": ["desc", "asc"],
                     "description": "desc = tăng nhiều nhất trước (mặc định), asc = giảm nhiều nhất trước."}},
        "required": ["codes"]},
    handler=packaging_price_impact,
)

PACKAGING_PRICE_LOOKUP_SPEC = ToolSpec(
    name="packaging_price_lookup",
    description=("Tra giá vật tư bao bì (VTBB) theo mã hoặc chữ tìm: giá cũ / giá mới, lần mua gần nhất (ngày, NCC, giá), "
                 "lần trước, báo giá mới nhất, min / max, số sản phẩm đang dùng, và n lần mua gần nhất. "
                 "Dùng cho câu kiểu giá mua gần nhất của nhãn NHG0713, 5 lần mua gần nhất của CPT0075, chai này giá bao "
                 "nhiêu. Giá trước VAT, VND."),
    parameters={"type": "object", "properties": {
        "codes": {**_CODES_PARAM, "maxItems": MAX_LOOKUP_CODES,
                  "description": f"Mã VTBB cần tra (tối đa {MAX_LOOKUP_CODES})."},
        "q": {"type": "string", "maxLength": Q_MAX_LEN,
              "description": "Chữ tìm trong mã / tên khi chưa biết mã (vd chai 450ml)."},
        "purchases": {"type": "integer", "minimum": 0, "maximum": MAX_PURCHASES,
                      "description": f"Số lần mua gần nhất kèm theo mỗi mã (mặc định {DEFAULT_PURCHASES}, 0 = không kèm)."},
        "limit": {"type": "integer", "minimum": 1, "maximum": MAX_LOOKUP_CODES,
                  "description": "Số mã tối đa khi tìm bằng q (mặc định 10)."}}},
    handler=packaging_price_lookup,
)

PACKAGING_PRODUCT_COST_SPEC = ToolSpec(
    name="packaging_product_cost",
    description=("Chi phí bao bì của sản phẩm (mã hàng hóa HH): chi phí / chai và / thùng theo giá cũ và giá mới, chênh "
                 "lệch, xu hướng, từng thành phần (chai, nắp, nhãn, nhãn thùng, thùng) kèm giá. Truyền fg_codes để xem "
                 "đúng sản phẩm, hoặc q / trend để lọc toàn bộ (vd những sản phẩm chi phí bao bì tăng). Giá trước VAT, VND."),
    parameters={"type": "object", "properties": {
        "fg_codes": {**_CODES_PARAM, "maxItems": MAX_LOOKUP_CODES,
                     "description": f"Mã hàng hóa cần xem (tối đa {MAX_LOOKUP_CODES})."},
        "q": {"type": "string", "maxLength": Q_MAX_LEN,
              "description": "Lọc theo mã / tên sản phẩm / mã thành phần (khi không có fg_codes)."},
        "trend": {"type": "string", "enum": list(TRENDS),
                  "description": "up tăng, down giảm, flat không đổi, missing chưa có giá, all tất cả (mặc định)."},
        "limit": {"type": "integer", "minimum": 1, "maximum": MAX_ROWS,
                  "description": f"Số sản phẩm mỗi trang (mặc định {DEFAULT_ROWS})."},
        "page": {"type": "integer", "minimum": 1, "description": "Trang (mặc định 1)."}}},
    handler=packaging_product_cost,
)

PACKAGING_COST_SPECS = [PACKAGING_PRICE_IMPACT_SPEC, PACKAGING_PRICE_LOOKUP_SPEC, PACKAGING_PRODUCT_COST_SPEC]
