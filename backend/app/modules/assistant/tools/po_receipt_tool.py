"""Ghi LẦN NHẬN HÀNG vào Đơn mua hàng từ phiếu xuất kho giấy của NCC (bao-CR-740).

Luồng: người dùng gửi ẢNH phiếu xuất kho cho ứng dụng AI (Claude / ChatGPT qua cổng MCP, Trợ lý web). AI tự bóc NCC,
ngày, số phiếu, các dòng mã hàng + tổng SL rồi gọi `draft_po_receipt`: tool đề xuất chia vào các dòng ĐMH còn thiếu (tạo
lần giao mới hoặc điền lần giao đang chờ), KHÔNG ghi gì. Người dùng sửa (gọi lại tool với số / chỉ định mới) hoặc gật →
`confirm_draft` kind=`po_receipt` → `confirm_receipt` ghi bằng ĐÚNG service lưu ĐMH của màn web (`update_po` →
`_save_deliveries` + `recompute_effects`: phiếu nhập kho ngầm, tồn kho, công nợ; rồi tiến độ dòng + đồng bộ YCMH).
`po_open_lines` cho AI xem các dòng còn thiếu kèm các lần giao để giải thích.

Luật chia (chủ hệ thống chốt 07/11/2026):
1. Chỉ ĐMH đã duyệt trở đi còn mở (`STATUS_AFTER_APPROVE` trừ Hoàn thành), dòng chưa Hoàn thành / Hủy, còn thiếu > 0.
2. Đơn chứa NHIỀU mã của phiếu (chai + nắp cùng đơn) xét trước, cùng mức thì đơn cũ trước. Mã ít đơn chứa chia trước;
   mã đi kèm chia sau theo tỷ lệ bộ trong đơn (nắp giao 504 cho đơn còn 500 chai + 500 nắp → chai của đơn đó cũng 504).
3. Giao dư không chặn: phần vượt tổng còn thiếu dồn vào dòng chia sau cùng của mã đó, có cảnh báo.
4. Dòng có lần giao đang chờ (chưa nhận) mà SL gửi khớp số chia → đề xuất điền lần đó thay vì tạo lần mới.
5. Sửa lần giao chỉ đổi SL nhận / ngày nhận (+ kho nhận, SL gửi nếu người dùng nêu); không xóa lần giao qua AI (xóa gỡ
   phiếu nhập kho / công nợ — làm trên màn ĐMH).

Quyền: đọc cần `purchase_order.read` + `supplier.read` (phiếu nêu tên NCC — cùng luật ẩn NCC của các tool thu mua), chỉ
ĐMH trong phạm vi đọc. Soạn nháp cần thêm `purchase_order.write`, chỉ chia vào ĐMH trong phạm vi GHI. Lúc xác nhận kiểm
lại quyền + phạm vi `write` (đúng action của `PATCH /api/purchase-orders/{id}`) cho TỪNG ĐMH, và chặn khi dòng / lần giao
đã đổi sau lúc soạn (xác nhận hai lần không ghi đôi). Không trả giá.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date

from sqlalchemy import or_

from app.core.scoping import apply_scope
from app.core.status_codes import PO_DELIVERY_STATUS
from app.modules.purchase_order.model import STATUS_AFTER_APPROVE, PODelivery, POItem, PurchaseOrder

from .base import ToolContext, ToolSpec, denied

KIND = "po_receipt"
OPEN_PO_STATUSES = tuple(s for s in STATUS_AFTER_APPROVE if s != "completed")
CLOSED_LINE_PROGRESS = ("completed", "cancelled")   # = base_service.PROG_COMPLETED / PROG_CANCELLED (_save_items khóa)
EPS = 0.001
MAX_LINES = 50
MAX_ASSIGN = 20
MAX_QTY = 1e9
PAGE_MAX = 200
PAGE_DEFAULT = 50
PO_URL = "/procurement/purchase-orders/{id}"
_STATUS_LABELS = {"approved": "Đã duyệt", "partial": "Đã nhận một phần", "received": "Đã nhận đủ",
                  "processing": "Đang xử lý", "completed": "Hoàn thành"}
_LEGAL = re.compile(r"\b(cong ty|cty|ctcp|tnhh|co phan|mot thanh vien|mtv|trach nhiem huu han|chi nhanh|cn)\b")
_DATE_VN = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$")
_THOUSANDS = re.compile(r"^\d{1,3}([.,]\d{3})+$")


# ── tiện ích ─────────────────────────────────────────────────────────────────────────────
def _fold(v) -> str:
    from app.modules.assistant.glossary import fold

    return fold(str(v or ""))


def _text(v, limit: int = 255) -> str:
    return " ".join(str(v or "").split())[:limit]


def _code(v) -> str:
    return _text(v, 50).upper()


def _num(v) -> float:
    return round(float(v or 0), 3)


def vn(v) -> str:
    """Số kiểu Việt cho câu chữ: 1000000 → "1.000.000", 12.5 → "12,5" (bỏ ,0 thừa, tối đa 3 số lẻ)."""
    try:
        n = round(float(v or 0), 3)
    except (TypeError, ValueError):
        return str(v)
    whole, _, frac = f"{abs(n):,.3f}".partition(".")
    frac = frac.rstrip("0")
    return ("-" if n < 0 else "") + whole.replace(",", ".") + ("," + frac if frac else "")


def parse_qty(v) -> float | None:
    """Số lượng trên phiếu: số, hoặc chuỗi kiểu Việt "3.780" / "3,780" (nghìn) / "12,5" (lẻ). Sai / ≤ 0 → None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        n = float(v)
    else:
        s = str(v or "").strip().replace(" ", "")
        if _THOUSANDS.match(s):
            s = s.replace(".", "").replace(",", "")
        else:
            s = s.replace(",", ".")
        try:
            n = float(s)
        except ValueError:
            return None
    return round(n, 3) if EPS <= n < MAX_QTY else None


