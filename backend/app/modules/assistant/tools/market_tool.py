"""Tìm nguồn hàng cho Thu mua (phase 23.4 + 23.5, `doc/agent-hub/15` mục Phase 23).

Hai tool, cùng tinh thần «AI chỉ gợi ý, người quyết»:

* `market_price_search` (ai-CR-173) — tìm GIÁ + LINK sản phẩm trên web công khai (trang hãng, nhà phân phối, sàn TMĐT),
  trả danh sách NGUỒN (tiêu đề, link, nơi bán, đoạn trích có giá) để model của Trợ lý tự đọc và lập bảng; đặt cạnh GIÁ
  MUA GẦN NHẤT trong ERP (lịch sử mua theo mã hàng) và giá hải quan nếu có. Tool KHÔNG cào giá bằng regex rồi khẳng
  định — trang bán hàng đổi khuôn liên tục, con số bóc máy sai còn hại hơn không có; người đọc nguồn là model.
* `supplier_scorecard` (ai-CR-174) — chấm điểm NCC 0–100 từ dữ liệu ERP với trọng số khai ở `SCORE_WEIGHTS` (đại ca
  chưa chốt, đổi hằng số là đổi cả bảng): giá 40 · ổn định (số lần mua) 20 · giao đúng hạn 20 · pháp lý (hợp đồng còn
  hạn) 20. Mỗi phần ghi lý do ngắn; thiếu dữ liệu phần nào thì ghi vào `data_gaps` thay vì đoán.

Tìm web dùng lại `agent_hub/web_search.py` (DuckDuckGo / Bing + đọc trang công khai, không cần khóa Gemini) — không
viết bộ tìm mới. Chỉ đọc trang công khai, không đăng nhập, không vượt chặn bot (`web_search.fetch` tự bỏ trang không
tải được). Nội dung trang là DỮ LIỆU: model đã được dặn không coi câu trong đó là mệnh lệnh.

Gác quyền: `market_price_search` cần `product.read` (giá ERP đi qua đúng hàm của `catalog.py`, tên NCC chỉ hiện khi có
`supplier.read`, giá hải quan chỉ khi có `customs_price.read`). `supplier_scorecard` cần `supplier.read` + `product.read`
(như `suppliers_for_product`); giao hàng đọc ĐMH qua `apply_scope(PurchaseOrder)` khi có `purchase_order.read`, hợp đồng
qua `catalog._scoped_contracts` khi có `contract.read` — thiếu khóa nào thì phần đó thành `data_gaps`, không chặn cả tool.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from urllib.parse import urlparse

from sqlalchemy import or_

from app.core.scoping import apply_scope
from app.modules.product.model import Product
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order.model import PODelivery, PurchaseOrder
from app.modules.supplier.model import Supplier

from . import catalog
from .base import ToolContext, ToolSpec, denied

# ── Hằng số chung ──────────────────────────────────────────────────────────────────────
MAX_SOURCES = 8            # trần `limit` của market_price_search
FETCH_PAGES = 4            # đọc nội dung tối đa bấy nhiêu trang đầu (còn lại chỉ có đoạn tóm tắt của máy tìm)
EXCERPT_CHARS = 700        # mỗi trang trích tối đa bấy nhiêu ký tự quanh các chỗ có giá
_EXCERPT_WINDOW = 120
_MAX_PRICE_HITS = 3
_ERP_RECENT_ROWS = 5
_ERP_CANDIDATES = 5

#  Sàn TMĐT lớn: đại ca chưa cấm nên vẫn lấy, nhưng gắn tên để người đọc tự lọc (phase 23.4).
_MARKETPLACES = {"shopee.vn": "Shopee", "lazada.vn": "Lazada", "tiki.vn": "Tiki", "sendo.vn": "Sendo"}

#  Dấu hiệu CÓ GIÁ trong chữ của trang: 1.250.000đ · 1,2 triệu · 35.000 VNĐ · 12 USD. Chỉ dùng để CHỌN đoạn trích,
#  không dùng để kết luận giá.
_PRICE_RX = re.compile(
    r"\d{1,3}(?:[.,]\d{3}){1,4}\s*(?:đ|₫|vnd|vnđ|đồng)?|\d+(?:[.,]\d+)?\s*(?:triệu|tr\b|k\b|đ\b|₫|vnd\b|vnđ\b|usd\b|\$)",
    re.IGNORECASE)

# ── Trọng số chấm NCC (phase 23.5) — MẶC ĐỊNH, đại ca chưa chốt; đổi ở đây là đổi cả bảng ──
SCORE_WEIGHTS = {"gia": 40, "on_dinh": 20, "giao_hang": 20, "phap_ly": 20}
SCORE_WEIGHT_LABELS = {"gia": "Giá (đơn giá trung bình so NCC rẻ nhất)", "on_dinh": "Ổn định (số lần mua trong kỳ)",
                       "giao_hang": "Giao hàng đúng hạn (lần nhận <= ngày NCC cam kết)",
                       "phap_ly": "Pháp lý (hợp đồng còn hạn trong ERP)"}
EXPIRED_CONTRACT_SHARE = 0.25   # chỉ có hợp đồng ĐÃ hết hạn: hưởng 1/4 điểm pháp lý
DEFAULT_MONTHS = 12
MAX_MONTHS = 60
MAX_SUPPLIERS = 20

MARKET_NOTE = ("Giá web chỉ để THAM KHẢO, chưa gồm vận chuyển / VAT / chiết khấu số lượng và có thể đã đổi; mỗi dòng "
               "phải ghi ngày thấy giá (seen_on) và link. Chỉ đọc trang công khai, không đăng nhập, không vượt chặn bot. "
               "Nguồn ưu tiên: trang hãng, nhà phân phối chính thức; sàn TMĐT (Shopee / Lazada / Tiki) là giá bán lẻ, "
               "người đọc tự lọc theo cột seller.")
SCORECARD_NOTE = ("AI chỉ GỢI Ý theo dữ liệu ERP và trọng số mặc định ở `weights`; KHÔNG tự chọn NCC trên phiếu — người "
                  "mua quyết định. NCC chưa có trong ERP thì tìm thêm trên web bằng market_price_search (ứng viên mới). "
                  "Phần nào ghi trong data_gaps là CHƯA có dữ liệu, không phải NCC kém.")


# ── Tiện ích ──────────────────────────────────────────────────────────────────────────
def _host(url: str) -> str:
    host = (urlparse(url or "").hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _seller_of(url: str) -> str:
    host = _host(url)
    for domain, label in _MARKETPLACES.items():
        if host == domain or host.endswith("." + domain):
            return label
    return host


def _excerpt(text: str) -> str:
    """Đoạn trích quanh các chỗ CÓ GIÁ (tối đa 3 chỗ); trang không có số giá thì lấy đoạn đầu."""
    text = (text or "").strip()
    if not text:
        return ""
    windows: list[tuple[int, int]] = []
    for m in _PRICE_RX.finditer(text):
        lo, hi = max(0, m.start() - _EXCERPT_WINDOW), min(len(text), m.end() + _EXCERPT_WINDOW)
        if windows and lo <= windows[-1][1]:
            windows[-1] = (windows[-1][0], hi)      # dính vào cửa sổ trước
        else:
            windows.append((lo, hi))
        if len(windows) >= _MAX_PRICE_HITS:
            break
    if not windows:
        return text[:EXCERPT_CHARS]
    out = " ... ".join(text[lo:hi].strip() for lo, hi in windows)
    return out[:EXCERPT_CHARS]


def _dedupe_key(url: str) -> str:
    return (url or "").split("#")[0].rstrip("/").lower()


def search_product_sources(product: str, limit: int) -> tuple[list[dict], list[str]]:
    """Tìm web 1–2 lượt («giá <sp>», «báo giá <sp>») rồi đọc vài trang đầu. Trả (nguồn, các câu đã tìm).

    Dùng `web_search.search` + `web_search.fetch` của Agent Hub (DuckDuckGo → Bing, trang công khai). Lượt hai chỉ chạy
    khi lượt một chưa đủ `limit` nguồn — đỡ gọi máy tìm vô ích.
    """
    from app.modules.agent_hub import web_search

    queries = [f"giá {product}", f"báo giá {product}"]
    found: list[dict] = []
    seen: set[str] = set()
    asked: list[str] = []
    for q in queries:
        if len(found) >= limit:
            break
        asked.append(q)
        try:
            results = web_search.search(q, limit=limit)
        except Exception:  # noqa: BLE001 — máy tìm hỏng thì coi như không ra, không làm sập tool
            results = []
        for r in results:
            key = _dedupe_key(r.get("url", ""))
            if not key or key in seen:
                continue
            seen.add(key)
            found.append({"title": (r.get("title") or "").strip() or _host(r.get("url", "")),
                          "url": r["url"], "seller": _seller_of(r["url"]),
                          "snippet": (r.get("snippet") or "").strip(), "excerpt": ""})
            if len(found) >= limit:
                break
    top = found[:FETCH_PAGES]
    if top:
        with ThreadPoolExecutor(max_workers=len(top)) as pool:
            texts = list(pool.map(lambda s: _safe_fetch(web_search, s["url"]), top))
        for src, text in zip(top, texts):
            src["excerpt"] = _excerpt(text)
    return found, asked


def _safe_fetch(web_search, url: str) -> str:
    try:
        return web_search.fetch(url)
    except Exception:  # noqa: BLE001 — một trang hỏng không được kéo cả lượt
        return ""


# ── market_price_search (23.4) ─────────────────────────────────────────────────────────
def _resolve_product(ctx: ToolContext, product: str) -> tuple[Product | None, list[dict]]:
    """Tìm mã hàng ERP theo tên: đúng MỘT kết quả thì dùng luôn; nhiều thì trả ứng viên để model hỏi lại / chọn."""
    kw = (product or "").strip()
    if not kw:
        return None, []
    like = f"%{kw}%"
    rows = (ctx.db.query(Product)
            .filter(or_(Product.code.like(like), Product.name.like(like), Product.hh_name.like(like)))
            .limit(_ERP_CANDIDATES + 1).all())
    if len(rows) == 1:
        return rows[0], []
    return None, [{"code": r.code, "name": r.name, "unit": r.unit} for r in rows[:_ERP_CANDIDATES]]


def _erp_prices(ctx: ToolContext, product_code: str) -> dict:
    """Giá mua gần nhất + NCC rẻ nhất trong ERP, đi đúng hàm của `catalog.py` để không lệch số với màn Lịch sử mua."""
    history = catalog.product_purchase_history(ctx, {"product_code": product_code, "limit": _ERP_RECENT_ROWS})
    out: dict = {"product_code": product_code, "recent_purchases": history.get("items", []),
                 "total_purchases": history.get("total", 0)}
    if history.get("note"):
        out["note"] = history["note"]
    latest = history.get("items") or []
    if latest:
        out["latest_price"] = {k: latest[0].get(k) for k in ("order_date", "price", "unit", "qty_order", "po_code")}
    if ctx.can("supplier"):
        best = catalog.product_best_price(ctx, {"product_code": product_code, "top_n": 3})
        if not best.get("denied"):
            out["best_price_suppliers"] = best.get("items", [])
    return out


def _customs_summary(ctx: ToolContext, keyword: str) -> dict | None:
    """Giá hải quan của mặt hàng nếu người hỏi có quyền VÀ có dữ liệu — không có thì None, không báo lỗi."""
    if not keyword or not ctx.can("customs_price"):
        return None
    try:
        from app.modules.customs import service as customs

        st = customs.compute_stats(ctx.db, {"q": keyword, "hs_code": "", "date_from": "", "date_to": ""},
                                   "month", "adjusted", "")
    except Exception:  # noqa: BLE001 — không có bộ dữ liệu hải quan / lọc không hợp lệ: bỏ qua phần này
        return None
    cov = st.get("coverage") or {}
    if not cov.get("lines"):
        return None
    return {"unit": st.get("unit"), "summary": st.get("kpi"), "coverage": cov,
            "price_note": "Giá nhập khẩu USD trên một đơn vị tính theo tờ khai hải quan — không cộng lẫn đơn vị.",
            "url": "/customs-prices"}


def market_price_search(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("product"):
        return denied("giá sản phẩm")
    product = catalog._need(args, "product")
    if not product:
        return {"error": "Thiếu tên / quy cách sản phẩm (product)."}
    limit = catalog._clamp(args.get("limit"), 6, hi=MAX_SOURCES)
    product_code = catalog._need(args, "product_code")
    today = date.today().isoformat()

    sources, queries = search_product_sources(product, limit)
    for s in sources:
        s["seen_on"] = today

    out: dict = {
        "product": product, "queries": queries, "seen_on": today,
        "sources": sources, "count": len(sources),
        "columns": ["name", "spec", "price", "unit", "currency", "seller", "url", "seen_on"],
        "note": MARKET_NOTE,
    }
    if not sources:
        out["note"] = ("Không tìm được kết quả nào trên web cho sản phẩm này (máy tìm không trả lời hoặc không có trang "
                       "công khai). " + MARKET_NOTE)

    #  (b) giá ERP: có mã thì dùng mã; không thì dò theo tên, chỉ nhận khi ra đúng một mã.
    erp_product: Product | None = None
    if product_code:
        erp_product = ctx.db.query(Product).filter(Product.code == product_code).first()
        if erp_product is None:
            out["erp_note"] = f"Không có mã hàng {product_code} trong danh mục ERP; vẫn tra lịch sử mua theo mã đó."
    else:
        erp_product, candidates = _resolve_product(ctx, product)
        if candidates:
            out["erp_candidates"] = candidates
            out["erp_note"] = ("Nhiều mã hàng ERP khớp tên — hỏi người dùng chọn hoặc gọi lại với product_code để kèm "
                               "giá mua gần nhất.")
    code = product_code or (erp_product.code if erp_product is not None else "")
    if code:
        erp = _erp_prices(ctx, code)
        if erp_product is not None:
            erp["product_name"] = erp_product.name
            erp["unit"] = erp_product.unit
        out["erp"] = erp
    else:
        out.setdefault("erp_note", "Chưa đối chiếu được với mã hàng ERP nào — chỉ có giá web.")

    customs = _customs_summary(ctx, (erp_product.name if erp_product is not None else product))
    if customs:
        out["customs"] = customs
    return out


# ── supplier_scorecard (23.5) ──────────────────────────────────────────────────────────
def _window_from(months: int) -> str:
    return (date.today() - timedelta(days=30 * months)).isoformat()


def _product_codes_for(ctx: ToolContext, product: str, product_code: str) -> tuple[list[str], str]:
    """Tập mã hàng để gom NCC: mã truyền vào, hoặc mọi mã khớp tên trong danh mục / lịch sử mua."""
    if product_code:
        return [product_code], ""
    kw = (product or "").strip()
    if not kw:
        return [], ""
    like = f"%{kw}%"
    codes = {r.code for r in ctx.db.query(Product.code)
             .filter(or_(Product.code.like(like), Product.name.like(like), Product.hh_name.like(like))).limit(50)}
    codes |= {r.product_code for r in ctx.db.query(PurchaseHistory.product_code)
              .filter(PurchaseHistory.product_name.like(like), PurchaseHistory.product_code != "").distinct().limit(50)}
    return sorted(codes), like


def _history_query(ctx: ToolContext, codes: list[str], name_like: str, since: str):
    q = ctx.db.query(PurchaseHistory).filter(PurchaseHistory.price > 0)
    if codes and name_like:
        q = q.filter(or_(PurchaseHistory.product_code.in_(codes), PurchaseHistory.product_name.like(name_like)))
    elif codes:
        q = q.filter(PurchaseHistory.product_code.in_(codes))
    elif name_like:
        q = q.filter(PurchaseHistory.product_name.like(name_like))
    if since:
        q = q.filter(PurchaseHistory.order_date >= since)
    return q


def _delivery_stats(ctx: ToolContext, supplier_codes: list[str], since: str) -> dict[str, dict] | None:
    """{mã NCC: {total, on_time}} từ lần giao đã nhận (received_date) có ngày cam kết (promised_date), trên ĐMH trong
    phạm vi người hỏi. None = không có quyền xem ĐMH."""
    if not ctx.can("purchase_order"):
        return None
    po_q = apply_scope(ctx.db.query(PurchaseOrder.id, PurchaseOrder.supplier_code), PurchaseOrder, "purchase_order",
                       ctx.user, ctx.profile).filter(PurchaseOrder.supplier_code.in_(supplier_codes))
    po_supplier = {po_id: code for po_id, code in po_q.all()}
    stats = {c: {"total": 0, "on_time": 0, "late_days_max": 0} for c in supplier_codes}
    if not po_supplier:
        return stats
    rows = (ctx.db.query(PODelivery.po_id, PODelivery.promised_date, PODelivery.received_date)
            .filter(PODelivery.po_id.in_(list(po_supplier)), PODelivery.received_date != "",
                    PODelivery.promised_date != "")
            .all())
    for po_id, promised, received in rows:
        if since and received < since:
            continue
        slot = stats[po_supplier[po_id]]
        slot["total"] += 1
        if received <= promised:
            slot["on_time"] += 1
        else:
            try:
                late = (date.fromisoformat(received) - date.fromisoformat(promised)).days
            except ValueError:
                late = 0
            slot["late_days_max"] = max(slot["late_days_max"], late)
    return stats


def _contract_stats(ctx: ToolContext, supplier_codes: list[str], today: str) -> dict[str, dict] | None:
    """{mã NCC: {active, expired, unknown}} qua hợp đồng đã gác phạm vi. None = không có quyền xem hợp đồng."""
    if not ctx.can("contract"):
        return None
    from app.modules.contract.model import Contract

    rows = (catalog._scoped_contracts(ctx).filter(Contract.party_code.in_(supplier_codes))
            .with_entities(Contract.party_code, Contract.end_date).all())
    stats = {c: {"active": 0, "expired": 0, "unknown": 0} for c in supplier_codes}
    for code, end_date in rows:
        stats[code][catalog._expiry(end_date, today)] += 1
    return stats


def _pct(part: float, whole: float) -> float:
    return round(part / whole, 4) if whole else 0.0


def score_suppliers(agg: dict[str, dict], deliveries: dict[str, dict] | None,
                    contracts: dict[str, dict] | None) -> list[dict]:
    """Chấm điểm từ số liệu đã gom. Tách riêng để bài kiểm chấm đúng công thức mà không cần DB.

    agg[code] = {supplier_code, supplier_name, times, qty, value, last_order_date, units}
    """
    w = SCORE_WEIGHTS
    avg_price = {c: (a["value"] / a["qty"] if a["qty"] else 0.0) for c, a in agg.items()}
    priced = [p for p in avg_price.values() if p > 0]
    cheapest = min(priced) if priced else 0.0
    max_times = max((a["times"] for a in agg.values()), default=0)

    items = []
    for code, a in agg.items():
        parts: dict[str, float] = {}
        reasons: list[str] = []
        gaps: list[str] = []
        metrics: dict = {"avg_price": round(avg_price[code], 2), "units": sorted(a["units"]), "times": a["times"],
                         "last_order_date": a["last_order_date"]}

        #  Giá: rẻ nhất 40, còn lại tỉ lệ rẻ nhất / giá mình (giá gấp đôi = nửa điểm).
        p = avg_price[code]
        if p > 0 and cheapest > 0:
            parts["gia"] = round(w["gia"] * cheapest / p, 1)
            if len(priced) == 1:
                reasons.append(f"Chỉ có một NCC có giá ({p:,.0f}/{'/'.join(sorted(a['units'])) or 'đv'}) — chưa so được.")
            elif p == cheapest:
                reasons.append(f"Đơn giá TB {p:,.0f} — rẻ nhất trong các NCC so sánh.")
            else:
                reasons.append(f"Đơn giá TB {p:,.0f}, cao hơn NCC rẻ nhất {((p / cheapest) - 1) * 100:.0f}%.")
        else:
            parts["gia"] = 0.0
            gaps.append("chưa có đơn giá trong lịch sử mua")

        #  Ổn định: số lần mua trong kỳ so với NCC mua nhiều nhất.
        parts["on_dinh"] = round(w["on_dinh"] * _pct(a["times"], max_times), 1)
        reasons.append(f"Mua {a['times']} lần trong kỳ, lần cuối {a['last_order_date'] or 'không rõ'}.")

        #  Giao hàng: tỉ lệ lần nhận <= ngày cam kết.
        d = deliveries.get(code) if deliveries is not None else None
        if deliveries is None:
            parts["giao_hang"] = 0.0
            gaps.append("không có quyền xem ĐMH nên chưa chấm giao hàng")
        elif not d or not d["total"]:
            parts["giao_hang"] = 0.0
            gaps.append("chưa có dữ liệu giao hàng (lần giao có ngày cam kết và ngày nhận)")
        else:
            parts["giao_hang"] = round(w["giao_hang"] * _pct(d["on_time"], d["total"]), 1)
            late = f", trễ nhất {d['late_days_max']} ngày" if d["late_days_max"] else ""
            reasons.append(f"Giao đúng hạn {d['on_time']}/{d['total']} lần{late}.")
            metrics["deliveries"] = {"total": d["total"], "on_time": d["on_time"]}

        #  Pháp lý: hợp đồng còn hạn đủ điểm; chỉ có hợp đồng hết hạn hưởng một phần; không có thì 0 + ghi thiếu.
        c = contracts.get(code) if contracts is not None else None
        if contracts is None:
            parts["phap_ly"] = 0.0
            gaps.append("không có quyền xem hợp đồng nên chưa chấm pháp lý")
        elif c and c["active"]:
            parts["phap_ly"] = float(w["phap_ly"])
            reasons.append(f"Có {c['active']} hợp đồng còn hạn.")
            metrics["contracts"] = c
        elif c and c["expired"]:
            parts["phap_ly"] = round(w["phap_ly"] * EXPIRED_CONTRACT_SHARE, 1)
            reasons.append(f"Chỉ có {c['expired']} hợp đồng đã hết hạn — cần gia hạn / ký lại.")
            metrics["contracts"] = c
        else:
            parts["phap_ly"] = 0.0
            gaps.append("chưa có hợp đồng trong ERP")

        items.append({"supplier_code": code, "name": a["supplier_name"], "score": round(sum(parts.values()), 1),
                      "parts": parts, "metrics": metrics, "reasons": reasons, "data_gaps": gaps})
    items.sort(key=lambda s: (-s["score"], -s["metrics"]["times"], s["supplier_code"]))
    return items


def supplier_scorecard(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("supplier") or not ctx.can("product"):
        return denied("nhà cung cấp và lịch sử mua")
    product = catalog._need(args, "product")
    product_code = catalog._need(args, "product_code")
    wanted = [str(c).strip() for c in (args.get("supplier_codes") or []) if str(c).strip()][:MAX_SUPPLIERS]
    if not (product or product_code or wanted):
        return {"error": "Cần một trong: product (tên hàng), product_code (mã hàng) hoặc supplier_codes (danh sách mã NCC)."}
    months = catalog._clamp(args.get("months"), DEFAULT_MONTHS, hi=MAX_MONTHS)
    today = date.today().isoformat()
    since = _window_from(months)
    global_gaps: list[str] = []

    codes, name_like = _product_codes_for(ctx, product, product_code)
    if (product or product_code) and not codes and not name_like:
        return {"error": "Không nhận ra mặt hàng để gom NCC."}

    #  Gom lịch sử mua theo NCC trong kỳ; không có dòng nào trong kỳ thì nới ra toàn thời gian và nói rõ.
    q = _history_query(ctx, codes, name_like, since)
    if wanted:
        q = q.filter(PurchaseHistory.supplier_code.in_(wanted))
    rows = q.all()
    if not rows and (codes or name_like):
        rows = _history_query(ctx, codes, name_like, "").filter(
            PurchaseHistory.supplier_code.in_(wanted)).all() if wanted else _history_query(ctx, codes, name_like, "").all()
        if rows:
            global_gaps.append(f"Không có lần mua nào trong {months} tháng gần đây — đang dùng toàn bộ lịch sử.")

    agg: dict[str, dict] = {}
    for r in rows:
        key = r.supplier_code or r.supplier_name
        if not key:
            continue
        slot = agg.setdefault(key, {"supplier_code": r.supplier_code, "supplier_name": r.supplier_name, "times": 0,
                                    "qty": 0.0, "value": 0.0, "last_order_date": "", "units": set()})
        qty, price = catalog._num(r.qty_order), catalog._num(r.price)
        slot["times"] += 1
        if qty > 0:
            slot["qty"] += qty
            slot["value"] += qty * price
        else:
            slot["qty"] += 1
            slot["value"] += price
        if r.unit:
            slot["units"].add(r.unit)
        if r.order_date >= slot["last_order_date"]:
            slot["last_order_date"] = r.order_date
    #  NCC được nêu tên nhưng chưa từng mua mặt hàng này vẫn vào bảng (điểm 0, ghi thiếu) — đúng ý «so NCC A với B».
    for code in wanted:
        agg.setdefault(code, {"supplier_code": code, "supplier_name": "", "times": 0, "qty": 0.0, "value": 0.0,
                              "last_order_date": "", "units": set()})
    if not agg:
        return {"items": [], "count": 0, "months": months, "window_from": since, "products": codes,
                "weights": SCORE_WEIGHTS, "note": SCORECARD_NOTE,
                "data_gaps": ["Chưa có NCC nào từng bán mặt hàng này trong ERP — tìm ứng viên mới trên web bằng "
                              "market_price_search."]}

    supplier_codes = [c for c in agg if c]
    sup_rows = {s.code: s for s in ctx.db.query(Supplier).filter(Supplier.code.in_(supplier_codes))}
    for code, slot in agg.items():
        s = sup_rows.get(code)
        if s is not None:
            slot["supplier_name"] = s.name or slot["supplier_name"]
    deliveries = _delivery_stats(ctx, supplier_codes, since)
    contracts = _contract_stats(ctx, supplier_codes, today)
    items = score_suppliers(agg, deliveries, contracts)
    for it in items:
        s = sup_rows.get(it["supplier_code"])
        if s is not None:
            it["is_active"] = bool(s.is_active)
            it["url"] = f"/production/suppliers/{s.id}"
            if not s.is_active:
                it["reasons"].append("NCC đang ở trạng thái NGỪNG hoạt động trong danh mục.")
        else:
            it["data_gaps"].append("mã NCC không có trong danh mục ERP")

    if deliveries is None:
        global_gaps.append("Không có quyền xem đơn mua hàng: cột giao hàng để trống cho mọi NCC.")
    elif not any(d["total"] for d in deliveries.values()):
        global_gaps.append("Chưa có dữ liệu giao hàng (lần giao có ngày cam kết và ngày nhận) cho các NCC này.")
    if contracts is None:
        global_gaps.append("Không có quyền xem hợp đồng: cột pháp lý để trống cho mọi NCC.")
    units = {u for a in agg.values() for u in a["units"]}
    if len(units) > 1:
        global_gaps.append(f"Đơn vị tính lẫn nhau ({', '.join(sorted(units))}) — điểm giá so đơn giá thô, chưa quy đổi.")

    return {
        "items": items, "count": len(items), "months": months, "window_from": since, "as_of_date": today,
        "products": codes, "weights": SCORE_WEIGHTS, "weight_labels": SCORE_WEIGHT_LABELS,
        "data_gaps": global_gaps, "note": SCORECARD_NOTE,
    }


# ── Khai báo cho model ─────────────────────────────────────────────────────────────────
MARKET_PRICE_SEARCH_SPEC = ToolSpec(
    name="market_price_search",
    description=(
        "Tìm GIÁ và LINK sản phẩm trên web công khai (trang hãng, nhà phân phối, sàn TMĐT Shopee / Lazada / Tiki) và đặt "
        "cạnh GIÁ MUA GẦN NHẤT trong ERP (+ giá hải quan nếu có). Gọi khi hỏi 'giá thị trường thép phi 10', 'ngoài "
        "thị trường giấy A4 bao nhiêu', 'tìm link mua máy in HP', 'giá mình mua có đắt không'. Tool trả `sources` "
        "(tiêu đề, url, seller, snippet, excerpt = đoạn trích quanh chỗ có giá) — BẠN là người đọc: từ mỗi nguồn rút ra "
        "một dòng bảng theo `columns` (name · spec · price · unit · currency · seller · url · seen_on); nguồn không nêu "
        "giá rõ thì ghi 'không nêu giá' thay vì đoán; không bịa dòng ngoài nguồn. Sau bảng, so với `erp.latest_price` / "
        "`erp.best_price_suppliers` (nếu có) để nói giá công ty đang mua rẻ hay đắt hơn, nhắc khác quy cách / số lượng / "
        "VAT. Có `erp_candidates` thì hỏi người dùng chọn mã. LUÔN nhắc `note` (giá tham khảo, ngày thu thập)."),
    parameters={"type": "object", "properties": {
        "product": {"type": "string", "description": "Tên + quy cách sản phẩm cần tìm giá, ví dụ 'thép phi 10 Hòa Phát', "
                                                      "'giấy A4 Double A 80gsm'."},
        "product_code": {"type": "string", "description": "Mã hàng ERP (tùy chọn) để kèm giá mua gần nhất; không biết "
                                                           "thì bỏ trống, tool tự dò theo tên."},
        "limit": {"type": "integer", "minimum": 1, "maximum": MAX_SOURCES,
                  "description": f"Số nguồn web tối đa (mặc định 6, trần {MAX_SOURCES})."},
    }, "required": ["product"]},
    handler=market_price_search,
)

SUPPLIER_SCORECARD_SPEC = ToolSpec(
    name="supplier_scorecard",
    description=(
        "CHẤM ĐIỂM nhà cung cấp 0–100 cho một mặt hàng từ dữ liệu ERP, trọng số mặc định: giá 40 (đơn giá TB so NCC rẻ "
        "nhất) · ổn định 20 (số lần mua trong kỳ) · giao hàng đúng hạn 20 · pháp lý 20 (hợp đồng còn hạn). Gọi khi hỏi "
        "'NCC nào tốt nhất cho giấy A4', 'nên mua thép của ai', 'so NCC A với NCC B', 'đánh giá nhà cung cấp X'. Truyền "
        "product (tên) hoặc product_code, hoặc supplier_codes để so các NCC cụ thể. Khi trả lời: bảng điểm theo `items` "
        "(score + từng phần `parts` + `reasons`), nêu `weights` để người đọc biết cách chấm, liệt kê `data_gaps` là CHƯA CÓ "
        "DỮ LIỆU chứ không phải NCC kém, và LUÔN nhắc `note`: AI chỉ gợi ý, không tự chọn NCC trên phiếu; NCC chưa có "
        "trong ERP thì gọi market_price_search để tìm ứng viên mới."),
    parameters={"type": "object", "properties": {
        "product": {"type": "string", "description": "Tên mặt hàng (khớp một phần tên trong danh mục / lịch sử mua)."},
        "product_code": {"type": "string", "description": "Mã hàng ERP chính xác (ưu tiên hơn product)."},
        "supplier_codes": {"type": "array", "items": {"type": "string"}, "maxItems": MAX_SUPPLIERS,
                           "description": "Chỉ chấm các NCC này (mã NCC). Bỏ trống = mọi NCC từng bán mặt hàng."},
        "months": {"type": "integer", "minimum": 1, "maximum": MAX_MONTHS,
                   "description": f"Kỳ xét lịch sử mua / giao hàng, tính bằng tháng (mặc định {DEFAULT_MONTHS})."},
    }},
    handler=supplier_scorecard,
)

MARKET_SPECS = [MARKET_PRICE_SEARCH_SPEC, SUPPLIER_SCORECARD_SPEC]
