"""Dựng kết quả gọn cho ba công cụ Giá bao bì của Trợ lý / bot / cổng MCP (duoc-CR-784).

Chỉ ĐỔI HÌNH dữ liệu do dịch vụ của màn Giá bao bì đã tính (`packaging_cost.impact_service`, `product_overview_service`,
`product_price.price_state_service`) — không tính lại giá hay chi phí ở đây. Luật §5.6 (doc/erp/tro-ly-ai/.../21): mã kèm nhãn
tiếng Việt, tiền ghi rõ đơn vị và trước VAT, đường dẫn màn để người dùng mở xem đủ (cổng MCP tự nối gốc ERP cho khóa `url`).
"""
from __future__ import annotations

from urllib.parse import quote

from app.core.packaging_price_codes import (COST_TREND_LABELS, COST_WARNING_LABELS, PACKAGING_ROLE_LABELS, CostTrend,
                                            CostWarning, PackagingRole, price_source_text)

CURRENCY = "VND"
PRICE_BASIS = "Đơn giá / chi phí trước VAT, đơn vị VND."
#  Luật giá cũ / mới của màn Giá bao bì (price_state_service.derive_old_new) — để AI giải thích đúng, không tự đoán.
OLD_NEW_RULE = ("Giá mới = báo giá mới nhất nếu có (kể cả báo giá có hiệu lực sau hôm nay), không có báo giá thì là lần mua "
                "có giá gần nhất. Giá cũ = lần mua có giá gần nhất khi có báo giá, không thì là lần mua trước đó. Dòng giá 0 "
                "bị bỏ qua. Chi phí bao bì / chai = chai + nắp + nhãn + (nhãn thùng + thùng) / quy cách thùng.")
IMPACT_URL = "/procurement/packaging-cost"
PRODUCTS_URL = "/procurement/packaging-cost/products"
HISTORY_URL = "/procurement/packaging-cost/history"


def history_url(*, codes: list[str] | None = None, hh: list[str] | None = None) -> str:
    """Đường dẫn sâu của tab Lịch sử mua hàng (`?codes=` theo mã VTBB, `?hh=` theo mã sản phẩm)."""
    if codes:
        return f"{HISTORY_URL}?codes={quote(','.join(codes), safe=',')}"
    if hh:
        return f"{HISTORY_URL}?hh={quote(','.join(hh), safe=',')}"
    return HISTORY_URL


def pct_change(fraction) -> float | None:
    """Tỷ số (0,05) → phần trăm (5.0), 2 số lẻ."""
    return None if fraction is None else round(float(fraction) * 100, 2)


def role_label(role) -> str:
    try:
        return PACKAGING_ROLE_LABELS[PackagingRole(int(role))]
    except (TypeError, ValueError, KeyError):
        return ""


def trend_label(trend) -> str:
    try:
        return COST_TREND_LABELS[CostTrend(int(trend))]
    except (TypeError, ValueError, KeyError):
        return ""


def warning_labels(warnings: list) -> list[str]:
    """Cảnh báo dạng số (`[3, 6]`) hoặc dạng dòng sản phẩm (`[{kind, role}]`) → câu ngắn, kèm vai trò nếu có."""
    out: list[str] = []
    for w in warnings or []:
        kind, role = (w.get("kind"), w.get("role")) if isinstance(w, dict) else (w, None)
        try:
            text = COST_WARNING_LABELS[CostWarning(int(kind))]
        except (TypeError, ValueError, KeyError):
            continue
        label = role_label(role) if role is not None else ""
        #  "Thiếu giá chai" đã nói vai trò — không nối thêm "(Chai)".
        out.append(f"{text} ({label})" if label and label.lower() not in text.lower() else text)
    return out


def selected_code_row(row: dict) -> dict:
    """Một mã đã chọn ở Tác động giá (`impact_service.selected_row`) → dòng gọn."""
    return {"code": row["code"], "name": row["name"], "group": row["group"], "unit": row["unit"],
            "old_price": row["old"], "new_price": row["new"], "assumed_price": row["assumed"],
            "applied_price": row["applied"], "price_diff": row["diff"], "pct_change": pct_change(row["pct"]),
            "products_using": row["usage"], "min_price": row["min"], "max_price": row["max"],
            "floor_price": row["floor"], "ceiling_price": row["ceiling"], "last_purchase_date": row["last_date"],
            "warnings": warning_labels(row["warnings"]), "history_url": history_url(codes=[row["code"]])}


def _part(p: dict) -> dict:
    return {"role": p["role"], "role_label": role_label(p["role"]), "code": p["code"], "name": p["name"],
            "old_price": p["old"], "new_price": p["new"], "applied_price": p["applied"]}


