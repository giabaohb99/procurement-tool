"""Đối chiếu HÓA ĐƠN NCC với lần giao / dòng ĐMH và công nợ khi soạn nháp `draft_po_receipt` (ai-CR-239).

Người dùng gửi ảnh hóa đơn; AI đọc các số trên hóa đơn (tiền trước thuế, VAT % / tiền VAT, tổng tiền, tùy chọn từng dòng
hàng: tên, ĐVT, SL, đơn giá) và truyền vào `draft_po_receipt` cùng số + ngày hóa đơn (ai-CR-237). Ở đây MÁY tự cộng các
lần giao của nháp theo đơn giá × tỷ giá và % VAT của dòng ĐMH — đúng công thức sinh công nợ hàng
(`purchase_order.delivery_service._post_received_delivery`) — rồi báo khớp hay lệch bao nhiêu, thay cho việc AI cộng tay.

- Ngưỡng làm tròn: tiền ±`MONEY_TOLERANCE` đồng; đơn giá ±`PRICE_TOLERANCE_RATIO` (hóa đơn làm tròn đơn giá về đồng, ĐMH
  giữ 4 số lẻ); % VAT phải bằng đúng; SL lệch quá `QTY_TOLERANCE`.
- Hóa đơn GỘP BỘ: một dòng hóa đơn ứng với nhiều dòng ĐMH (chai + nắp) → so SL bộ với SL từng dòng (tỷ lệ bộ) và đơn giá
  bộ với tổng đơn giá các dòng thành phần.
- Công nợ hàng của các lần giao (id, đã trả, còn phải trả) chỉ kèm khi người hỏi được xem công nợ, qua `apply_scope`;
  để AI gợi ý bước kế là `draft_payment_request` với đúng `payable_ids`.

CHỈ CẢNH BÁO: không chặn soạn / ghi, không ghi gì, không vào `draft` (xác nhận vẫn ghi đúng như ai-CR-237).
"""
from __future__ import annotations

import re

from app.core.scoping import apply_scope
from app.modules.purchase_order.model import POItem

from .base import ToolContext

MONEY_TOLERANCE = 1000.0          # đồng — lệch làm tròn chấp nhận được của tiền trước thuế / VAT / tổng
PRICE_TOLERANCE_RATIO = 0.005     # 0,5% — đơn giá trên hóa đơn làm tròn về đồng
QTY_TOLERANCE = 0.001
MAX_INVOICE_LINES = 50
MAX_MONEY = 1e13
CURRENCY = "VND"
FIGURE_KEYS = ("invoice_amount", "invoice_vat_rate", "invoice_vat_amount", "invoice_total", "invoice_lines")
_VN_GROUPED = re.compile(r"^\d{1,3}(\.\d{3})+(,\d+)?$")       # 12.125.000 / 12.125.000,5
_EN_GROUPED = re.compile(r"^\d{1,3}(,\d{3})+(\.\d+)?$")       # 12,125,000 / 12,125,000.5
_MONEY_JUNK = re.compile(r"(?i)\s|vn[dđ]|đồng|đ|%")


def _vn(v) -> str:
    from .po_receipt_tool import vn

    return vn(v)


def _fold(v) -> str:
    from app.modules.assistant.glossary import fold

    return " ".join(fold(str(v or "")).split())