def parse_date(v) -> str:
    """YYYY-MM-DD hoặc DD/MM/YYYY → YYYY-MM-DD; sai → ''."""
    s = _text(v, 20)
    m = _DATE_VN.match(s)
    try:
        if m:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        return date.fromisoformat(s[:10]).isoformat() if len(s) >= 10 else ""
    except ValueError:
        return ""


def _core_name(name: str) -> str:
    return " ".join(_LEGAL.sub(" ", _fold(name)).split())


# ── dữ liệu ──────────────────────────────────────────────────────────────────────────────
def _scoped_open_pos(ctx: ToolContext, action: str):
    q = apply_scope(ctx.db.query(PurchaseOrder), PurchaseOrder, "purchase_order", ctx.user, ctx.profile, action)
    return q.filter(PurchaseOrder.status.in_(OPEN_PO_STATUSES))


def _resolve_supplier(ctx: ToolContext, raw) -> tuple[tuple[str, str] | None, dict | None]:
    """NCC theo mã / MST / tên (khớp mờ, bỏ dấu, bỏ chữ "Công ty TNHH"…) — CHỈ trong các NCC có ĐMH mở mà người hỏi
    được xem, nên không lộ NCC ngoài phạm vi."""
    from app.modules.supplier.model import Supplier

    want = _text(raw)
    if not want:
        return None, {"error": "Thiếu tên hoặc mã NCC (ghi trên phiếu xuất kho)."}
    rows = (_scoped_open_pos(ctx, "read").with_entities(PurchaseOrder.supplier_code, PurchaseOrder.supplier_name)
            .distinct().all())
    names: dict[str, str] = {}
    for code, name in rows:
        if code:
            names.setdefault(code, name or "")
    taxes = dict(ctx.db.query(Supplier.code, Supplier.tax_code).filter(Supplier.code.in_(list(names) or [""])).all())
    up, core = want.upper(), _core_name(want)
    hit = [c for c in names if c.upper() == up or (taxes.get(c) or "").strip() == want]
    if not hit and len(core) >= 3:
        hit = [c for c, n in names.items() if core in _core_name(n) or (len(_core_name(n)) >= 3 and _core_name(n) in core)]
    if len(hit) == 1:
        return (hit[0], names[hit[0]]), None
    if not hit:
        return None, {"error": f"Không thấy ĐMH đang mở (đã duyệt, còn thiếu hàng) nào của NCC khớp **{want}** trong "
                               "phạm vi bạn được xem. Hỏi lại người dùng tên / mã NCC đúng như trên ERP."}
    return None, {"need_choice": "nhà cung cấp", "options": [f"{names[c]} ({c})" for c in sorted(hit)][:10],
                  "note": f"Có nhiều NCC khớp **{want}**. Hỏi người dùng MỘT câu, đưa danh sách đánh số, rồi gọi lại tool "
                          "với đúng mã NCC."}


def _delivery_view(d: PODelivery) -> dict:
    return {"delivery_id": d.id, "delivery_no": int(d.delivery_no or 0), "warehouse_code": d.warehouse_code or "",
            "carrier_name": d.carrier_name or "", "ship_qty": _num(d.ship_qty), "ship_unit": d.ship_unit or "",
            "received_qty": _num(d.received_qty), "received_date": d.received_date or "",
            "status": d.status or "", "status_label": PO_DELIVERY_STATUS.label_of(d.status, d.status or ""),
            "invoice_no": d.invoice_no or "", "invoice_date": d.invoice_date or ""}


def _lines(ctx: ToolContext, supplier_code: str, codes: set[str] | None, action: str) -> list[dict]:
    """Mọi dòng còn GHI ĐƯỢC (đơn mở, dòng chưa Hoàn thành / Hủy) của NCC trong phạm vi `action`, kèm các lần giao.
    Cũ trước (ngày đặt, id đơn, id dòng)."""
    pos = {p.id: p for p in _scoped_open_pos(ctx, action).filter(PurchaseOrder.supplier_code == supplier_code)}
    if not pos:
        return []
    q = ctx.db.query(POItem).filter(POItem.po_id.in_(list(pos)),
                                    or_(POItem.progress_status.is_(None), POItem.progress_status.notin_(CLOSED_LINE_PROGRESS)))
    if codes:
        q = q.filter(POItem.product_code.in_(list(codes)))
    items = q.all()
    delivs: dict[int, list[PODelivery]] = {}
    if items:
        for d in (ctx.db.query(PODelivery).filter(PODelivery.po_item_id.in_([i.id for i in items]))
                  .order_by(PODelivery.delivery_no, PODelivery.id)):
            delivs.setdefault(d.po_item_id, []).append(d)
    out = []
    for it in items:
        po = pos[it.po_id]
        qty_order, qty_recv = _num(it.qty_order), _num(it.qty_received)
        out.append({"po_id": po.id, "po_code": po.code or "", "misa_code": po.misa_code or "",
                    "order_date": po.order_date or "", "status": po.status,
                    "status_label": _STATUS_LABELS.get(po.status, po.status), "po_item_id": it.id,
                    "product_code": (it.product_code or "").strip(), "product_name": it.product_name or "",
                    "unit": it.unit or "", "warehouse_code": it.warehouse_code or "", "qty_order": qty_order,
                    "qty_received": qty_recv, "qty_remaining": round(qty_order - qty_recv, 3),
                    "deliveries": [_delivery_view(d) for d in delivs.get(it.id, [])],
                    "url": PO_URL.format(id=po.id)})
    out.sort(key=lambda r: (r["order_date"], r["po_id"], r["po_item_id"]))
    return out