def impact_product_row(row: dict) -> dict:
    """Một sản phẩm bị ảnh hưởng (`impact_service.product_row`) → dòng gọn; chỉ kèm thành phần ĐÃ CHỌN của sản phẩm đó."""
    return {"hh_code": row["hh_code"], "hh_name": row["hh_name"], "carton_qty": row["carton_qty"],
            "cost_old_bottle": row["cost_old_bottle"], "cost_applied_bottle": row["cost_applied_bottle"],
            "diff_bottle": row["diff_bottle"], "pct_change": pct_change(row["pct"]),
            "cost_old_carton": row["cost_old_carton"], "cost_applied_carton": row["cost_applied_carton"],
            "diff_carton": row["diff_carton"], "trend": row["trend"], "trend_label": trend_label(row["trend"]),
            "selected_parts": [_part(p) for p in row["parts"] if p["selected"]],
            "warnings": warning_labels(row["warnings"])}


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _num(value) -> float | None:
    return None if value is None else round(float(value), 4)


def _supplier_of(point, suppliers: dict[str, str]) -> str:
    """Tên nhà cung cấp của một lần mua: tên chép theo dòng sổ (nguồn Misa) thắng tên tra theo mã."""
    from app.modules.packaging_cost.last_prices_service import supplier_label

    name = (getattr(point, "supplier_name", "") or "").strip()
    return supplier_label(name, point.supplier_code) if name else suppliers.get(point.supplier_code, point.supplier_code)


def purchase_point(point, suppliers: dict[str, str]) -> dict | None:
    """Một lần mua (`PricePoint` / `LedgerRow`) → `{date, price, qty?, unit, supplier_code, supplier, source_label}`."""
    if point is None:
        return None
    day = getattr(point, "date", None) or getattr(point, "price_date", None)
    out = {"date": _iso(day), "price": _num(point.price), "unit": point.unit or "",
           "supplier_code": point.supplier_code, "supplier": _supplier_of(point, suppliers),
           "source_label": price_source_text(point.source_type, getattr(point, "line_stage", 0)) if point.source_type else ""}
    if getattr(point, "qty", None) is not None:
        out["qty"] = round(float(point.qty), 3)
    return out


def lookup_row(st, usage: int, recent: list, suppliers: dict[str, str], warnings: list) -> dict:
    """Trạng thái giá một mã (`price_state_service.PriceState`) + n lần mua gần nhất → dòng gọn của `packaging_price_lookup`."""
    diff = (st.new - st.old) if st.new is not None and st.old is not None else None
    quote = None if st.quote is None else {
        "price": _num(st.quote.price), "valid_from": _iso(st.quote.valid_from), "supplier_code": st.quote.supplier_code,
        "supplier": suppliers.get(st.quote.supplier_code, st.quote.supplier_code)}
    source = "Báo giá" if st.quote is not None else ("Lần mua gần nhất" if st.p1 is not None else None)
    return {"code": st.code, "name": st.name, "group": st.group or "Khác", "unit": st.unit,
            "old_price": _num(st.old), "new_price": _num(st.new), "new_price_source": source, "price_diff": _num(diff),
            "pct_change": pct_change(diff / st.old) if diff is not None and st.old else None,
            "last_purchase": purchase_point(st.p1, suppliers), "prev_purchase": purchase_point(st.p2, suppliers),
            "quote": quote, "purchase_count": st.purchase_count, "min_price": _num(st.min), "max_price": _num(st.max),
            "floor_price": _num(st.floor), "ceiling_price": _num(st.ceiling), "products_using": usage,
            "recent_purchases": [purchase_point(p, suppliers) for p in recent],
            "warnings": warning_labels([int(w) for w in warnings]), "history_url": history_url(codes=[st.code])}


def product_cost_row(row: dict) -> dict:
    """Một sản phẩm ở Tổng hợp theo sản phẩm (cùng hình `product_row`, không giá giả định) → dòng gọn kèm đủ thành phần."""
    return {"hh_code": row["hh_code"], "hh_name": row["hh_name"], "legal_name": row["legal_name"],
            "carton_qty": row["carton_qty"], "cost_old_bottle": row["cost_old_bottle"],
            "cost_new_bottle": row["cost_new_bottle"], "diff_bottle": row["diff_bottle"],
            "pct_change": pct_change(row["pct"]), "cost_old_carton": row["cost_old_carton"],
            "cost_new_carton": row["cost_applied_carton"], "diff_carton": row["diff_carton"],
            "trend": row["trend"], "trend_label": trend_label(row["trend"]),
            #  thành phần chưa khai mã thì bỏ (đã có trong `warnings` khi là nắp / nhãn) — kết quả gọn
            "parts": [{k: v for k, v in _part(p).items() if k != "applied_price"} for p in row["parts"] if p["code"]],
            "warnings": warning_labels(row["warnings"]), "history_url": history_url(hh=[row["hh_code"]])}
