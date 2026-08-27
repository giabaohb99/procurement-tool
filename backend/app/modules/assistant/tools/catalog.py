"""Danh mục tool loại A (tra cứu dữ liệu có cấu trúc) cho Trợ lý AI.

Mỗi tool ánh xạ ĐÚNG một truy vấn đọc, gác quyền của chính người hỏi. Model chỉ chọn tool +
điền tham số theo schema; KHÔNG sinh SQL. Xem `02-danh-sach-api-tool.md` để biết ý đồ từng tool.

Gác quyền (thực tế trong mã, khác chữ ở tài liệu vì `purchase_history` KHÔNG phải entity):
- Hợp đồng: entity `contract` (có scope theo pháp nhân) -> `apply_scope`.
- Sản phẩm / NCC: entity `product` / `supplier` (PUBLIC) -> chỉ cần bit `read`.
- Lịch sử mua / giá: gác `product.read` (đúng như tab "Lịch sử mua hàng"); tên NCC chỉ hiện
  khi có thêm `supplier.read`.
"""
from datetime import date

from sqlalchemy import func, or_

from app.core.scoping import apply_scope
from app.modules.contract.model import Contract
from app.modules.product.model import Product
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_history.service import list_history
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.supplier.model import Supplier

from .base import ToolContext, ToolSpec, denied

MAX_LIMIT = 100


def _today() -> str:
    return date.today().isoformat()


def _clamp(value, default: int, hi: int = MAX_LIMIT) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, hi))


def _num(v) -> float:
    """Numeric/Decimal của DB -> float cho JSON. None -> 0."""
    return float(v) if v is not None else 0.0


def _need(args: dict, key: str) -> str:
    return str(args.get(key) or "").strip()


def _expiry(end_date: str, as_of: str) -> str:
    """'active' còn hạn | 'expired' hết hạn | 'unknown' không ghi ngày."""
    if not end_date:
        return "unknown"
    return "expired" if end_date < as_of else "active"