def _requested_codes(args: dict) -> list[str]:
    raw = args.get("product_codes")
    if isinstance(raw, str):
        raw = re.split(r"[,;\s]+", raw)
    return [c for c in dict.fromkeys(_code(x) for x in (raw or [])[:MAX_LINES]) if c] if isinstance(raw, list) else []


# ── po_open_lines ────────────────────────────────────────────────────────────────────────
def po_open_lines(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("purchase_order") or not ctx.can("supplier"):
        return denied("đơn mua hàng của nhà cung cấp")
    sup, problem = _resolve_supplier(ctx, args.get("supplier"))
    if problem:
        return problem
    codes = _requested_codes(args)
    rows = _lines(ctx, sup[0], set(codes) or None, "read")
    if not args.get("include_full"):
        rows = [r for r in rows if r["qty_remaining"] > EPS]
    rows.sort(key=lambda r: (r["product_code"], r["order_date"], r["po_id"], r["po_item_id"]))
    try:
        offset = max(0, int(args.get("offset") or 0))
        limit = max(1, min(int(args.get("limit") or PAGE_DEFAULT), PAGE_MAX))
    except (TypeError, ValueError):
        offset, limit = 0, PAGE_DEFAULT
    page = rows[offset:offset + limit]
    found = {r["product_code"] for r in rows}
    out = {"supplier": {"code": sup[0], "name": sup[1]}, "items": page, "total": len(rows),
           "offset": offset, "has_more": offset + limit < len(rows),
           "note": ("Dòng ĐMH đã duyệt còn thiếu hàng (qty_remaining = đặt − đã nhận), cũ trước, kèm các lần giao "
                    "(`deliveries`, lần đang chờ có received_qty = 0). Muốn ghi lần nhận theo phiếu xuất kho thì gọi "
                    "draft_po_receipt — đừng tự chia.")}
    if out["has_more"]:
        out["next_offset"] = offset + limit
    if missing := [c for c in codes if c not in found]:
        out["codes_without_open_lines"] = missing
    return out


# ── draft_po_receipt ─────────────────────────────────────────────────────────────────────
def _parse_lines(args: dict) -> tuple[list[dict], list[str]]:
    raw = args.get("lines")
    errors: list[str] = []
    if not isinstance(raw, list) or not raw:
        return [], ["Thiếu các dòng hàng của phiếu (`lines`: mã hàng + SL)."]
    merged: dict[str, dict] = {}
    for i, ln in enumerate(raw[:MAX_LINES], 1):
        if not isinstance(ln, dict):
            errors.append(f"Dòng {i} không đúng dạng.")
            continue
        code, qty = _code(ln.get("product_code")), parse_qty(ln.get("qty"))
        if not code or qty is None:
            errors.append(f"Dòng {i}: cần mã hàng và SL > 0 (SL gửi dạng số, 3.780 trên phiếu = 3780).")
            continue
        assign = []
        for a in (ln.get("assign") or [])[:MAX_ASSIGN] if isinstance(ln.get("assign"), list) else []:
            if not isinstance(a, dict):
                continue
            a_qty = parse_qty(a.get("qty"))
            if a_qty is None:
                errors.append(f"Mã {code}: chỉ định ĐMH cần SL > 0.")
                continue
            try:
                did, dno = int(a.get("delivery_id") or 0), int(a.get("delivery_no") or 0)
            except (TypeError, ValueError):
                did = dno = 0
            assign.append({"po": _code(a.get("po_code")), "qty": a_qty, "delivery_id": did, "delivery_no": dno,
                           "received_date": parse_date(a.get("received_date")),
                           "warehouse_code": _text(a.get("warehouse_code"), 50),
                           "ship_qty": parse_qty(a.get("ship_qty"))})
        slot = merged.setdefault(code, {"product_code": code, "qty": 0.0, "assign": []})
        slot["qty"] = round(slot["qty"] + qty, 3)
        slot["assign"] += assign
    if len(raw) > MAX_LINES:
        errors.append(f"Phiếu quá {MAX_LINES} dòng — tách làm nhiều lượt.")
    return list(merged.values()), errors


class _Plan:
    """Kế hoạch chia: mỗi phần tử một thao tác trên một dòng ĐMH (thêm lần giao / điền lần giao có sẵn)."""

    def __init__(self, lines: list[dict]):
        self.lines = {r["po_item_id"]: r for r in lines}
        self.cap = {r["po_item_id"]: max(0.0, r["qty_remaining"]) for r in lines}
        self.alloc: dict[tuple[int, str], float] = {}      # (po_id, mã) → SL đã chia (gồm phần dư)
        self.auto: dict[int, float] = {}                   # po_item_id → SL chia tự động
        self.explicit: list[dict] = []                     # thao tác người dùng chỉ định

    def take(self, item_id: int, qty: float, auto: bool = True, **extra) -> None:
        ln = self.lines[item_id]
        self.cap[item_id] = max(0.0, self.cap[item_id] - qty)
        key = (ln["po_id"], ln["product_code"])
        self.alloc[key] = round(self.alloc.get(key, 0.0) + qty, 3)
        if auto:
            self.auto[item_id] = round(self.auto.get(item_id, 0.0) + qty, 3)
        else:
            self.explicit.append({"po_item_id": item_id, "qty": qty, **extra})


def _kit_factor(plan: _Plan, pool: list[dict], po_id: int, code: str, slip_codes: set[str]) -> float | None:
    """Tỷ lệ bộ của đơn theo các mã đi kèm ĐÃ chia: Σ chia / Σ còn thiếu của chúng trong đơn. Chưa có thì None."""
    got = need = 0.0
    for c in slip_codes - {code}:
        if (po_id, c) in plan.alloc:
            got += plan.alloc[(po_id, c)]
            need += sum(max(0.0, r["qty_remaining"]) for r in pool if r["po_id"] == po_id and r["product_code"] == c)
    return got / need if need > EPS else None


def _auto_allocate(plan: _Plan, pool: list[dict], code: str, qty: float, slip_codes: set[str], kit: dict) -> float:
    """Chia `qty` của một mã vào các dòng còn thiếu. Trả phần chưa chia được (khi không còn dòng nào nhận)."""
    cands = [r for r in pool if r["product_code"] == code and plan.cap[r["po_item_id"]] > EPS]
    cands.sort(key=lambda r: (-kit.get(r["po_id"], 1), r["order_date"], r["po_id"], r["po_item_id"]))
    left, last = qty, None
    #  Lượt 1: theo tỷ lệ bộ của đơn (đơn nhiều mã của phiếu), lượt 2: lấp đủ phần còn thiếu theo cùng thứ tự.
    for first in (True, False):
        for r in cands:
            if left <= EPS:
                break
            target = plan.cap[r["po_item_id"]]
            if first and kit.get(r["po_id"], 1) > 1:
                f = _kit_factor(plan, pool, r["po_id"], code, slip_codes)
                if f is not None:   # theo bộ: có thể vượt phần còn thiếu (giao dư cùng tỷ lệ với mã đi kèm)
                    target = round(max(0.0, r["qty_remaining"]) * f, 3) - plan.auto.get(r["po_item_id"], 0.0)
            give = round(min(left, target), 3)
            if give > EPS:
                plan.take(r["po_item_id"], give)
                left, last = round(left - give, 3), r
    if left > EPS:
        #  Giao dư: dồn vào dòng chia sau cùng; chưa chia dòng nào (mọi dòng đã đủ) thì để người dùng chỉ định.
        target = last or next((r for r in cands), None)
        if target is not None:
            plan.take(target["po_item_id"], left)
            left = 0.0
    return left


def _find_po_lines(pool: list[dict], po: str, code: str) -> list[dict]:
    return [r for r in pool if r["product_code"] == code and po and po in (r["po_code"].upper(), r["misa_code"].upper())]


def _apply_assign(plan: _Plan, pool: list[dict], read_pool: list[dict], ln: dict, warnings: list[str]) -> float:
    """Chỉ định của người dùng cho một mã. Trả SL đã chia theo chỉ định."""
    used, code = 0.0, ln["product_code"]
    for a in ln["assign"]:
        rows = _find_po_lines(pool, a["po"], code)
        if not rows:
            if _find_po_lines(read_pool, a["po"], code):
                warnings.append(f"ĐMH {a['po']}: bạn chỉ được xem, không được ghi (ngoài phạm vi ghi) — bỏ qua chỉ định.")
            else:
                warnings.append(f"ĐMH {a['po'] or '(trống)'} không có dòng mở mã {code} trong phạm vi của bạn — bỏ qua "
                                "chỉ định.")
            continue
        extra = {k: a[k] for k in ("received_date", "warehouse_code", "ship_qty") if a.get(k)}
        if a["delivery_id"] or a["delivery_no"]:
            hit = [(r, d) for r in rows for d in r["deliveries"]
                   if (a["delivery_id"] and d["delivery_id"] == a["delivery_id"])
                   or (not a["delivery_id"] and d["delivery_no"] == a["delivery_no"])]
            if len(hit) != 1:
                warnings.append(f"ĐMH {a['po']} mã {code}: không thấy đúng một lần giao "
                                f"{a['delivery_id'] or 'số ' + str(a['delivery_no'])} — bỏ qua chỉ định.")
                continue
            r, d = hit[0]
            if any(x.get("delivery_id") == d["delivery_id"] for x in plan.explicit):
                warnings.append(f"Lần giao {d['delivery_id']} bị chỉ định hai lần — chỉ lấy lần đầu.")
                continue
            plan.cap[r["po_item_id"]] += d["received_qty"]       # sửa lần đã nhận: số cũ trả lại phần thiếu
            plan.take(r["po_item_id"], a["qty"], auto=False, op="update", delivery_id=d["delivery_id"], **extra)
        else:
            left = a["qty"]
            for i, r in enumerate(rows):
                give = left if i == len(rows) - 1 else min(left, plan.cap[r["po_item_id"]])
                if give > EPS:
                    plan.take(r["po_item_id"], round(give, 3), auto=False, op="add", **extra)
                    left = round(left - give, 3)
        used = round(used + a["qty"], 3)
    return used


def _pending_match(line: dict, qty: float, taken: set[int]) -> dict | None:
    for d in line["deliveries"]:
        if d["received_qty"] <= EPS and abs(d["ship_qty"] - qty) <= EPS and d["delivery_id"] not in taken:
            return d
    return None


def _rows(plan: _Plan, slip_date: str, default_wh: str) -> list[dict]:
    """Biến kế hoạch thành các dòng nháp (đúng dữ liệu `confirm_receipt` cần + phần đọc cho người)."""
    out, taken = [], {x["delivery_id"] for x in plan.explicit if x.get("delivery_id")}
    ops = list(plan.explicit)
    for item_id, qty in plan.auto.items():
        d = _pending_match(plan.lines[item_id], qty, taken)
        if d:
            taken.add(d["delivery_id"])
            ops.append({"po_item_id": item_id, "qty": qty, "op": "update", "delivery_id": d["delivery_id"]})
        else:
            ops.append({"po_item_id": item_id, "qty": qty, "op": "add"})
    after: dict[int, float] = {}
    for op in ops:
        ln = plan.lines[op["po_item_id"]]
        d = next((x for x in ln["deliveries"] if x["delivery_id"] == op.get("delivery_id")), None)
        before_d = d["received_qty"] if d else 0.0
        after[ln["po_item_id"]] = round(after.get(ln["po_item_id"], ln["qty_received"]) + op["qty"] - before_d, 3)
        out.append({"op": op["op"], "po_id": ln["po_id"], "po_code": ln["po_code"], "misa_code": ln["misa_code"],
                    "order_date": ln["order_date"], "po_item_id": ln["po_item_id"], "product_code": ln["product_code"],
                    "product_name": ln["product_name"], "unit": ln["unit"], "qty": op["qty"],
                    "delivery_id": d["delivery_id"] if d else 0, "delivery_no": d["delivery_no"] if d else 0,
                    "delivery_received_before": before_d,
                    "received_date": op.get("received_date") or slip_date,
                    "warehouse_code": op.get("warehouse_code") or default_wh,
                    **({"ship_qty": op["ship_qty"]} if op.get("ship_qty") else {}),
                    "qty_order": ln["qty_order"], "line_received_before": ln["qty_received"]})
    for r in out:
        r["line_received_after"] = after[r["po_item_id"]]
        r["over"] = round(max(0.0, after[r["po_item_id"]] - r["qty_order"]), 3)
    out.sort(key=lambda r: (r["po_code"], r["product_code"], r["po_item_id"]))
    return out


def _draft_ref(draft: dict) -> str:
    raw = json.dumps({k: draft.get(k) for k in ("supplier_code", "slip_no", "slip_date", "rows")}, sort_keys=True,
                     ensure_ascii=False, default=str)
    return hashlib.sha1(raw.encode()).hexdigest()[:10]


def _code_problems(ctx: ToolContext, lines: list[dict], pool: list[dict], read_pool: list[dict]) -> tuple[set, list]:
    """Mã của phiếu không có dòng ghi được: ngoài phạm vi ghi / không có đơn mở của NCC / không có trong danh mục."""
    from app.modules.product.model import Product

    have = {r["product_code"] for r in pool}
    lost = [ln["product_code"] for ln in lines if ln["product_code"] not in have]
    known = {c for (c,) in ctx.db.query(Product.code).filter(Product.code.in_(lost))} if lost else set()
    warnings = []
    for c in lost:
        if pos := sorted({r["po_code"] for r in read_pool if r["product_code"] == c}):
            warnings.append(f"Mã {c}: chỉ có ở ĐMH bạn được xem nhưng không được ghi ({', '.join(pos[:5])}) — chưa chia.")
        elif c in known:
            warnings.append(f"Mã {c}: không có dòng ĐMH đã duyệt nào của NCC này đang mở — chưa chia (kiểm lại mã / NCC).")
        else:
            warnings.append(f"Mã {c}: không có trong danh mục sản phẩm — có thể đọc sai mã trên phiếu, hỏi lại người dùng.")
    return set(lost), warnings


def draft_po_receipt(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("purchase_order", "write") or not ctx.can("supplier"):
        return denied("ghi lần nhận hàng vào đơn mua hàng")
    lines, errors = _parse_lines(args)
    slip_date = parse_date(args.get("slip_date"))
    if not slip_date:
        errors.append("Thiếu / sai ngày trên phiếu xuất kho (`slip_date` YYYY-MM-DD) — ngày này là ngày nhận hàng.")
    if errors:
        return {"error": " ".join(errors)}
    sup, problem = _resolve_supplier(ctx, args.get("supplier"))
    if problem:
        return problem
    codes = {ln["product_code"] for ln in lines}
    pool = _lines(ctx, sup[0], codes, "write")
    read_pool = _lines(ctx, sup[0], codes, "read")
    lost, warnings = _code_problems(ctx, lines, pool, read_pool)
    plan = _Plan(pool)
    open_rows = [r for r in pool if r["qty_remaining"] > EPS]
    #  Số mã của phiếu có dòng còn thiếu trong từng đơn — đơn "bộ" (≥ 2 mã) xét trước.
    kit = {pid: len({r["product_code"] for r in open_rows if r["po_id"] == pid}) for pid in {r["po_id"] for r in pool}}
    n_pos = {c: len({r["po_id"] for r in open_rows if r["product_code"] == c}) for c in codes}
    #  Mã ít đơn chứa chia trước (nắp chỉ ở một đơn) — mã đi kèm (chai) theo sau lấy theo tỷ lệ bộ.
    for ln in sorted((x for x in lines if x["product_code"] not in lost), key=lambda x: n_pos[x["product_code"]]):
        code, qty = ln["product_code"], ln["qty"]
        used = _apply_assign(plan, pool, read_pool, ln, warnings) if ln["assign"] else 0.0
        left = round(qty - used, 3)
        if left < -EPS:
            warnings.append(f"Mã {code}: chỉ định {vn(used)} nhiều hơn SL trên phiếu {vn(qty)}.")
        elif left > EPS:
            rest = _auto_allocate(plan, pool, code, left, codes, kit)
            if rest > EPS:
                warnings.append(f"Mã {code}: các dòng ĐMH mở đều đã nhận đủ — {vn(rest)} chưa chia. Muốn ghi dư thì chỉ "
                                "định ĐMH (assign).")
    default_wh = _text(args.get("warehouse_code"), 50)
    rows = _rows(plan, slip_date, default_wh)
    if not rows:
        return {"error": "Không chia được dòng nào vào ĐMH.", "warnings": warnings}
    for r in rows:
        if r["over"] > EPS:
            warnings.append(f"GIAO DƯ {vn(r['over'])} {r['unit']} mã {r['product_code']} ở {r['po_code']}: sau khi ghi đã "
                            f"nhận {vn(r['line_received_after'])} / đặt {vn(r['qty_order'])}.")
    others = sorted({r["po_code"] for r in read_pool if r["product_code"] in codes} - {r["po_code"] for r in pool})
    if others:
        warnings.append(f"Có ĐMH mở của NCC này bạn chỉ được xem, không được ghi: {', '.join(others[:10])} — không chia vào.")
    draft = {"supplier_code": sup[0], "supplier_name": sup[1], "slip_no": _text(args.get("slip_no"), 50),
             "slip_date": slip_date, "rows": rows}
    draft["draft_ref"] = _draft_ref(draft)
    return {"draft": draft, "kind": KIND, "warnings": list(dict.fromkeys(warnings)),
            "note": ("Đã soạn nháp, CHƯA ghi gì. Trình người dùng bảng `draft.rows` (ĐMH, mã MISA, mã hàng, SL ghi, thêm lần "
                     "giao mới hay điền lần giao số mấy, đã nhận sau khi ghi / đặt) và đọc rõ từng cảnh báo, nhất là GIAO "
                     "DƯ. Người dùng muốn chia khác thì gọi lại tool này với `assign` / SL mới (đừng tự sửa `draft`). Họ "
                     "đồng ý rõ thì gọi confirm_draft với kind=po_receipt và draft = đúng đối tượng `draft` này. Đừng tự "
                     "báo là đã ghi.")}


# ── xác nhận (chạy phía ERP: agent_hub.draft_create.create → kind po_receipt) ───────────────
def _err(msg: str):
    from app.modules.agent_hub.draft_create import DraftError

    return DraftError(msg)


def _validated_rows(draft: dict) -> list[dict]:
    rows = draft.get("rows") if isinstance(draft, dict) else None
    if not isinstance(rows, list) or not rows or len(rows) > MAX_LINES * MAX_ASSIGN:
        raise _err("Bản nháp không có dòng nào để ghi — gọi lại draft_po_receipt.")
    out = []
    for r in rows:
        if not isinstance(r, dict) or r.get("op") not in ("add", "update"):
            raise _err("Bản nháp hỏng (thao tác lạ) — gọi lại draft_po_receipt, đừng tự sửa bản nháp.")
        qty, rdate = parse_qty(r.get("qty")), parse_date(r.get("received_date"))
        try:
            po_id, item_id, did = int(r.get("po_id") or 0), int(r.get("po_item_id") or 0), int(r.get("delivery_id") or 0)
            line_before, d_before = float(r.get("line_received_before") or 0), float(r.get("delivery_received_before") or 0)
        except (TypeError, ValueError):
            raise _err("Bản nháp hỏng (số không hợp lệ) — gọi lại draft_po_receipt.") from None
        if qty is None or not rdate or po_id <= 0 or item_id <= 0 or (r["op"] == "update" and did <= 0):
            raise _err("Bản nháp thiếu SL / ngày nhận / dòng ĐMH — gọi lại draft_po_receipt.")
        ship = parse_qty(r.get("ship_qty")) if r.get("ship_qty") else None
        out.append({"op": r["op"], "po_id": po_id, "po_item_id": item_id, "delivery_id": did, "qty": qty,
                    "received_date": rdate, "warehouse_code": _text(r.get("warehouse_code"), 50),
                    "ship_qty": ship, "product_code": _code(r.get("product_code")),
                    "line_received_before": line_before, "delivery_received_before": d_before})
    if len({r["delivery_id"] for r in out if r["op"] == "update"}) != sum(r["op"] == "update" for r in out):
        raise _err("Bản nháp sửa một lần giao hai lần — gọi lại draft_po_receipt.")
    return out


def _check_po(db, user, profile, po_id: int, rows: list[dict], supplier_code: str):
    """Kiểm lại MỘT đơn trước khi ghi: phạm vi `write`, trạng thái, dòng, lần giao, dữ liệu chưa đổi."""
    from app.modules.purchase_order import service as po_service
    from app.modules.purchase_order.base_service import deliveries_of, items_of

    po = apply_scope(po_service.query_by_id(db, po_id), PurchaseOrder, "purchase_order", user, profile, "write").first()
    if po is None:
        raise _err(f"Không tìm thấy ĐMH #{po_id} trong phạm vi bạn được ghi — chưa ghi gì.")
    if po.status not in OPEN_PO_STATUSES:
        raise _err(f"ĐMH {po.code} không còn ở trạng thái đã duyệt / đang nhận — chưa ghi gì.")
    if supplier_code and (po.supplier_code or "") != supplier_code:
        raise _err(f"ĐMH {po.code} không phải của NCC trên phiếu — chưa ghi gì.")
    items = {it.id: it for it in items_of(db, po.id)}
    for r in rows:
        it = items.get(r["po_item_id"])
        if it is None or (it.product_code or "").strip().upper() != r["product_code"]:
            raise _err(f"Dòng mã {r['product_code']} không thuộc ĐMH {po.code} — chưa ghi gì.")
        if (it.progress_status or "") in CLOSED_LINE_PROGRESS:
            raise _err(f"Dòng {r['product_code']} của {po.code} đã Hoàn thành / Hủy — chưa ghi gì.")
        if abs(_num(it.qty_received) - r["line_received_before"]) > EPS:
            raise _err(f"Dòng {r['product_code']} của {po.code} đã có người ghi nhận hàng sau lúc soạn nháp (đã nhận "
                       f"{vn(_num(it.qty_received))}) — gọi lại draft_po_receipt để soạn nháp mới. Chưa ghi gì.")
        if r["op"] == "update":
            d = next((x for x in deliveries_of(db, it.id) if x.id == r["delivery_id"]), None)
            if d is None or abs(_num(d.received_qty) - r["delivery_received_before"]) > EPS:
                raise _err(f"Lần giao #{r['delivery_id']} của {po.code} không còn / đã đổi sau lúc soạn nháp — gọi lại "
                           "draft_po_receipt. Chưa ghi gì.")
    return po


def _payload(db, po, rows: list[dict], note: str):
    """Nguyên đơn đúng hình màn web gửi lên (`PATCH /api/purchase-orders/{id}`): MỌI dòng + MỌI lần giao cũ giữ nguyên id
    (thiếu là `_save_deliveries` / `_save_items` coi như xóa), chỉ đổi đúng các lần giao trong nháp, lần mới nối cuối."""
    from pydantic import ValidationError

    from app.modules.purchase_order.base_service import deliveries_of, items_of
    from app.modules.purchase_order.schema import DeliveryIn, POItemIn, POUpdate

    from .update_tool import _row_to_input

    updates = {r["delivery_id"]: r for r in rows if r["op"] == "update"}
    adds: dict[int, list[dict]] = {}
    for r in rows:
        if r["op"] == "add":
            adds.setdefault(r["po_item_id"], []).append(r)
    items_in = []
    try:
        for it in items_of(db, po.id):
            existing = deliveries_of(db, it.id)
            delivs = []
            for d in existing:
                din = _row_to_input(DeliveryIn, d)
                if (u := updates.get(d.id)) is not None:
                    change = {"received_qty": u["qty"], "received_date": u["received_date"]}
                    if u["warehouse_code"]:
                        change["warehouse_code"] = u["warehouse_code"]
                    if u["ship_qty"]:
                        change["ship_qty"] = u["ship_qty"]
                    din = DeliveryIn(**{**din.model_dump(), **change})
                delivs.append(din)
            nxt = max((int(d.delivery_no or 0) for d in existing), default=0) + 1
            for a in adds.get(it.id, []):
                delivs.append(DeliveryIn(delivery_no=nxt, warehouse_code=a["warehouse_code"] or (it.warehouse_code or ""),
                                         ship_qty=a["ship_qty"] or a["qty"], ship_unit=it.unit or "",
                                         received_qty=a["qty"], received_date=a["received_date"], progress_note=note))
                nxt += 1
            items_in.append(POItemIn(**{**_row_to_input(POItemIn, it).model_dump(exclude={"deliveries"}),
                                        "deliveries": delivs}))
    except ValidationError as e:
        raise _err(f"ĐMH {po.code} có dữ liệu cũ không hợp lệ ({str(e)[:200]}) — ghi lần nhận trên màn ĐMH.") from None
    return POUpdate(items=items_in)


def _summary(po, rows: list[dict]) -> str:
    parts = [f"{r['product_code']} {'+' if r['op'] == 'add' else 'lần giao #' + str(r['delivery_id']) + ' = '}{vn(r['qty'])}"
             for r in rows]
    return f"{po.code}: " + "; ".join(parts)


def confirm_receipt(db, user, draft: dict, source: int = 0) -> tuple[str, int]:
    """Ghi thật. Kiểm lại hết (quyền + phạm vi write từng đơn, trạng thái, dòng, lần giao chưa đổi) TRƯỚC khi ghi đơn
    đầu tiên; ghi từng đơn bằng `purchase_order.service.update_po` (commit mỗi đơn như một lần bấm Lưu)."""
    from fastapi import HTTPException

    from app.core.audit import record as audit_record
    from app.core.auth import get_perm_profile, user_has_permission
    from app.modules.assistant import change_service
    from app.modules.assistant.change_model import ChangeAction
    from app.modules.purchase_order import service as po_service

    if not user_has_permission(db, user, "purchase_order", "write"):
        raise _err("Tài khoản này không có quyền sửa đơn mua hàng nên không ghi được lần nhận hàng.")
    rows = _validated_rows(draft)
    supplier_code = _text(draft.get("supplier_code"), 50)
    slip_no, ref = _text(draft.get("slip_no"), 50), _text(draft.get("draft_ref"), 20)
    profile = get_perm_profile(db, user)
    by_po: dict[int, list[dict]] = {}
    for r in rows:
        by_po.setdefault(r["po_id"], []).append(r)
    pos = {pid: _check_po(db, user, profile, pid, prow, supplier_code) for pid, prow in by_po.items()}
    note = f"Phiếu xuất kho NCC{' số ' + slip_no if slip_no else ''} — ghi qua trợ lý AI"
    done: list[str] = []
    for pid, prow in by_po.items():
        po = pos[pid]
        code = po.code
        before = {"deliveries": [{"delivery_id": r["delivery_id"], "received_qty": r["delivery_received_before"]}
                                 for r in prow if r["op"] == "update"]}
        try:
            po_service.update_po(db, pid, _payload(db, po, prow, note), user.id)
        except HTTPException as e:
            db.rollback()
            head = f"Đã ghi {', '.join(done)}; " if done else ""
            raise _err(f"{head}{code} chưa ghi: {e.detail}") from None
        summary = _summary(po, prow)
        audit_record(db, user.id, "purchase_order", pid,
                     "update", f"Ghi lần nhận hàng qua trợ lý AI (nháp {ref or '?'}, phiếu xuất kho "
                               f"{slip_no or 'không số'} ngày {prow[0]['received_date']}): {summary}"[:1000],
                     doc_code=code)
        change_service.record_change(db, user, entity="purchase_order", entity_id=pid, doc_code=code,
                                     action=ChangeAction.UPDATE, summary=f"Ghi lần nhận hàng {summary}",
                                     before=before, after={"draft_ref": ref, "slip_no": slip_no, "rows": prow},
                                     after_sig="", source=source)
        done.append(code)
    return ", ".join(done), next(iter(by_po))


def created_details(db, po_id: int) -> list[str]:
    """Các dòng của ĐMH sau khi ghi (đặt / đã nhận / dư), đọc lại từ DB — không có giá."""
    from app.modules.purchase_order.base_service import items_of

    po = db.get(PurchaseOrder, int(po_id or 0))
    if po is None:
        return []
    out = [f"{po.code}{' · MISA ' + po.misa_code if po.misa_code else ''} · {_STATUS_LABELS.get(po.status, po.status)}"]
    for it in items_of(db, po.id):
        got, need = _num(it.qty_received), _num(it.qty_order)
        tail = f" (dư {vn(got - need)})" if got - need > EPS else (f" (còn thiếu {vn(need - got)})" if need - got > EPS else "")
        out.append(f"- {it.product_code}: đã nhận {vn(got)} / đặt {vn(need)}{tail}")
    return out


def summary_lines(draft: dict) -> list[str]:
    """Tóm tắt nháp cho bot (draft_create.summarize)."""
    out = [f"NCC: {draft.get('supplier_name') or draft.get('supplier_code') or '?'}",
           f"Phiếu xuất kho: {draft.get('slip_no') or '(không số)'} · ngày {draft.get('slip_date') or '?'}"]
    for r in (draft.get("rows") or [])[:12]:
        how = "thêm lần giao" if r.get("op") == "add" else f"điền lần giao số {r.get('delivery_no')}"
        out.append(f"- {r.get('po_code')} · {r.get('product_code')}: {vn(r.get('qty'))} ({how})")
    return out


_SUPPLIER = {"type": "string", "description": "Tên NCC đúng như trên phiếu, hoặc mã NCC / MST (khớp mờ, bỏ dấu)."}

PO_OPEN_LINES_SPEC = ToolSpec(
    name="po_open_lines",
    description=("Các dòng ĐƠN MUA HÀNG (ĐMH) đã duyệt CÒN THIẾU HÀNG của một NCC: mã ĐMH, mã MISA, ngày đặt, trạng thái, mã "
                 "hàng, tên, SL đặt / đã nhận / còn thiếu, và các LẦN GIAO đã có (lần thứ mấy, kho, đơn vị vận chuyển, SL "
                 "gửi, SL nhận, ngày nhận, trạng thái, hóa đơn). Dùng để giải thích cho người dùng khi đối chiếu phiếu "
                 "xuất kho / phiếu giao hàng của NCC. Muốn GHI lần nhận thì dùng draft_po_receipt."),
    parameters={"type": "object", "properties": {
        "supplier": _SUPPLIER,
        "product_codes": {"type": "array", "items": {"type": "string"}, "description": "Lọc theo mã hàng (tùy chọn)."},
        "include_full": {"type": "boolean", "description": "Kèm cả dòng đã nhận đủ (mặc định không)."},
        "offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": PAGE_MAX}},
        "required": ["supplier"]},
    handler=po_open_lines,
)

DRAFT_PO_RECEIPT_SPEC = ToolSpec(
    name="draft_po_receipt",
    description=("SOẠN NHÁP ghi LẦN NHẬN HÀNG vào ĐMH từ PHIẾU XUẤT KHO / phiếu giao hàng của NCC (người dùng gửi ẢNH "
                 "phiếu: tự đọc NCC, ngày, số phiếu, các dòng MÃ HÀNG + tổng SL; phiếu không ghi số ĐMH). Tool tự đề xuất "
                 "chia vào dòng ĐMH đã duyệt còn thiếu (đơn có cả chai + nắp của phiếu trước, rồi đơn cũ trước; điền lần "
                 "giao đang chờ khớp số, không thì thêm lần giao mới), báo GIAO DƯ / mã không có đơn / ngoài quyền. KHÔNG "
                 "ghi gì. Quy trình: đọc ảnh → gọi tool này → trình bảng + cảnh báo → người dùng sửa thì gọi lại với SL / "
                 "assign mới → họ đồng ý rõ thì confirm_draft(kind=po_receipt, draft=đúng `draft`). Ngày nhận = ngày "
                 "trên phiếu. Không xóa lần giao qua AI."),
    parameters={"type": "object", "properties": {
        "supplier": _SUPPLIER,
        "slip_date": {"type": "string", "description": "Ngày trên phiếu YYYY-MM-DD — ghi làm ngày nhận hàng."},
        "slip_no": {"type": "string", "description": "Số phiếu xuất kho (nếu có)."},
        "warehouse_code": {"type": "string", "description": "Kho nhận (tùy chọn; trống = kho mặc định của dòng ĐMH)."},
        "lines": {"type": "array", "maxItems": MAX_LINES, "items": {"type": "object", "properties": {
            "product_code": {"type": "string", "description": "Mã hàng trên phiếu (trùng mã hàng của dòng ĐMH)."},
            "qty": {"type": "number", "description": "Tổng SL của mã trên phiếu (3.780 trên phiếu = 3780)."},
            "assign": {"type": "array", "maxItems": MAX_ASSIGN, "description": (
                "Tùy chọn — người dùng chỉ định chia: mỗi phần tử một ĐMH. Có delivery_id / delivery_no = SỬA lần giao "
                "đó (SL nhận = qty), không có = thêm lần giao mới. Phần SL phiếu còn lại tool tự chia."),
                "items": {"type": "object", "properties": {
                    "po_code": {"type": "string", "description": "Mã ĐMH hoặc mã MISA."},
                    "qty": {"type": "number"},
                    "delivery_id": {"type": "integer", "description": "Id lần giao (từ po_open_lines) cần điền / sửa."},
                    "delivery_no": {"type": "integer", "description": "Hoặc số thứ tự lần giao của dòng."},
                    "received_date": {"type": "string", "description": "Ngày nhận riêng (mặc định ngày phiếu)."},
                    "warehouse_code": {"type": "string"},
                    "ship_qty": {"type": "number", "description": "SL gửi (chỉ khi người dùng nêu)."}},
                    "required": ["po_code", "qty"]}}},
            "required": ["product_code", "qty"]}}},
        "required": ["supplier", "slip_date", "lines"]},
    handler=draft_po_receipt,
)

PO_RECEIPT_SPECS = [PO_OPEN_LINES_SPEC, DRAFT_PO_RECEIPT_SPEC]
