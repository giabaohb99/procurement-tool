"""Phần ĐỌC của phân hệ Tra cứu giá hải quan (bao-CR-470, HQ2 · HQ4 · HQ6).

Không tính sẵn gì, không task định kỳ (02 §3.6): mọi con số tính lúc gọi, trên tập dòng
đã lọc. Kỳ gom (tháng / quý / năm) là THAM SỐ, không phải bảng lưu sẵn (02 §3.5).

Gom theo kỳ làm ở Python chứ không bằng hàm ngày của SQL: tập dòng sau khi lọc theo từ
khóa / mã HS chỉ vài chục tới vài nghìn dòng, và cùng một mã chạy y hệt trên MySQL lẫn
SQLite của bộ test. Khi nào đo được chậm thật mới đẩy xuống SQL (02 §3.7).
"""
import calendar
import io
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import extract, func, or_
from sqlalchemy.orm import Session

from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule, ImportStatus

from . import reader
from .constants import (COLUMNS, FLAT_IMPORT_TAX_RATE, FORMULA_CAS, MIN_LINES_FOR_BEST,
                        REGULATION_LIST_LABELS, TRANSPORT_LABELS, RegulationList)
from .model import CustomsLine, CustomsParty, CustomsRegulation, CustomsTariff

PERIODS = ("month", "quarter", "year")
PRICE_MODES = ("adjusted", "declared")
MAX_EXPORT_ROWS = 50_000
NEED_FILTER_MSG = "Nhập tên hàng / hoạt chất hoặc chọn mã HS để xem biểu đồ."


# ── Lọc ─────────────────────────────────────────────────────────────────────
def _id_list(value) -> list[int]:
    """Một id, một chuỗi «1,2,3» hay một danh sách → danh sách id > 0 (bao-CR-493: chọn NHIỀU)."""
    if value in (None, "", 0):
        return []
    items = value if isinstance(value, (list, tuple)) else str(value).split(",")
    out = []
    for v in items:
        try:
            n = int(str(v).strip())
        except (TypeError, ValueError):
            continue
        if n > 0:
            out.append(n)
    return out