# ── Nhóm 3: tra danh mục (T7, T8) ─────────────────────────────────────────────────────
def product_search(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("product"):
        return denied("sản phẩm")
    kw = _need(args, "keyword")
    if not kw:
        return {"error": "Thiếu từ khóa tra cứu."}
    limit = _clamp(args.get("limit"), 20)
    like = f"%{kw}%"
    rows = (
        ctx.db.query(Product)
        .filter(or_(Product.code.like(like), Product.name.like(like),
                    Product.hh_code.like(like), Product.hh_name.like(like)))
        .limit(limit)
        .all()
    )
    items = [
        {"code": r.code, "name": r.name, "item_group": r.item_group,
         "unit": r.unit, "hh_code": r.hh_code}
        for r in rows
    ]
    return {"items": items, "total": len(items)}


def supplier_search(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("supplier"):
        return denied("nhà cung cấp")
    kw = _need(args, "keyword")
    if not kw:
        return {"error": "Thiếu từ khóa tra cứu."}
    limit = _clamp(args.get("limit"), 20)
    like = f"%{kw}%"
    rows = (
        ctx.db.query(Supplier)
        .filter(or_(Supplier.code.like(like), Supplier.name.like(like),
                    Supplier.tax_code.like(like)))
        .limit(limit)
        .all()
    )
    items = [
        {"code": r.code, "name": r.name, "tax_code": r.tax_code,
         "supplier_type": r.supplier_type, "is_active": bool(r.is_active)}
        for r in rows
    ]
    return {"items": items, "total": len(items)}


# ── Nhóm 1: hợp đồng NCC (T1, T2, T3) ─────────────────────────────────────────────────
def _contract_row(r: Contract, as_of: str) -> dict:
    return {
        "code": r.code,
        "supplier_code": r.party_code,
        "supplier_name": r.party_name,
        "title": r.title,
        "start_date": r.start_date,
        "end_date": r.end_date,
        "status": r.status,
        "expiry": _expiry(r.end_date, as_of),
    }


def _scoped_contracts(ctx: ToolContext):
    """Query hợp đồng NCC đã gác scope theo pháp nhân của người hỏi."""
    q = ctx.db.query(Contract).filter(Contract.party_type == "supplier")
    return apply_scope(q, Contract, "contract", ctx.user, ctx.profile)


def _filter_expiry(q, status: str, as_of: str):
    # Phải KHỚP `_expiry`: hợp đồng KHÔNG ghi ngày hết hạn là 'unknown', KHÔNG tính là còn hạn.
    # Trước đây `active` gộp cả `end_date == ""` nên đếm (count) và liệt kê (list) lệch nhau.
    if status == "active":
        return q.filter(Contract.end_date != "", Contract.end_date >= as_of)
    if status == "expired":
        return q.filter(Contract.end_date != "", Contract.end_date < as_of)
    return q


def contract_list_by_expiry(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("contract"):
        return denied("hợp đồng")
    status = (_need(args, "status") or "all").lower()
    supplier_code = _need(args, "supplier_code")
    as_of = _need(args, "as_of_date") or _today()
    limit = _clamp(args.get("limit"), 50)
    q = _scoped_contracts(ctx)
    if supplier_code:
        q = q.filter(Contract.party_code == supplier_code)
    q = _filter_expiry(q, status, as_of)
    rows = q.order_by(Contract.end_date.asc()).limit(limit).all()
    return {
        "items": [_contract_row(r, as_of) for r in rows],
        "total": len(rows),
        "as_of_date": as_of,
        "status_filter": status,
    }


def supplier_contracts(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("contract"):
        return denied("hợp đồng")
    supplier_code = _need(args, "supplier_code")
    if not supplier_code:
        return {"error": "Thiếu mã nhà cung cấp (supplier_code)."}
    status = (_need(args, "status") or "all").lower()
    as_of = _today()
    q = _scoped_contracts(ctx).filter(Contract.party_code == supplier_code)
    q = _filter_expiry(q, status, as_of)
    rows = q.order_by(Contract.end_date.asc()).all()
    return {
        "items": [_contract_row(r, as_of) for r in rows],
        "total": len(rows),
        "supplier_code": supplier_code,
        "as_of_date": as_of,
    }


def contract_count_by_status(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("contract"):
        return denied("hợp đồng")
    as_of = _need(args, "as_of_date") or _today()
    group_by = (_need(args, "group_by") or "none").lower()
    rows = _scoped_contracts(ctx).with_entities(
        Contract.party_code, Contract.party_name, Contract.end_date
    ).all()

    total = {"active": 0, "expired": 0, "unknown": 0}
    per: dict[str, dict] = {}
    for party_code, party_name, end_date in rows:
        state = _expiry(end_date, as_of)
        total[state] += 1
        if group_by == "supplier":
            key = party_code or party_name or "(không rõ)"
            slot = per.setdefault(
                key, {"supplier_code": party_code, "supplier_name": party_name,
                      "active": 0, "expired": 0, "unknown": 0}
            )
            slot[state] += 1

    result = {
        "as_of_date": as_of,
        "total": len(rows),
        "active": total["active"],
        "expired": total["expired"],
        "unknown": total["unknown"],
    }
    if group_by == "supplier":
        result["by_supplier"] = sorted(
            per.values(), key=lambda s: s["active"] + s["expired"], reverse=True
        )
    return result


# ── Nhóm 2: giá & lịch sử mua (T4, T5, T6) ────────────────────────────────────────────
def product_purchase_history(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("product"):
        return denied("lịch sử mua hàng")
    product_code = _need(args, "product_code")
    if not product_code:
        return {"error": "Thiếu mã hàng (product_code)."}
    limit = _clamp(args.get("limit"), 50)
    see_supplier = ctx.can("supplier")
    total, rows = list_history(
        ctx.db, {"offset": 0, "limit": limit},
        product_code=product_code, search_by_supplier=see_supplier,
    )
    items = []
    for r in rows:
        row = {
            "order_date": r.order_date,
            "price": _num(r.price),
            "qty_order": _num(r.qty_order),
            "vat": _num(r.vat),
            "unit": r.unit,
            "po_code": r.po_code,
        }
        if see_supplier:
            row["supplier_code"] = r.supplier_code
            row["supplier_name"] = r.supplier_name
        items.append(row)
    out = {"items": items, "total": total, "product_code": product_code}
    if not see_supplier:
        out["note"] = "Ẩn thông tin nhà cung cấp vì người hỏi không có quyền xem NCC."
    return out


def _history_rows_for(ctx: ToolContext, product_code: str,
                      date_from: str, date_to: str) -> list[PurchaseHistory]:
    q = ctx.db.query(PurchaseHistory).filter(
        PurchaseHistory.product_code == product_code,
        PurchaseHistory.price > 0,
    )
    if date_from:
        q = q.filter(PurchaseHistory.order_date >= date_from)
    if date_to:
        q = q.filter(PurchaseHistory.order_date <= date_to)
    return q.all()


def product_best_price(ctx: ToolContext, args: dict) -> dict:
    # Tool này bản chất trả lời "NCC nào" nên đòi cả quyền xem NCC.
    if not ctx.can("product") or not ctx.can("supplier"):
        return denied("giá và nhà cung cấp")
    product_code = _need(args, "product_code")
    if not product_code:
        return {"error": "Thiếu mã hàng (product_code)."}
    top_n = _clamp(args.get("top_n"), 3, hi=20)
    date_from = _need(args, "date_from")
    date_to = _need(args, "date_to")
    rows = _history_rows_for(ctx, product_code, date_from, date_to)

    best: dict[str, dict] = {}
    for r in rows:
        price = _num(r.price)
        key = r.supplier_code or r.supplier_name
        slot = best.get(key)
        if slot is None or price < slot["price"]:
            best[key] = {
                "supplier_code": r.supplier_code,
                "supplier_name": r.supplier_name,
                "price": price,
                "qty_order": _num(r.qty_order),
                "vat": _num(r.vat),
                "unit": r.unit,
                "order_date": r.order_date,
            }
    ranked = sorted(best.values(), key=lambda s: s["price"])[:top_n]
    return {
        "items": ranked,
        "count": len(ranked),
        "product_code": product_code,
        "samples": len(rows),
        "note": "Giá so theo đơn giá thô, CHƯA quy đổi đơn vị/quy cách — nhắc người dùng "
                "kiểm tra cột 'unit' trước khi kết luận.",
    }


def suppliers_for_product(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("product") or not ctx.can("supplier"):
        return denied("nhà cung cấp theo mã hàng")
    product_code = _need(args, "product_code")
    if not product_code:
        return {"error": "Thiếu mã hàng (product_code)."}
    rows = _history_rows_for(ctx, product_code, "", "")

    agg: dict[str, dict] = {}
    for r in rows:
        key = r.supplier_code or r.supplier_name
        slot = agg.get(key)
        if slot is None:
            slot = agg[key] = {
                "supplier_code": r.supplier_code,
                "supplier_name": r.supplier_name,
                "times": 0,
                "last_order_date": "",
                "last_price": 0.0,
            }
        slot["times"] += 1
        if r.order_date >= slot["last_order_date"]:
            slot["last_order_date"] = r.order_date
            slot["last_price"] = _num(r.price)
    items = sorted(agg.values(), key=lambda s: s["times"], reverse=True)
    return {"items": items, "count": len(items), "product_code": product_code}


# ── Nhóm 4: tổng hợp toàn hệ (PO/chi tiêu/xếp hạng NCC/báo cáo) ────────────────────────
def _spend_expr():
    """Thành tiền của một dòng lịch sử: ưu tiên cột `amount` (đã gồm VAT); dòng dữ liệu cũ
    để `amount == 0` thì lùi về `qty_order * price`. Gộp NGAY trong SQL, không nạp hết bảng."""
    return func.coalesce(
        func.nullif(PurchaseHistory.amount, 0),
        PurchaseHistory.qty_order * PurchaseHistory.price,
    )


def _ph_in_range(q, date_from: str, date_to: str):
    if date_from:
        q = q.filter(PurchaseHistory.order_date >= date_from)
    if date_to:
        q = q.filter(PurchaseHistory.order_date <= date_to)
    return q


def recent_purchases(ctx: ToolContext, args: dict) -> dict:
    """Các lần mua GẦN NHẤT toàn hệ (mọi mã hàng), sắp theo ngày mới nhất."""
    if not ctx.can("product"):
        return denied("lịch sử mua hàng")
    limit = _clamp(args.get("limit"), 20)
    date_from = _need(args, "date_from")
    date_to = _need(args, "date_to")
    see_supplier = ctx.can("supplier")
    q = _ph_in_range(ctx.db.query(PurchaseHistory), date_from, date_to)
    rows = (
        q.order_by(PurchaseHistory.order_date.desc(), PurchaseHistory.id.desc())
        .limit(limit)
        .all()
    )
    items = []
    for r in rows:
        row = {
            "order_date": r.order_date,
            "product_code": r.product_code,
            "product_name": r.product_name,
            "qty_order": _num(r.qty_order),
            "price": _num(r.price),
            "amount": _num(r.amount) or _num(r.qty_order) * _num(r.price),
            "unit": r.unit,
            "po_code": r.po_code,
        }
        if see_supplier:
            row["supplier_code"] = r.supplier_code
            row["supplier_name"] = r.supplier_name
        items.append(row)
    out = {"items": items, "total": len(items)}
    if not see_supplier:
        out["note"] = "Ẩn NCC vì người hỏi không có quyền xem nhà cung cấp."
    return out


def top_suppliers_by_purchase(ctx: ToolContext, args: dict) -> dict:
    """Xếp hạng NCC theo lịch sử mua: trả CẢ tổng giá trị lẫn số lần để model tự diễn giải."""
    if not ctx.can("supplier"):
        return denied("nhà cung cấp")
    top_n = _clamp(args.get("top_n"), 5, hi=50)
    date_from = _need(args, "date_from")
    date_to = _need(args, "date_to")
    q = ctx.db.query(
        PurchaseHistory.supplier_code,
        func.max(PurchaseHistory.supplier_name),
        func.sum(_spend_expr()),
        func.count(),
    ).group_by(PurchaseHistory.supplier_code)
    q = _ph_in_range(q, date_from, date_to)
    rows = q.all()
    items = [
        {
            "supplier_code": code,
            "supplier_name": name,
            "total_amount": round(_num(total), 2),
            "times": int(times),
        }
        for code, name, total, times in rows
    ]
    items.sort(key=lambda s: s["total_amount"], reverse=True)
    return {
        "items": items[:top_n],
        "count": min(len(items), top_n),
        "date_from": date_from or None,
        "date_to": date_to or None,
        "ranked_by": "total_amount",
        "note": "Mỗi NCC kèm tổng giá trị (total_amount) và số lần mua (times).",
    }


def recent_purchase_orders(ctx: ToolContext, args: dict) -> dict:
    """Các ĐƠN MUA HÀNG (PO) gần nhất kèm GIÁ TRỊ (tổng thành tiền các dòng). Gác scope PO."""
    if not ctx.can("purchase_order"):
        return denied("đơn mua hàng")
    limit = _clamp(args.get("limit"), 20)
    supplier_code = _need(args, "supplier_code")
    date_from = _need(args, "date_from")
    date_to = _need(args, "date_to")
    q = apply_scope(
        ctx.db.query(PurchaseOrder), PurchaseOrder, "purchase_order", ctx.user, ctx.profile
    )
    if supplier_code:
        q = q.filter(PurchaseOrder.supplier_code == supplier_code)
    if date_from:
        q = q.filter(PurchaseOrder.order_date >= date_from)
    if date_to:
        q = q.filter(PurchaseOrder.order_date <= date_to)
    pos = (
        q.order_by(PurchaseOrder.order_date.desc(), PurchaseOrder.id.desc())
        .limit(limit)
        .all()
    )
    ids = [p.id for p in pos]
    totals: dict[int, float] = {}
    if ids:
        for po_id, tot in (
            ctx.db.query(POItem.po_id, func.sum(POItem.amount))
            .filter(POItem.po_id.in_(ids))
            .group_by(POItem.po_id)
            .all()
        ):
            totals[po_id] = _num(tot)
    items = [
        {
            "code": p.code,
            "order_date": p.order_date,
            "supplier_code": p.supplier_code,
            "supplier_name": p.supplier_name,
            "status": p.status,
            "amount": round(totals.get(p.id, 0.0), 2),
        }
        for p in pos
    ]
    return {"items": items, "total": len(items)}


def purchase_report(ctx: ToolContext, args: dict) -> dict:
    """Báo cáo tổng quan mua hàng trong kỳ: tổng chi tiêu, số dòng, số mã/NCC, top mã hàng;
    `group_by=month` thì kèm chi tiêu theo tháng. Tổng hợp trong SQL."""
    if not ctx.can("product"):
        return denied("báo cáo mua hàng")
    group_by = (_need(args, "group_by") or "none").lower()
    date_from = _need(args, "date_from")
    date_to = _need(args, "date_to")
    see_supplier = ctx.can("supplier")
    spend = _spend_expr()

    total_spend, lines, product_cnt, supplier_cnt = _ph_in_range(
        ctx.db.query(
            func.sum(spend),
            func.count(),
            func.count(func.distinct(PurchaseHistory.product_code)),
            func.count(func.distinct(PurchaseHistory.supplier_code)),
        ),
        date_from,
        date_to,
    ).one()

    top_q = (
        _ph_in_range(
            ctx.db.query(
                PurchaseHistory.product_code,
                func.max(PurchaseHistory.product_name),
                func.sum(spend),
                func.count(),
            ),
            date_from,
            date_to,
        )
        .group_by(PurchaseHistory.product_code)
        .order_by(func.sum(spend).desc())
        .limit(5)
    )
    top_products = [
        {"product_code": code, "product_name": name,
         "amount": round(_num(total), 2), "times": int(times)}
        for code, name, total, times in top_q.all()
    ]

    out = {
        "date_from": date_from or None,
        "date_to": date_to or None,
        "total_spend": round(_num(total_spend), 2),
        "lines": int(lines or 0),
        "product_count": int(product_cnt or 0),
        "top_products": top_products,
    }
    if see_supplier:
        out["supplier_count"] = int(supplier_cnt or 0)
    if group_by == "month":
        month = func.substr(PurchaseHistory.order_date, 1, 7)
        by_month = (
            _ph_in_range(ctx.db.query(month, func.sum(spend)), date_from, date_to)
            .group_by(month)
            .order_by(month)
            .all()
        )
        out["by_month"] = [
            {"month": m or "(không rõ)", "amount": round(_num(a), 2)} for m, a in by_month
        ]
    return out


# ── Nhóm 5: thống kê TÙY BIẾN (một công cụ, tham số rộng) ─────────────────────────────
# "Rộng về câu hỏi, khóa về dữ liệu": chỉ số/chiều/lọc đều nằm trong danh sách khai sẵn dưới
# đây, model KHÔNG sinh SQL và không chọn được bảng/cột ngoài luồng. Vẫn gác quyền như các tool
# lịch sử mua (product.read; chia theo NCC thì cần thêm supplier.read).
_METRICS = {
    "total_amount": lambda: func.sum(_spend_expr()),
    # count phải tham chiếu một cột của bảng để suy ra FROM khi dimension=none (query chỉ có
    # mỗi func.count() thì SQLAlchemy không biết bảng nào -> ra 1 thay vì đếm dòng).
    "count": lambda: func.count(PurchaseHistory.id),
    "qty": lambda: func.sum(PurchaseHistory.qty_order),
    "avg_price": lambda: func.avg(PurchaseHistory.price),
}
_METRIC_LABEL = {
    "total_amount": "Tổng chi tiêu (đã gồm VAT)",
    "count": "Số dòng mua",
    "qty": "Tổng số lượng đặt",
    "avg_price": "Đơn giá trung bình",
}
_DIMENSIONS = {
    "supplier": (PurchaseHistory.supplier_code, PurchaseHistory.supplier_name),
    "product": (PurchaseHistory.product_code, PurchaseHistory.product_name),
    "month": (func.substr(PurchaseHistory.order_date, 1, 7), None),
    "none": (None, None),
}


def _metric_value(metric: str, raw):
    """count -> số nguyên; còn lại -> float làm tròn 2 số cho JSON."""
    if metric == "count":
        return int(raw or 0)
    return round(_num(raw), 2)


def analytics_query(ctx: ToolContext, args: dict) -> dict:
    """Thống kê mua hàng TÙY BIẾN: chọn chỉ số + chiều + khoảng ngày từ danh sách khai sẵn.
    Một công cụ phủ nhiều biến thể câu hỏi mà KHÔNG sinh SQL và vẫn gác quyền người hỏi."""
    if not ctx.can("product"):
        return denied("dữ liệu mua hàng")
    metric = (_need(args, "metric") or "total_amount").lower()
    dimension = (_need(args, "dimension") or "none").lower()
    if metric not in _METRICS:
        return {"error": f"Chỉ số '{metric}' không hợp lệ. Chọn: {', '.join(_METRICS)}."}
    if dimension not in _DIMENSIONS:
        return {"error": f"Chiều '{dimension}' không hợp lệ. Chọn: {', '.join(_DIMENSIONS)}."}
    # Chia theo NCC = lộ danh tính NCC -> đòi thêm quyền xem nhà cung cấp.
    if dimension == "supplier" and not ctx.can("supplier"):
        return denied("dữ liệu theo nhà cung cấp")

    date_from = _need(args, "date_from")
    date_to = _need(args, "date_to")
    supplier_code = _need(args, "supplier_code")
    product_code = _need(args, "product_code")
    sort = (_need(args, "sort") or "value_desc").lower()
    top_n = _clamp(args.get("top_n"), 10, hi=50)

    metric_expr = _METRICS[metric]()
    dim_key, dim_name = _DIMENSIONS[dimension]

    def _apply_filters(q):
        q = _ph_in_range(q, date_from, date_to)
        if supplier_code:
            q = q.filter(PurchaseHistory.supplier_code == supplier_code)
        if product_code:
            q = q.filter(PurchaseHistory.product_code == product_code)
        return q

    out = {
        "metric": metric,
        "metric_label": _METRIC_LABEL[metric],
        "dimension": dimension,
        "date_from": date_from or None,
        "date_to": date_to or None,
    }

    if dim_key is None:  # không chia chiều -> một con số tổng
        raw = _apply_filters(ctx.db.query(metric_expr)).scalar()
        out["value"] = _metric_value(metric, raw)
        return out

    cols = [dim_key, metric_expr] if dim_name is None else [dim_key, func.max(dim_name), metric_expr]
    q = _apply_filters(ctx.db.query(*cols)).group_by(dim_key)
    if sort == "value_asc":
        q = q.order_by(metric_expr.asc())
    elif sort == "dimension":
        q = q.order_by(dim_key.asc())
    else:
        q = q.order_by(metric_expr.desc())
    rows = q.limit(top_n).all()

    items = []
    for r in rows:
        if dim_name is None:
            key, name, value = r[0], None, r[1]
        else:
            key, name, value = r[0], r[1], r[2]
        items.append({"group": key, "group_name": name, "value": _metric_value(metric, value)})
    out["items"] = items
    out["count"] = len(items)
    out["sort"] = sort
    return out


# ── Khai báo tool cho model (name + description + JSON schema tham số) ─────────────────
_LIMIT_PARAM = {"type": "integer", "description": "Số dòng tối đa (mặc định tùy tool, trần 100)."}
_PRODUCT_CODE = {"type": "string", "description": "Mã hàng chính xác (product_code)."}

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="product_search",
        description="Tra mã hàng theo mã/tên/mô tả. Dùng khi người hỏi mô tả sản phẩm bằng "
                    "lời (vd 'thùng carton 5 lớp') để tìm ra product_code trước khi gọi tool khác.",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Từ khóa: mã, tên hoặc mã HH."},
                "limit": _LIMIT_PARAM,
            },
            "required": ["keyword"],
        },
        handler=product_search,
    ),
    ToolSpec(
        name="supplier_search",
        description="Tra nhà cung cấp theo tên/mã/MST để lấy supplier_code.",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Từ khóa: tên, mã hoặc MST."},
                "limit": _LIMIT_PARAM,
            },
            "required": ["keyword"],
        },
        handler=supplier_search,
    ),
    ToolSpec(
        name="contract_list_by_expiry",
        description="Liệt kê hợp đồng NCC theo trạng thái hạn (còn hạn/hết hạn) tính đến một "
                    "ngày. Trả số hợp đồng, NCC, ngày ký, ngày hết hạn.",
        parameters={
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "expired", "all"],
                           "description": "active=còn hạn, expired=hết hạn, all=tất cả (mặc định)."},
                "supplier_code": {"type": "string", "description": "Lọc theo một NCC (tùy chọn)."},
                "as_of_date": {"type": "string", "description": "Ngày xét hạn YYYY-MM-DD (mặc định hôm nay)."},
                "limit": _LIMIT_PARAM,
            },
        },
        handler=contract_list_by_expiry,
    ),
    ToolSpec(
        name="contract_count_by_status",
        description="Đếm số hợp đồng NCC còn hạn / hết hạn tính đến một ngày, tùy chọn phân rã "
                    "theo từng NCC. Dùng cho câu hỏi tổng hợp về số lượng.",
        parameters={
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "enum": ["supplier", "none"],
                             "description": "supplier=phân rã theo NCC; none=chỉ tổng (mặc định)."},
                "as_of_date": {"type": "string", "description": "Ngày xét hạn YYYY-MM-DD (mặc định hôm nay)."},
            },
        },
        handler=contract_count_by_status,
    ),
    ToolSpec(
        name="supplier_contracts",
        description="Liệt kê các hợp đồng của MỘT nhà cung cấp cụ thể (theo supplier_code).",
        parameters={
            "type": "object",
            "properties": {
                "supplier_code": {"type": "string", "description": "Mã NCC (bắt buộc)."},
                "status": {"type": "string", "enum": ["active", "expired", "all"],
                           "description": "Lọc theo trạng thái hạn (mặc định all)."},
            },
            "required": ["supplier_code"],
        },
        handler=supplier_contracts,
    ),
    ToolSpec(
        name="product_purchase_history",
        description="Lịch sử mua của một mã hàng: đã mua của ai, giá bao nhiêu, số lượng, ngày, "
                    "mã PO. Sắp theo ngày mới nhất.",
        parameters={
            "type": "object",
            "properties": {
                "product_code": _PRODUCT_CODE,
                "limit": _LIMIT_PARAM,
            },
            "required": ["product_code"],
        },
        handler=product_purchase_history,
    ),
    ToolSpec(
        name="product_best_price",
        description="Giá tốt nhất của một mã hàng: top NCC theo đơn giá thấp nhất, kèm số lượng, "
                    "VAT, đơn vị, ngày mua. Lưu ý chưa quy đổi đơn vị.",
        parameters={
            "type": "object",
            "properties": {
                "product_code": _PRODUCT_CODE,
                "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD (tùy chọn)."},
                "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD (tùy chọn)."},
                "top_n": {"type": "integer", "description": "Số NCC rẻ nhất trả về (mặc định 3)."},
            },
            "required": ["product_code"],
        },
        handler=product_best_price,
    ),
    ToolSpec(
        name="suppliers_for_product",
        description="Các NCC từng bán một mã hàng, kèm số lần mua và giá gần nhất. Dùng để gợi ý "
                    "danh sách NCC cho mã đó.",
        parameters={
            "type": "object",
            "properties": {"product_code": _PRODUCT_CODE},
            "required": ["product_code"],
        },
        handler=suppliers_for_product,
    ),
    ToolSpec(
        name="recent_purchases",
        description="Các lần mua GẦN NHẤT toàn hệ (mọi mã hàng), sắp theo ngày mới nhất. Dùng "
                    "cho câu hỏi 'mua gì gần nhất', 'lần mua mới nhất là gì'.",
        parameters={
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD (tùy chọn)."},
                "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD (tùy chọn)."},
                "limit": _LIMIT_PARAM,
            },
        },
        handler=recent_purchases,
    ),
    ToolSpec(
        name="top_suppliers_by_purchase",
        description="Xếp hạng nhà cung cấp MUA NHIỀU NHẤT theo lịch sử mua, kèm tổng giá trị "
                    "(total_amount) và số lần mua (times). Dùng cho 'NCC nào mua nhiều nhất'.",
        parameters={
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD (tùy chọn)."},
                "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD (tùy chọn)."},
                "top_n": {"type": "integer", "description": "Số NCC đứng đầu trả về (mặc định 5)."},
            },
        },
        handler=top_suppliers_by_purchase,
    ),
    ToolSpec(
        name="recent_purchase_orders",
        description="Các ĐƠN MUA HÀNG (PO) gần nhất kèm giá trị đơn (tổng thành tiền các dòng). "
                    "Dùng cho 'đơn hàng gần nhất', 'PO mới nhất giá trị bao nhiêu'.",
        parameters={
            "type": "object",
            "properties": {
                "supplier_code": {"type": "string", "description": "Lọc theo một NCC (tùy chọn)."},
                "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD (tùy chọn)."},
                "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD (tùy chọn)."},
                "limit": _LIMIT_PARAM,
            },
        },
        handler=recent_purchase_orders,
    ),
    ToolSpec(
        name="purchase_report",
        description="Báo cáo tổng quan mua hàng trong kỳ: tổng chi tiêu, số dòng mua, số mã hàng "
                    "/NCC, top mã hàng theo chi tiêu. group_by=month kèm chi tiêu theo tháng.",
        parameters={
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "enum": ["month", "none"],
                             "description": "month=chi tiêu theo tháng; none=chỉ tổng quan (mặc định)."},
                "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD (tùy chọn)."},
                "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD (tùy chọn)."},
            },
        },
        handler=purchase_report,
    ),
    ToolSpec(
        name="analytics_query",
        description="Thống kê mua hàng TÙY BIẾN — dùng khi câu hỏi KHÔNG khớp các công cụ chuyên "
                    "biệt. Chọn CHỈ SỐ (total_amount=chi tiêu, count=số dòng mua, qty=tổng số "
                    "lượng, avg_price=đơn giá TB) theo CHIỀU (supplier=NCC, product=mã hàng, "
                    "month=tháng, none=tổng gộp) trong khoảng ngày, lọc theo NCC/mã hàng. Ví dụ: "
                    "'chi tiêu của NCC X theo tháng', 'số lượng mã Y mua trong quý 1'.",
        parameters={
            "type": "object",
            "properties": {
                "metric": {"type": "string",
                           "enum": ["total_amount", "count", "qty", "avg_price"],
                           "description": "Chỉ số cần tính (mặc định total_amount)."},
                "dimension": {"type": "string",
                              "enum": ["supplier", "product", "month", "none"],
                              "description": "Chia theo chiều nào (mặc định none = tổng gộp một số)."},
                "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD (tùy chọn)."},
                "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD (tùy chọn)."},
                "supplier_code": {"type": "string", "description": "Lọc theo một NCC (tùy chọn)."},
                "product_code": {"type": "string", "description": "Lọc theo một mã hàng (tùy chọn)."},
                "sort": {"type": "string", "enum": ["value_desc", "value_asc", "dimension"],
                         "description": "Sắp xếp nhóm (mặc định value_desc). Chỉ áp khi có dimension."},
                "top_n": {"type": "integer", "description": "Số nhóm trả về (mặc định 10, trần 50)."},
            },
        },
        handler=analytics_query,
    ),
]