def parse_money(v) -> float | None:
    """Số tiền / đơn giá / SL trên hóa đơn: số, hoặc chuỗi kiểu Việt "12.125.000" / "2.425" (nghìn) / "12,5" (lẻ), kiểu
    Anh "12,125,000.00". Bỏ chữ đ / VND / %. Sai / âm → None."""
    if isinstance(v, bool) or v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        n = float(v)
    else:
        s = _MONEY_JUNK.sub("", str(v))[:40]
        if _VN_GROUPED.match(s):
            s = s.replace(".", "").replace(",", ".")
        elif _EN_GROUPED.match(s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
        try:
            n = float(s)
        except ValueError:
            return None
    return round(n, 4) if 0 <= n < MAX_MONEY else None


def parse_vat_rate(v) -> float | None:
    """% VAT: 8 / "8%" / 0,08 (phần thập phân → %). Ngoài 0..100 → None."""
    n = parse_money(v)
    if n is None:
        return None
    if 0 < n < 1:
        n *= 100
    return round(n, 2) if n <= 100 else None


def has_figures(args: dict) -> bool:
    return any(args.get(k) not in (None, "", []) for k in FIGURE_KEYS)


# ── đọc số trên hóa đơn ───────────────────────────────────────────────────────────────────
def _read_figures(args: dict, notes: list[str]) -> dict:
    """Các số người dùng / AI đọc trên hóa đơn. Số sai dạng: ghi vào `notes`, bỏ qua (không chặn)."""
    labels = {"invoice_amount": "tiền trước thuế", "invoice_vat_amount": "tiền VAT", "invoice_total": "tổng tiền",
              "invoice_vat_rate": "% VAT"}
    out: dict = {}
    for key, label in labels.items():
        raw = args.get(key)
        if raw in (None, ""):
            continue
        val = parse_vat_rate(raw) if key == "invoice_vat_rate" else parse_money(raw)
        if val is None:
            notes.append(f"Không đọc được {label} trên hóa đơn **{str(raw)[:40]}** — bỏ qua số này khi đối chiếu.")
        else:
            out[key] = val
    raw_lines = args.get("invoice_lines")
    lines = []
    for i, ln in enumerate((raw_lines if isinstance(raw_lines, list) else [])[:MAX_INVOICE_LINES], 1):
        if not isinstance(ln, dict):
            continue
        qty, price, amount = parse_money(ln.get("qty")), parse_money(ln.get("unit_price")), parse_money(ln.get("amount"))
        if price is None and amount is not None and qty:
            price = round(amount / qty, 4)
        if amount is None and price is not None and qty is not None:
            amount = round(qty * price, 2)
        if not qty:
            notes.append(f"Dòng {i} của hóa đơn thiếu / sai số lượng — bỏ qua dòng này khi so từng dòng.")
            continue
        lines.append({"no": i, "name": " ".join(str(ln.get("name") or "").split())[:255],
                      "unit": " ".join(str(ln.get("unit") or "").split())[:25], "qty": qty, "unit_price": price,
                      "amount": amount})
    if isinstance(raw_lines, list) and len(raw_lines) > MAX_INVOICE_LINES:
        notes.append(f"Hóa đơn quá {MAX_INVOICE_LINES} dòng — chỉ so {MAX_INVOICE_LINES} dòng đầu.")
    out["lines"] = lines
    return out


def _resolve_totals(fig: dict, notes: list[str]) -> dict:
    """Tiền trước thuế A, VAT V, tổng T của hóa đơn: số nào thiếu thì suy từ số khác (đánh dấu suy ra). Kiểm hóa đơn tự
    cộng có khớp không."""
    a, v, t, rate = (fig.get(k) for k in ("invoice_amount", "invoice_vat_amount", "invoice_total", "invoice_vat_rate"))
    if a is not None and v is not None and t is not None and abs(a + v - t) > MONEY_TOLERANCE:
        notes.append(f"Hóa đơn tự cộng không khớp: {_vn(a)} + VAT {_vn(v)} = {_vn(a + v)} nhưng tổng ghi {_vn(t)} — đọc "
                     "lại ảnh hóa đơn.")
    if a is not None and v is not None and rate is not None and abs(a * rate / 100 - v) > MONEY_TOLERANCE:
        notes.append(f"Tiền VAT trên hóa đơn {_vn(v)} không bằng {_vn(rate)}% của {_vn(a)} ({_vn(a * rate / 100)}).")
    if v is None and a is not None and rate is not None:
        v = round(a * rate / 100, 2)
    if v is None and a is not None and t is not None:
        v = round(t - a, 2)
    if a is None and t is not None and v is not None:
        a = round(t - v, 2)
    if a is None and t is not None and rate is not None:
        a = round(t / (1 + rate / 100), 2)
        v = round(t - a, 2)
    if t is None and a is not None and v is not None:
        t = round(a + v, 2)
    return {"amount": a, "vat": v, "total": t, "vat_rate": rate}


# ── phía ĐMH ───────────────────────────────────────────────────────────────────────────────
def _row_qty(r: dict) -> float:
    """SL của lần giao SAU khi ghi: lần nhận mới / sửa = `qty`; chế độ chỉ ghi hóa đơn = SL đã nhận."""
    return float(r.get("received_qty") or 0) if r.get("op") == "invoice" else float(r.get("qty") or 0)


def _targets(ctx: ToolContext, rows: list[dict]) -> list[dict]:
    """Gộp các dòng nháp theo dòng ĐMH, kèm đơn giá quy đổi + % VAT của dòng (dòng đã lọc phạm vi ghi khi soạn nháp)."""
    from app.modules.purchase_order.base_service import rate_of

    ids = sorted({int(r["po_item_id"]) for r in rows})
    items = {it.id: it for it in ctx.db.query(POItem).filter(POItem.id.in_(ids or [0]))}
    out: dict[int, dict] = {}
    for r in rows:
        it = items.get(int(r["po_item_id"]))
        if it is None:
            continue
        rate = rate_of(it)
        t = out.setdefault(it.id, {
            "po_code": r.get("po_code") or "", "po_item_id": it.id, "product_code": (it.product_code or "").strip(),
            "product_name": it.product_name or "", "invoice_name": it.invoice_name or "", "unit": it.unit or "",
            "currency": it.currency or CURRENCY, "unit_price": round(float(it.price or 0) * rate, 4),
            "vat_rate": round(float(it.vat or 0), 2), "qty": 0.0})
        t["qty"] = round(t["qty"] + _row_qty(r), 3)
    for t in out.values():
        t["amount"] = round(t["qty"] * t["unit_price"], 2)
        t["vat"] = round(t["amount"] * t["vat_rate"] / 100, 2)
    return list(out.values())


def _diff(field: str, label: str, invoice: float, expected: float, where: str = "") -> dict:
    return {"field": field, "label": label, "where": where, "invoice": round(invoice, 4), "expected": round(expected, 4),
            "diff": round(invoice - expected, 4)}


def _money_off(a: float, b: float) -> bool:
    return abs(a - b) > MONEY_TOLERANCE


def _price_off(a: float, b: float) -> bool:
    return abs(a - b) > max(PRICE_TOLERANCE_RATIO * abs(b), 0.01)


# ── ghép dòng hóa đơn ↔ dòng ĐMH ───────────────────────────────────────────────────────────
def _name_hits(line: dict, targets: list[dict]) -> list[dict]:
    name = _fold(line["name"])
    if len(name) < 3:
        return []
    hits = []
    for t in targets:
        code = _fold(t["product_code"])
        names = [n for n in (_fold(t["invoice_name"]), _fold(t["product_name"])) if len(n) >= 4]
        if (code and code in name) or any(n in name or name in n for n in names):
            hits.append(t)
    return hits


def _pair_lines(lines: list[dict], targets: list[dict]) -> tuple[list[tuple[dict, dict]], list[tuple[dict, list]], list]:
    """(cặp 1-1, bộ gộp (dòng HĐ, các dòng ĐMH), dòng HĐ không ghép được)."""
    pairs: list[tuple[dict, dict]] = []
    used: set[int] = set()
    left = []
    for ln in lines:                                    # 1. theo tên / mã hàng, chỉ khi trúng đúng một dòng
        hits = [t for t in _name_hits(ln, targets) if t["po_item_id"] not in used]
        if len(hits) == 1:
            pairs.append((ln, hits[0]))
            used.add(hits[0]["po_item_id"])
        else:
            left.append(ln)
    rest = [t for t in targets if t["po_item_id"] not in used]
    kits: list[tuple[dict, list]] = []
    if len(left) == 1 and len(rest) >= 2:               # 2. một dòng HĐ còn lại ↔ nhiều dòng ĐMH = hóa đơn gộp bộ
        return pairs, [(left[0], rest)], []
    unmatched = []
    for ln in left:                                     # 3. theo SL bằng nhau (duy nhất), rồi theo thứ tự
        same = [t for t in rest if abs(t["qty"] - ln["qty"]) <= QTY_TOLERANCE]
        pick = same[0] if len(same) == 1 else (rest[0] if len(left) == len(rest) and rest else None)
        if pick is None:
            unmatched.append(ln)
            continue
        pairs.append((ln, pick))
        rest.remove(pick)
    return pairs, kits, unmatched


def _check_pair(ln: dict, t: dict, diffs: list[dict]) -> dict:
    where = f"dòng {ln['no']} hóa đơn ↔ {t['po_code']} · {t['product_code']}"
    if abs(ln["qty"] - t["qty"]) > QTY_TOLERANCE:
        diffs.append(_diff("qty", "số lượng", ln["qty"], t["qty"], where))
    if ln["unit_price"] is not None and _price_off(ln["unit_price"], t["unit_price"]):
        diffs.append(_diff("unit_price", "đơn giá", ln["unit_price"], t["unit_price"], where))
    return {"invoice_line": ln["no"], "name": ln["name"], "po_code": t["po_code"], "product_code": t["product_code"],
            "qty": ln["qty"], "expected_qty": t["qty"], "unit_price": ln["unit_price"],
            "expected_unit_price": t["unit_price"]}


def _check_kit(ln: dict, parts: list[dict], diffs: list[dict]) -> dict:
    """Một dòng HĐ = một BỘ gồm nhiều dòng ĐMH: SL bộ × tỷ lệ = SL từng dòng, đơn giá bộ = Σ đơn giá × tỷ lệ."""
    q = ln["qty"]
    comps = []
    for t in parts:
        ratio = round(t["qty"] / q, 4) if q else 0
        comps.append({"po_code": t["po_code"], "product_code": t["product_code"], "product_name": t["product_name"],
                      "qty": t["qty"], "ratio": int(ratio) if float(ratio).is_integer() else ratio,
                      "unit_price": t["unit_price"]})
        if ratio <= 0 or abs(ratio - round(ratio)) > QTY_TOLERANCE:
            diffs.append(_diff("qty", "số lượng bộ", q, t["qty"],
                               f"dòng {ln['no']} hóa đơn ({_vn(q)} {ln['unit'] or 'bộ'}) ↔ {t['po_code']} · "
                               f"{t['product_code']} ({_vn(t['qty'])} {t['unit']}) — không ra tỷ lệ bộ nguyên"))
    kit_price = round(sum(t["amount"] for t in parts) / q, 4) if q else 0.0
    if ln["unit_price"] is not None and _price_off(ln["unit_price"], kit_price):
        diffs.append(_diff("unit_price", "đơn giá bộ", ln["unit_price"], kit_price,
                           f"dòng {ln['no']} hóa đơn ↔ bộ {' + '.join(t['product_code'] for t in parts)}"))
    return {"invoice_line": ln["no"], "name": ln["name"], "unit": ln["unit"], "qty": q, "unit_price": ln["unit_price"],
            "expected_unit_price": kit_price, "components": comps}


# ── công nợ ────────────────────────────────────────────────────────────────────────────────
def _payables(ctx: ToolContext, rows: list[dict], out: dict) -> None:
    from app.modules.payable.model import Payable
    from app.modules.payable.service import status_label

    dids = sorted({int(r.get("delivery_id") or 0) for r in rows} - {0})
    if not ctx.can("payable"):
        out["payable_note"] = "Không kèm công nợ vì người hỏi không có quyền xem công nợ."
        return
    q = apply_scope(ctx.db.query(Payable), Payable, "payable", ctx.user, ctx.profile)
    pays = (q.filter(Payable.source_type == "goods", Payable.ref_type == "delivery", Payable.ref_id.in_(dids or [0]))
            .order_by(Payable.id).all())
    out["payables"] = [{"payable_id": p.id, "delivery_id": p.ref_id, "po_code": p.po_code or "",
                        "invoice_no": p.invoice_no or "", "amount": round(float(p.amount or 0), 2),
                        "vat": round(float(p.vat or 0), 2), "total": round(float(p.total or 0), 2),
                        "paid": round(float(p.paid_amount or 0), 2), "remaining": round(float(p.remaining or 0), 2),
                        "status": p.status or "", "status_label": status_label(p.status), "currency": CURRENCY}
                       for p in pays]
    out["payables_remaining"] = round(sum(x["remaining"] for x in out["payables"]), 2)
    out["payable_ids"] = [x["payable_id"] for x in out["payables"] if x["remaining"] > 0]
    #  Lần nhận mới / sửa SL: công nợ hàng sinh (hoặc tính lại) khi xác nhận nháp — số hiện có chưa phải số sau khi ghi.
    out["pending_payables"] = sum(1 for r in rows if r.get("op") != "invoice")


def _next_step(out: dict) -> str:
    if out.get("pending_payables"):
        return ("Công nợ hàng của lần nhận sinh ra khi người dùng xác nhận nháp (confirm_draft kind=po_receipt), đúng bằng "
                "số `expected`. Sau đó muốn lập đề nghị thanh toán thì gọi payable_lookup theo NCC / số hóa đơn rồi "
                "draft_payment_request với payable_ids của các khoản đó.")
    if out.get("payable_ids"):
        return (f"Sau khi ghi số hóa đơn, gợi ý người dùng lập đề nghị thanh toán: draft_payment_request với payable_ids = "
                f"{out['payable_ids']} (còn phải trả {_vn(out['payables_remaining'])} {CURRENCY}).")
    if "payables" in out:
        return "Các khoản công nợ của lần giao này đã trả hết — không cần lập đề nghị thanh toán."
    return ""


# ── chính ──────────────────────────────────────────────────────────────────────────────────
def reconcile(ctx: ToolContext, rows: list[dict], args: dict) -> dict | None:
    """Đối chiếu hóa đơn với các dòng nháp. Không có số nào trên hóa đơn → None (không đối chiếu)."""
    if not has_figures(args) or not rows:
        return None
    notes: list[str] = []
    fig = _read_figures(args, notes)
    inv = _resolve_totals(fig, notes)
    targets = _targets(ctx, rows)
    exp_amount = round(sum(t["amount"] for t in targets), 2)
    exp_vat = round(sum(t["vat"] for t in targets), 2)
    expected = {"amount": exp_amount, "vat": exp_vat, "total": round(exp_amount + exp_vat, 2)}
    diffs: list[dict] = []
    compared = False
    for key, label in (("amount", "tiền trước thuế"), ("vat", "tiền VAT"), ("total", "tổng tiền")):
        if inv[key] is not None:
            compared = True
            if _money_off(inv[key], expected[key]):
                diffs.append(_diff(key, label, inv[key], expected[key]))
    if inv["vat_rate"] is not None:
        compared = True
        for t in targets:
            if abs(t["vat_rate"] - inv["vat_rate"]) > 0.001:
                diffs.append(_diff("vat_rate", "% VAT", inv["vat_rate"], t["vat_rate"], f"{t['po_code']} · "
                                                                                         f"{t['product_code']}"))
    pairs, kits, unmatched = _pair_lines(fig["lines"], targets)
    compared = compared or bool(pairs or kits)
    out: dict = {"currency": CURRENCY, "expected": expected,
                 "invoice": {k: inv[k] for k in ("amount", "vat", "total", "vat_rate")},
                 "po_lines": [{k: t[k] for k in ("po_code", "product_code", "product_name", "unit", "qty", "unit_price",
                                                 "vat_rate", "amount", "vat")} for t in targets],
                 "lines": [_check_pair(ln, t, diffs) for ln, t in pairs],
                 "kits": [_check_kit(ln, parts, diffs) for ln, parts in kits]}
    for ln in unmatched:
        notes.append(f"Dòng {ln['no']} hóa đơn ({ln['name'] or 'không tên'}, {_vn(ln['qty'])} {ln['unit']}) không ghép "
                     "được với dòng ĐMH nào của nháp — có thể hóa đơn gồm cả lần giao khác chưa nêu.")
    if any(t["currency"] != CURRENCY for t in targets):
        notes.append("Có dòng ĐMH ngoại tệ: đã so theo số quy đổi VNĐ (đơn giá × tỷ giá của dòng), như công nợ.")
    out["diffs"] = diffs
    out["status"] = "mismatch" if diffs else ("match" if compared else "unchecked")
    out["status_label"] = {"match": "Khớp", "mismatch": "Lệch", "unchecked": "Chưa đối chiếu được"}[out["status"]]
    out["notes"] = notes
    out["tolerance"] = {"money": MONEY_TOLERANCE, "unit_price_ratio": PRICE_TOLERANCE_RATIO}
    _payables(ctx, rows, out)
    out["next_step"] = _next_step(out)
    out["summary"] = _summary(out)
    return out


def _summary(out: dict) -> str:
    e = out["expected"]
    head = (f"{out['status_label']}: theo ĐMH {_vn(e['amount'])} + VAT {_vn(e['vat'])} = {_vn(e['total'])} {CURRENCY}"
            + (f"; hóa đơn ghi tổng {_vn(out['invoice']['total'])}" if out["invoice"]["total"] is not None else "") + ".")
    for k in out["kits"]:
        head += (f" Hóa đơn ghi GỘP BỘ: dòng {k['invoice_line']} {_vn(k['qty'])} {k['unit'] or 'bộ'} ứng với "
                 f"{len(k['components'])} dòng ĐMH ({' + '.join(c['product_code'] for c in k['components'])}), đơn giá bộ "
                 f"theo ĐMH {_vn(k['expected_unit_price'])}.")
    return head


def warnings_of(check: dict | None) -> list[str]:
    """Câu cảnh báo cho mảng `warnings` của nháp: mỗi chỗ lệch một câu có số lệch."""
    if not check:
        return []
    out = []
    for d in check["diffs"]:
        unit = "%" if d["field"] == "vat_rate" else ("" if d["field"] == "qty" else f" {CURRENCY}")
        where = f" ({d['where']})" if d["where"] else ""
        out.append(f"HÓA ĐƠN LỆCH {d['label']}{where}: hóa đơn {_vn(d['invoice'])}{unit}, theo ĐMH {_vn(d['expected'])}"
                   f"{unit}, lệch {'+' if d['diff'] > 0 else ''}{_vn(d['diff'])}{unit}. Chỉ là cảnh báo — hỏi người dùng "
                   "có ghi không.")
    return out + list(check["notes"])


NOTE = ("Đọc người dùng `invoice_check.summary` và từng dòng HÓA ĐƠN LỆCH (nếu có) — máy đã tự cộng, KHÔNG tự cộng lại. "
        "Lệch chỉ là cảnh báo: người dùng vẫn quyết ghi hay không. Có `invoice_check.next_step` thì gợi ý bước kế đó.")