def _as_number(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def apply_line_filters(q, f: dict):
    """Bộ lọc dùng CHUNG cho danh sách, biểu đồ, xếp hạng, xuất Excel — bốn nơi một luật.

    `q` (từ khóa) khớp CẢ tên hàng lẫn hoạt chất đã gắn: gõ ATRAZINE ra cả dòng ghi tên
    thương mại mà hoạt chất suy ra được là atrazine (HQ4).

    bao-CR-493 thêm theo sheet 4 của yêu cầu phòng Thu mua: doanh nghiệp / đối tác chọn NHIỀU
    (HOẶC), nguyên tệ, điều kiện giao hàng, khoảng đơn giá (giá HIỆU LỰC — điều chỉnh nếu có),
    khoảng lượng, khoảng tỷ giá USD, lô nạp nguồn. Khoảng số bỏ trống một đầu thì chỉ chặn một đầu.
    """
    term = (f.get("q") or "").strip()
    if term:
        like = f"%{term}%"
        q = q.filter(or_(CustomsLine.product_name.ilike(like), CustomsLine.active_ingredient.ilike(like)))
    if f.get("ingredient"):
        q = q.filter(CustomsLine.active_ingredient.ilike(f"%{f['ingredient'].strip()}%"))
    if f.get("hs_code"):
        q = q.filter(CustomsLine.hs_code.like(f"{f['hs_code'].strip()}%"))
    if f.get("formulation"):
        q = q.filter(CustomsLine.formulation == f["formulation"].strip().upper())
    for key, col in (("origin", CustomsLine.origin_country), ("unit", CustomsLine.unit_code)):
        if f.get(key):
            q = q.filter(col == f[key].strip().upper())
    for key, col in (("importer_id", CustomsLine.importer_id), ("partner_id", CustomsLine.partner_id),
                     ("batch_id", CustomsLine.batch_id)):
        ids = _id_list(f.get(key))
        if ids:
            q = q.filter(col.in_(ids))
    for key, col in (("currency", CustomsLine.currency), ("incoterm", CustomsLine.incoterm)):
        if f.get(key):
            q = q.filter(col == str(f[key]).strip().upper())
    effective_price = func.coalesce(CustomsLine.adj_price_usd, CustomsLine.price_usd)
    for key_lo, key_hi, col in (("price_min", "price_max", effective_price),
                                ("qty_min", "qty_max", CustomsLine.quantity),
                                ("rate_min", "rate_max", CustomsLine.usd_rate)):
        lo, hi = _as_number(f.get(key_lo)), _as_number(f.get(key_hi))
        if lo is not None:
            q = q.filter(col >= lo)
        if hi is not None:
            q = q.filter(col <= hi)
    if f.get("date_from"):
        q = q.filter(CustomsLine.reg_date >= _as_date(f["date_from"], start=True))
    if f.get("date_to"):
        q = q.filter(CustomsLine.reg_date <= _as_date(f["date_to"], start=False))
    return q


def _as_date(value: str, start: bool) -> date:
    """`YYYY-MM-DD` hoặc `YYYY-MM` (ô chọn tháng) → ngày; tháng thì lấy đầu / cuối tháng."""
    s = str(value).strip()
    try:
        if len(s) == 7:
            y, m = int(s[:4]), int(s[5:7])
            return date(y, m, 1) if start else date(y, m, calendar.monthrange(y, m)[1])
        return date.fromisoformat(s[:10])
    except ValueError:
        raise HTTPException(400, f"Ngày không hợp lệ: «{value}»") from None


def has_chart_filter(f: dict) -> bool:
    """Biểu đồ chỉ vẽ khi có từ khóa / hoạt chất / mã HS (đại ca chốt 23/09/2026): biểu đồ
    của toàn bộ dữ liệu là trộn hàng nghìn mặt hàng, kg lẫn lít — con số vô nghĩa."""
    return any((f.get(k) or "").strip() for k in ("q", "ingredient", "hs_code"))


# ── Danh sách dòng hàng ─────────────────────────────────────────────────────
def _num(v):
    return float(v) if isinstance(v, Decimal) else v


def compute_vnd_prices(ln: CustomsLine) -> tuple[float | None, float | None]:
    """Hai cột «Đơn giá quy đổi VND» (bao-CR-493) → (theo thuế 7% tạm tính, theo thuế suất XNK của dòng).

    Gốc quy đổi là GIÁ HIỆU LỰC (điều chỉnh nếu có, không thì khai báo — cùng luật với biểu đồ)
    nhân tỷ giá USD của ngày đăng ký. Thiếu tỷ giá thì cả hai cột trống; thiếu thuế suất XNK thì
    chỉ cột theo dòng trống — không tự điền 7% vào đó, hai cột phải nói hai chuyện khác nhau.
    Làm tròn tới đồng.
    """
    price = ln.adj_price_usd if ln.adj_price_usd is not None else ln.price_usd
    rate = ln.usd_rate if ln.usd_rate is not None else (ln.fx_rate if (ln.currency or "").upper() == "USD" else None)
    if price is None or rate is None or float(rate) <= 0:
        return None, None
    base = float(price) * float(rate)
    flat = round(base * (1 + FLAT_IMPORT_TAX_RATE))
    line_tax = round(base * (1 + float(ln.rate_import) / 100)) if ln.rate_import is not None else None
    return flat, line_tax


def serialize_lines(db: Session, lines: list[CustomsLine]) -> list[dict]:
    """Đủ 32 trường theo khóa của `COLUMNS` + vài trường dẫn xuất. Nối tên đối tượng
    bằng MỘT truy vấn cho cả trang, không truy vấn theo từng dòng."""
    ids = {x for ln in lines for x in (ln.importer_id, ln.partner_id) if x}
    parties = {p.id: p for p in db.query(CustomsParty).filter(CustomsParty.id.in_(ids))} if ids else {}
    out = []
    for ln in lines:
        imp, par = parties.get(ln.importer_id), parties.get(ln.partner_id)
        d = {"id": ln.id, "batch_id": ln.batch_id, "source_row": ln.source_row,
             "date_fixed": bool(ln.date_fixed), "importer_id": ln.importer_id,
             "partner_id": ln.partner_id, "active_ingredient": ln.active_ingredient,
             "formulation": ln.formulation}
        for key, _ in COLUMNS:
            if key == "importer_tax_code":
                d[key] = imp.tax_code if imp else ""
            elif key == "importer_name":
                d[key] = imp.name if imp else ""
            elif key == "partner_name":
                d[key] = par.name if par else ""
            elif key == "transport_mode":
                d[key] = ln.transport_mode
                d["transport_label"] = TRANSPORT_LABELS.get(ln.transport_mode, "") if ln.transport_mode else ""
            else:
                v = getattr(ln, key)
                d[key] = v.isoformat() if isinstance(v, date) else _num(v)
        d["effective_price_usd"] = _num(ln.adj_price_usd if ln.adj_price_usd is not None else ln.price_usd)
        d["price_vnd_flat"], d["price_vnd_line_tax"] = compute_vnd_prices(ln)
        out.append(d)
    return out


def list_lines(db: Session, f: dict, offset: int, limit: int) -> tuple[int, list[dict]]:
    q = apply_line_filters(db.query(CustomsLine), f)
    #  Đếm thẳng COUNT(id) — `Query.count()` bọc cả câu SELECT mọi cột thành bảng con.
    total = apply_line_filters(db.query(func.count(CustomsLine.id)), f).scalar() or 0
    rows = q.order_by(CustomsLine.reg_date.desc(), CustomsLine.id.desc()).offset(offset).limit(limit).all()
    return total, serialize_lines(db, rows)


def get_line(db: Session, line_id: int) -> dict:
    ln = db.get(CustomsLine, line_id)
    if not ln:
        raise HTTPException(404, "Không tìm thấy dòng hàng")
    return serialize_lines(db, [ln])[0]


# ── Thống kê theo kỳ ────────────────────────────────────────────────────────
def _period_key(d: date, period: str) -> str:
    if period == "year":
        return f"{d.year}"
    if period == "quarter":
        return f"{d.year}-Q{(d.month - 1) // 3 + 1}"
    return f"{d.year}-{d.month:02d}"


def _period_label(key: str, period: str) -> str:
    if period == "year":
        return key
    if period == "quarter":
        y, qn = key.split("-Q")
        return f"Q{qn}/{y}"
    y, m = key.split("-")
    return f"{m}/{y}"


def _period_range(first: str, last: str, period: str) -> list[str]:
    """Mọi kỳ từ đầu tới cuối, KỂ CẢ kỳ trống — biểu đồ phải đứt đoạn ở kỳ không có dòng
    nào (ATRAZINE tháng 7), không được vẽ thành 0 hay nối đường qua (04 §4)."""
    keys, cur = [], first
    while True:
        keys.append(cur)
        if cur == last:
            return keys
        if period == "year":
            cur = str(int(cur) + 1)
        elif period == "quarter":
            y, qn = cur.split("-Q")
            y, qn = (int(y) + 1, 1) if qn == "4" else (int(y), int(qn) + 1)
            cur = f"{y}-Q{qn}"
        else:
            y, m = map(int, cur.split("-"))
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
            cur = f"{y}-{m:02d}"


def _price(row, price_mode: str):
    adj, dec = row.adj_price_usd, row.price_usd
    return adj if (price_mode == "adjusted" and adj is not None) else dec


def _quantile(sorted_prices: list[float], q: float):
    """Phân vị nội suy tuyến tính trên danh sách ĐÃ SẮP XẾP; rỗng → None."""
    if not sorted_prices:
        return None
    pos = (len(sorted_prices) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(sorted_prices) - 1)
    return round(sorted_prices[lo] + (sorted_prices[hi] - sorted_prices[lo]) * (pos - lo), 4)


def _aggregate(rows, period: str, price_mode: str) -> tuple[list[dict], dict]:
    """Gom theo kỳ. Ngoài thấp / cao / bình quân gia quyền còn trả PHÂN VỊ 25–50–75.

    Vì sao cần phân vị: tên hàng là chữ tự do nên cùng từ khóa hay lẫn vài dòng giá lạ
    (gói nhỏ, mẫu thử, khai sai đơn vị — đo được 250 USD/lít giữa đám 2–4 USD/lít). Vẽ
    dải thấp–cao thì một dòng lạ kéo trục lên trần và ép đường giá dẹp sát đáy. Dải
    25–75% là khoảng của NỬA số dòng ở giữa — không bị một dòng lạ kéo lệch; thấp / cao
    vẫn trả để bảng và ô rê chuột nói ra.
    """
    buckets = defaultdict(lambda: {"count": 0, "qty": 0.0, "value": 0.0, "prices": []})
    for r in rows:
        b = buckets[_period_key(r.reg_date, period)]
        b["count"] += 1
        p = _price(r, price_mode)
        if p is None:
            continue
        p = float(p)
        b["prices"].append(p)
        qty = float(r.quantity or 0)
        if qty > 0:
            b["qty"] += qty
            b["value"] += p * qty
    if not buckets:
        return [], {}
    for b in buckets.values():
        b["prices"].sort()
    keys = sorted(buckets)
    series = []
    for k in _period_range(keys[0], keys[-1], period):
        b = buckets.get(k)
        prices = b["prices"] if b else []
        wavg = (b["value"] / b["qty"]) if b and b["qty"] else None
        series.append({"period": k, "label": _period_label(k, period), "count": b["count"] if b else 0,
                       "qty": round(b["qty"], 4) if b else 0,
                       "min": prices[0] if prices else None, "max": prices[-1] if prices else None,
                       "p25": _quantile(prices, 0.25), "median": _quantile(prices, 0.5),
                       "p75": _quantile(prices, 0.75),
                       "wavg": round(wavg, 4) if wavg is not None else None,
                       "low_data": bool(b) and b["count"] < MIN_LINES_FOR_BEST})
    qty = sum(b["qty"] for b in buckets.values())
    value = sum(b["value"] for b in buckets.values())
    allp = sorted(p for b in buckets.values() for p in b["prices"])
    p25, p75 = _quantile(allp, 0.25), _quantile(allp, 0.75)
    #  Dòng "giá bất thường" theo luật hộp râu 1,5 × IQR — chỉ để ĐẾM và nói ra, không loại khỏi số liệu.
    outliers = 0
    if p25 is not None:
        fence = 1.5 * (p75 - p25)
        outliers = sum(1 for p in allp if p < p25 - fence or p > p75 + fence)
    kpi = {"count": sum(b["count"] for b in buckets.values()), "qty": round(qty, 4),
           "min": allp[0] if allp else None, "max": allp[-1] if allp else None,
           "p25": p25, "median": _quantile(allp, 0.5), "p75": p75, "outliers": outliers,
           "wavg": round(value / qty, 4) if qty else None}
    return series, kpi


def compute_stats(db: Session, f: dict, period: str, price_mode: str, unit: str = "") -> dict:
    """Biểu đồ + bảng theo kỳ của TẬP DÒNG ĐÃ LỌC, tách theo đơn vị tính.

    - Không cộng kg với lít: trả danh sách đơn vị kèm số dòng, vẽ MỘT đơn vị (mặc định
      đơn vị nhiều dòng nhất). ATRAZINE: KGM 60 · LTR 30 · TNE 2.
    - Kỳ ít hơn `MIN_LINES_FOR_BEST` dòng KHÔNG được gắn nhãn "kỳ giá tốt nhất": tháng 8
      của ATRAZINE "rẻ nhất" chỉ nhờ 3 dòng, tháng 5 gần ngang giá dựa trên 16 dòng.
    - Trả kèm ĐỘ PHỦ (bao nhiêu dòng, bao nhiêu tháng có dữ liệu, bao nhiêu năm) để màn
      hình và trợ lý AI nói ra độ tin cậy, không để người đọc tin quá mức.
    """
    if period not in PERIODS:
        raise HTTPException(400, "Kỳ gom phải là month, quarter hoặc year")
    if price_mode not in PRICE_MODES:
        raise HTTPException(400, "Giá phải là adjusted hoặc declared")
    if not has_chart_filter(f):
        raise HTTPException(400, NEED_FILTER_MSG)
    base = apply_line_filters(
        db.query(CustomsLine.reg_date, CustomsLine.unit_code, CustomsLine.price_usd,
                 CustomsLine.adj_price_usd, CustomsLine.quantity), f)
    rows = base.all()
    units = Counter(r.unit_code for r in rows)
    chosen = (unit or "").strip().upper() or (units.most_common(1)[0][0] if units else "")
    rows_u = [r for r in rows if r.unit_code == chosen]
    series, kpi = _aggregate(rows_u, period, price_mode)
    eligible = [s for s in series if s["wavg"] is not None and s["count"] >= MIN_LINES_FOR_BEST]
    best = min(eligible, key=lambda s: s["wavg"])["period"] if eligible else None
    months = {(r.reg_date.year, r.reg_date.month) for r in rows_u}
    years = {r.reg_date.year for r in rows_u}
    return {
        "period": period, "price_mode": price_mode, "unit": chosen,
        "units": [{"unit": u, "count": n} for u, n in units.most_common()],
        "series": series, "kpi": kpi, "best_period": best, "min_lines_for_best": MIN_LINES_FOR_BEST,
        "coverage": {"lines": len(rows_u), "months": len(months), "years": len(years),
                     "date_from": min(r.reg_date for r in rows_u).isoformat() if rows_u else None,
                     "date_to": max(r.reg_date for r in rows_u).isoformat() if rows_u else None,
                     "empty_periods": [s["label"] for s in series if s["count"] == 0]},
    }


def compare_terms(db: Session, terms: list[str], f: dict, period: str, price_mode: str, unit: str = "") -> dict:
    """So sánh 2–5 từ khóa trên cùng một biểu đồ (B-05). Dùng CHUNG một đơn vị — đơn vị
    nhiều dòng nhất trên tổng các từ khóa — không thì các đường không cùng thước đo."""
    terms = [t.strip() for t in terms if t and t.strip()][:5]
    if len(terms) < 2:
        raise HTTPException(400, "Cần ít nhất 2 từ khóa để so sánh")
    per_term = {}
    units = Counter()
    for t in terms:
        rows = apply_line_filters(
            db.query(CustomsLine.reg_date, CustomsLine.unit_code, CustomsLine.price_usd,
                     CustomsLine.adj_price_usd, CustomsLine.quantity), {**f, "q": t}).all()
        per_term[t] = rows
        units.update(r.unit_code for r in rows)
    chosen = (unit or "").strip().upper() or (units.most_common(1)[0][0] if units else "")
    out = []
    for t in terms:
        series, kpi = _aggregate([r for r in per_term[t] if r.unit_code == chosen], period, price_mode)
        out.append({"term": t, "series": series, "kpi": kpi})
    return {"period": period, "unit": chosen, "units": [{"unit": u, "count": n} for u, n in units.most_common()],
            "terms": out}


# ── Xếp hạng nhà nhập khẩu (T-05) ───────────────────────────────────────────
def rank_importers(db: Session, f: dict, unit: str = "", limit: int = 20) -> dict:
    """Ai đang nhập mặt hàng này. Gộp theo MÃ SỐ THUẾ (qua `importer_id`), không theo
    tên — cùng công ty có nhiều cách viết tên."""
    rows = apply_line_filters(
        db.query(CustomsLine.importer_id, CustomsLine.unit_code, CustomsLine.quantity,
                 CustomsLine.price_usd, CustomsLine.adj_price_usd, CustomsLine.reg_date), f).all()
    units = Counter(r.unit_code for r in rows)
    chosen = (unit or "").strip().upper() or (units.most_common(1)[0][0] if units else "")
    agg = defaultdict(lambda: {"count": 0, "qty": 0.0, "value": 0.0, "last": None})
    for r in rows:
        if r.unit_code != chosen:
            continue
        a = agg[r.importer_id]
        a["count"] += 1
        a["last"] = max(a["last"], r.reg_date) if a["last"] else r.reg_date
        p, qty = _price(r, "adjusted"), float(r.quantity or 0)
        if p is not None and qty > 0:
            a["qty"] += qty
            a["value"] += float(p) * qty
    top = sorted(agg.items(), key=lambda kv: (-kv[1]["qty"], -kv[1]["count"]))[:limit]
    parties = {p.id: p for p in db.query(CustomsParty).filter(CustomsParty.id.in_([k for k, _ in top]))}
    total_qty = sum(a["qty"] for a in agg.values()) or 0
    return {"unit": chosen, "units": [{"unit": u, "count": n} for u, n in units.most_common()],
            "total_importers": len(agg),
            "items": [{"importer_id": k, "name": parties[k].name if k in parties else "",
                       "tax_code": parties[k].tax_code if k in parties else "",
                       "count": a["count"], "qty": round(a["qty"], 4),
                       "share": round(a["qty"] / total_qty, 4) if total_qty else None,
                       "wavg": round(a["value"] / a["qty"], 4) if a["qty"] else None,
                       "last_date": a["last"].isoformat() if a["last"] else None} for k, a in top]}


# ── Thị trường: đối tác nước ngoài · nước xuất xứ · lô gần nhất (bao-CR-481) ──
def market_overview(db: Session, f: dict, unit: str = "", limit: int = 10, recent: int = 5) -> dict:
    """Cho trợ lý AI trả lời «ai nhập / mua của ai / từ nước nào / lô gần nhất giá bao nhiêu».

    Cùng bộ lọc với màn tra cứu (`apply_line_filters`) và cùng MỘT đơn vị tính (mặc định
    đơn vị nhiều dòng nhất) — gom kg với lít là ra thị phần vô nghĩa. Giá = giá điều chỉnh
    nếu có, không thì giá khai báo (như biểu đồ).
    """
    if not has_chart_filter(f):
        raise HTTPException(400, NEED_FILTER_MSG)
    importers = rank_importers(db, f, unit, limit=limit)
    chosen = importers["unit"]
    rows = apply_line_filters(
        db.query(CustomsLine.partner_id, CustomsLine.origin_country, CustomsLine.unit_code,
                 CustomsLine.quantity, CustomsLine.price_usd, CustomsLine.adj_price_usd), f).all()
    by_partner = defaultdict(lambda: {"count": 0, "qty": 0.0, "value": 0.0})
    by_origin = defaultdict(lambda: {"count": 0, "qty": 0.0, "value": 0.0})
    for r in rows:
        if r.unit_code != chosen:
            continue
        p, qty = _price(r, "adjusted"), float(r.quantity or 0)
        for bucket in (by_partner[r.partner_id], by_origin[(r.origin_country or "").strip() or "(không ghi)"]):
            bucket["count"] += 1
            if p is not None and qty > 0:
                bucket["qty"] += qty
                bucket["value"] += float(p) * qty
    total_qty = sum(b["qty"] for b in by_origin.values()) or 0

    def _rank(agg: dict) -> list[tuple]:
        return sorted(agg.items(), key=lambda kv: (-kv[1]["qty"], -kv[1]["count"]))[:limit]

    def _stats(b: dict) -> dict:
        return {"count": b["count"], "qty": round(b["qty"], 4),
                "share": round(b["qty"] / total_qty, 4) if total_qty else None,
                "wavg": round(b["value"] / b["qty"], 4) if b["qty"] else None}

    top_partners = _rank(by_partner)
    names = {p.id: p.name for p in db.query(CustomsParty).filter(
        CustomsParty.id.in_([k for k, _ in top_partners if k]))}
    unit_f = {**f, "unit": chosen} if chosen else f
    _, latest = list_lines(db, unit_f, 0, recent)
    return {
        "unit": chosen, "units": importers["units"],
        "importers": importers["items"], "total_importers": importers["total_importers"],
        "partners": [{"name": names.get(k, "") or "(không ghi đối tác)", **_stats(b)} for k, b in top_partners],
        "origins": [{"country": k, **_stats(b)} for k, b in _rank(by_origin)],
        "recent_lines": [{"date": x["reg_date"], "product_name": x["product_name"], "quantity": x["quantity"],
                          "unit": x["unit_code"], "price_usd": x["effective_price_usd"],
                          "origin": x["origin_country"], "partner": x["partner_name"],
                          "importer": x["importer_name"], "incoterm": x["incoterm"]} for x in latest],
    }


# ── Đánh giá THỜI ĐIỂM HIỆN TẠI cho câu «có nên mua lúc này» (bao-CR-481) ───
#  Dữ liệu cũ hơn chừng này ngày so với hôm nay thì phải nói ra — giá «hiện tại» khi đó
#  thật ra là giá của mấy tháng trước.
STALE_DATA_DAYS = 45


def assess_current_price(stats: dict, today: date | None = None) -> dict:
    """Đặt giá THÁNG GẦN NHẤT có dữ liệu cạnh cả năm: rẻ / trung bình / đắt, xu hướng 3 tháng.

    Chỉ nói điều số liệu nói được: mức giá NHẬP KHẨU của thị trường so với chính nó. Không
    biết tồn kho, nhu cầu, hạn dùng, dòng tiền của công ty — trợ lý phải nói rõ điều đó.
    Tháng gần nhất ít dòng (< MIN_LINES_FOR_BEST) thì vẫn trả nhưng gắn cờ `reliable=False`,
    kèm `reference_month` = tháng ĐỦ dữ liệu gần nhất để trợ lý có mốc đáng tin mà nói.
    Xu hướng cũng chỉ tính trên tháng đủ dữ liệu — một lô lẻ không được lật cả câu chuyện
    (dữ liệu thật 24/09: ATRAZINE 09/2026 chỉ 1 dòng mà suýt thành «đang giảm»).
    """
    today = today or date.today()
    months = [s for s in stats.get("series", []) if s.get("wavg") is not None]
    if not months:
        return {"available": False, "reason": "Không có tháng nào có giá để đánh giá."}
    latest = months[-1]
    base = [s for s in months if s["count"] >= MIN_LINES_FOR_BEST] or months
    solid_sorted = sorted(s["wavg"] for s in base)
    q1, q3 = _quantile(solid_sorted, 0.25), _quantile(solid_sorted, 0.75)

    def _level(price: float) -> str:
        return "thấp" if price <= q1 else "cao" if price >= q3 else "trung bình"

    price = latest["wavg"]
    level = _level(price)
    rank_pct = round(100 * sum(1 for v in solid_sorted if v < price) / len(solid_sorted))
    recent = [s["wavg"] for s in base[-3:]]
    if len(recent) >= 2 and recent[-1] > recent[0] * 1.03:
        trend = "đang tăng"
    elif len(recent) >= 2 and recent[-1] < recent[0] * 0.97:
        trend = "đang giảm"
    else:
        trend = "đi ngang" if len(recent) >= 2 else "chưa đủ tháng để nói xu hướng"
    date_to = (stats.get("coverage") or {}).get("date_to")
    age_days = (today - date.fromisoformat(date_to)).days if date_to else None
    reliable = latest["count"] >= MIN_LINES_FOR_BEST
    ref = base[-1]
    return {
        "available": True,
        "latest_month": latest["label"], "latest_wavg": price, "latest_count": latest["count"],
        "reliable": reliable,
        "reference_month": None if reliable or ref is latest else {
            "label": ref["label"], "wavg": ref["wavg"], "count": ref["count"], "price_level": _level(ref["wavg"])},
        #  % số tháng (đủ dữ liệu) có giá THẤP HƠN tháng gần nhất: 0 = đang rẻ nhất năm.
        "pct_months_cheaper": rank_pct, "price_level": level,
        "monthly_q1": q1, "monthly_median": _quantile(solid_sorted, 0.5), "monthly_q3": q3,
        "trend_3_months": trend,             # chỉ trên tháng ĐỦ dữ liệu
        "data_age_days": age_days,
        "stale": age_days is not None and age_days > STALE_DATA_DAYS,
    }


# ── Độ phủ dữ liệu, ô lọc, đối tượng ────────────────────────────────────────
def get_coverage(db: Session) -> dict:
    """Dải tháng đã phủ đầu trang — chặn lỗi quên nạp một tệp (04 §2)."""
    lo, hi, total = db.query(func.min(CustomsLine.reg_date), func.max(CustomsLine.reg_date),
                             func.count(CustomsLine.id)).one()
    #  Đếm theo tháng BẰNG SQL (GROUP BY năm, tháng) — trước đây kéo cả 18.243 ngày về Python,
    #  chậm dần theo số dòng mà đầu trang gọi nó mỗi lần mở màn.
    per_month = Counter()
    if total:
        y, m = extract("year", CustomsLine.reg_date), extract("month", CustomsLine.reg_date)
        for yy, mm, n in db.query(y, m, func.count(CustomsLine.id)).group_by(y, m):
            per_month[f"{int(yy)}-{int(mm):02d}"] = n
    last = (db.query(func.max(ImportBatch.finished_at))
            .filter(ImportBatch.module == ImportModule.CUSTOMS_DECLARATION,
                    ImportBatch.mode == ImportMode.APPLY, ImportBatch.status == ImportStatus.DONE).scalar())
    years = sorted({int(k[:4]) for k in per_month})
    return {"total": total, "date_from": lo.isoformat() if lo else None, "date_to": hi.isoformat() if hi else None,
            "last_import_at": last.isoformat() if last else None,
            "years": [{"year": y, "months": [per_month.get(f"{y}-{m:02d}", 0) for m in range(1, 13)]} for y in years]}


def list_options(db: Session) -> dict:
    def distinct(col, limit=200):
        rows = (db.query(col, func.count(CustomsLine.id)).filter(col != "")
                .group_by(col).order_by(func.count(CustomsLine.id).desc()).limit(limit).all())
        return [{"value": v, "count": n} for v, n in rows]
    #  bao-CR-493: lô nạp làm ô lọc «tệp nguồn» (sheet 4 mục 13) — chỉ lô ghi thật đã xong, mới nhất trước.
    batches = (db.query(ImportBatch.id, ImportBatch.filename, ImportBatch.created_count)
               .filter(ImportBatch.module == ImportModule.CUSTOMS_DECLARATION,
                       ImportBatch.mode == ImportMode.APPLY, ImportBatch.status == ImportStatus.DONE)
               .order_by(ImportBatch.id.desc()).limit(100).all())
    return {"hs_codes": distinct(CustomsLine.hs_code), "origins": distinct(CustomsLine.origin_country),
            "units": distinct(CustomsLine.unit_code), "ingredients": distinct(CustomsLine.active_ingredient, 300),
            "formulations": distinct(CustomsLine.formulation, 300),
            "currencies": distinct(CustomsLine.currency), "incoterms": distinct(CustomsLine.incoterm),
            "batches": [{"value": str(b.id), "label": f"#{b.id} {b.filename}", "count": b.created_count or 0}
                        for b in batches],
            "ingredient_coverage": _ingredient_coverage(db)}


def _ingredient_coverage(db: Session) -> dict:
    total = db.query(func.count(CustomsLine.id)).scalar() or 0
    tagged = db.query(func.count(CustomsLine.id)).filter(CustomsLine.active_ingredient != "").scalar() or 0
    return {"total": total, "tagged": tagged, "ratio": round(tagged / total, 4) if total else None}


def search_parties(db: Session, party_type: int, term: str, limit: int = 20) -> list[dict]:
    q = db.query(CustomsParty).filter(CustomsParty.party_type == party_type)
    if term.strip():
        like = f"%{term.strip()}%"
        q = q.filter(or_(CustomsParty.name.ilike(like), CustomsParty.tax_code.like(like)))
    return [{"id": p.id, "name": p.name, "tax_code": p.tax_code} for p in q.order_by(CustomsParty.name).limit(limit)]


# ── Xuất Excel (T-06) ───────────────────────────────────────────────────────
def export_lines_xlsx(db: Session, f: dict) -> bytes:
    import openpyxl
    q = apply_line_filters(db.query(CustomsLine), f)
    if q.count() > MAX_EXPORT_ROWS:
        raise HTTPException(400, f"Kết quả quá {MAX_EXPORT_ROWS:,} dòng — thu hẹp bộ lọc rồi xuất lại.".replace(",", "."))
    lines = serialize_lines(db, q.order_by(CustomsLine.reg_date.desc(), CustomsLine.id.desc()).all())
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tra cuu gia hai quan"
    header = [label for _, label in COLUMNS] + ["Hoạt chất (suy ra)", "Hàm lượng / dạng (suy ra)",
                                                 "Đơn giá quy đổi VND (thuế NK 7%)",
                                                 "Đơn giá quy đổi VND (theo thuế suất XNK)"]
    ws.append(header)
    for d in lines:
        row = [d.get("transport_label") if k == "transport_mode" else d.get(k) for k, _ in COLUMNS]
        ws.append(row + [d.get("active_ingredient"), d.get("formulation"),
                         d.get("price_vnd_flat"), d.get("price_vnd_line_tax")])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── Biểu thuế (P-04) ────────────────────────────────────────────────────────
def lookup_tariff(db: Session, hs_code: str) -> list[dict]:
    """Dòng biểu thuế của mã HS và các mã CHA (3808 → 380891 → 38089199), để thấy cả
    mô tả nhóm lẫn thuế suất của dòng lá."""
    code = "".join(ch for ch in (hs_code or "") if ch.isdigit())
    if len(code) < 4:
        raise HTTPException(400, "Mã HS phải có ít nhất 4 chữ số")
    prefixes = {code[:n] for n in (4, 6, 8) if len(code) >= n}
    rows = (db.query(CustomsTariff).filter(or_(CustomsTariff.hs_code.in_(prefixes),
                                               CustomsTariff.hs_code.like(f"{code}%")))
            .order_by(CustomsTariff.hs_code).limit(60).all())
    return [{"hs_code": r.hs_code, "name_vn": r.name_vn, "name_en": r.name_en, "unit": r.unit,
             "rate_normal": r.rate_normal, "rate_mfn": r.rate_mfn, "rate_vat": r.rate_vat,
             "fta": json.loads(r.fta_json or "{}"), "policy": r.policy} for r in rows]


# ── Pháp lý (P-03 tra cứu, cảnh báo theo từ khóa) ───────────────────────────
def _obligation(r: CustomsRegulation) -> str:
    """Câu nói việc cần lưu ý — chỉ nói những gì dữ liệu nguồn nói, không suy diễn pháp lý."""
    if r.list_code == RegulationList.BANNED_TT75:
        return f"Hoạt chất CẤM{f' từ năm {r.banned_year}' if r.banned_year else ''} ({r.legal_basis or 'TT 75/2025/TT-BNNMT'})."
    if r.list_code == RegulationList.ND24_PL4 and r.threshold_kg is not None:
        return f"Có NGƯỠNG KHỐI LƯỢNG {float(r.threshold_kg):g} kg theo {r.legal_basis}."
    if r.list_code == RegulationList.PUBLISH_TT01:
        return "Phải công bố hóa chất nguy hiểm theo từng lô nhập trên chemicaldata.gov.vn (TT 01/2026/TT-BCT Phụ lục XIX)."
    return f"Có trong {r.legal_basis}{f' — {r.category}' if r.category else ''}."


def _regulation_out(r: CustomsRegulation) -> dict:
    return {"id": r.id, "list_code": r.list_code,
            "list_label": REGULATION_LIST_LABELS.get(RegulationList(r.list_code), "") if r.list_code in
            {int(x) for x in RegulationList} else "",
            "name": r.name, "name_vi": r.name_vi, "cas_no": r.cas_no, "category": r.category,
            "threshold_kg": _num(r.threshold_kg), "banned_year": r.banned_year,
            "legal_basis": r.legal_basis, "note": r.note, "obligation": _obligation(r)}


def lookup_regulations(db: Session, term: str, limit: int = 50) -> dict:
    """Tra theo tên / số CAS / công thức hóa học (`H2SO4` → CAS 7664-93-9)."""
    t = (term or "").strip()
    if len(t) < 2:
        raise HTTPException(400, "Nhập ít nhất 2 ký tự: tên hóa chất, số CAS hoặc công thức")
    cas = FORMULA_CAS.get(t.upper().replace(" ", ""), "")
    like = f"%{t}%"
    conds = [CustomsRegulation.name.ilike(like), CustomsRegulation.name_vi.ilike(like), CustomsRegulation.cas_no == t]
    if cas:
        conds.append(CustomsRegulation.cas_no == cas)
    rows = (db.query(CustomsRegulation).filter(CustomsRegulation.is_active.is_(True), or_(*conds))
            .order_by(CustomsRegulation.list_code, CustomsRegulation.name).limit(limit).all())
    return {"term": t, "formula_cas": cas or None, "items": [_regulation_out(r) for r in rows]}


def match_alerts(db: Session, f: dict) -> list[dict]:
    """Cảnh báo pháp lý cho TỪ KHÓA đang tra — hoạt chất cấm, hóa chất có ngưỡng khối lượng,
    hóa chất phải công bố — hiện ngay trên màn tra cứu lúc thu mua đang tính chuyện mua.

    Không so với tồn kho (P-02 cần cầu nối vật tư ↔ hoạt chất, đại ca để sau); đây là
    cảnh báo LÚC LÊN KẾ HOẠCH MUA, dựa trên chính cái tên đang tra.
    """
    term = (f.get("q") or f.get("ingredient") or "").strip()
    if len(term) < 3:
        return []
    watch = (RegulationList.BANNED_TT75, RegulationList.ND24_PL4, RegulationList.PUBLISH_TT01)
    rows = (db.query(CustomsRegulation)
            .filter(CustomsRegulation.is_active.is_(True), CustomsRegulation.list_code.in_([int(x) for x in watch]))
            .all())
    norm = reader.normalize_text(term)
    out = []
    for r in rows:
        name = reader.normalize_text(r.name)
        head = name.split(" (")[0].split(",")[0].strip()
        if norm in name or (len(head) >= 4 and head in norm) or term == r.cas_no:
            out.append(_regulation_out(r))
    return out
