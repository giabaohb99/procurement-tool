"""Tính báo cáo ma trận (đối tượng × tháng) + precompute snapshot.

Đọc báo cáo -> lấy snapshot đã tính (nhanh). Nút "Cập nhật" -> tính lại + lưu (chạy nền)."""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from .model import ReportSnapshot


def _mk(s):
    return (s or "")[:7]  # 'YYYY-MM'


def _amt(it):
    return float(it.qty_order or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)


def _recv_amt(it):
    return float(it.qty_received or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)


def _rate(part, whole):
    return round(part / whole * 100, 2) if whole else 0


def compute(db: Session, year: str, company_id) -> dict:
    poq = db.query(PurchaseOrder)
    if company_id:
        poq = poq.filter(PurchaseOrder.company_id == int(company_id))
    if year and year != "all":
        poq = poq.filter(PurchaseOrder.order_date.like(f"{year}%"))
    pos = poq.all()
    po_ids = [p.id for p in pos]
    po_by = {p.id: p for p in pos}
    items = db.query(POItem).filter(POItem.po_id.in_(po_ids)).all() if po_ids else []
    item_by = {it.id: it for it in items}
    delivs = (db.query(PODelivery).filter(PODelivery.po_id.in_(po_ids), PODelivery.received_qty > 0).all()
              if po_ids else [])

    # ---- Danh sách tháng ----
    if year and year != "all":
        months = [f"{year}-{m:02d}" for m in range(1, 13)]
    else:
        s = set()
        for p in pos:
            if p.order_date:
                s.add(_mk(p.order_date))
        for d in delivs:
            if d.received_date:
                s.add(_mk(d.received_date))
        months = sorted(x for x in s if x)
    month_out = [{"key": m, "label": f"{m[5:7]}/{m[:4]}"} for m in months]
    mset = set(months)

    # ================= 1) BỘ PHẬN (đặt hàng / gấp) — theo order_date =================
    dept = {}
    for p in pos:
        m = _mk(p.order_date)
        if m not in mset:
            continue
        r = dept.setdefault(p.department or "(Không rõ)", {"key": p.department or "(Không rõ)", "m": {}, "orders": 0, "urgent": 0})
        c = r["m"].setdefault(m, {"orders": 0, "urgent": 0})
        c["orders"] += 1
        r["orders"] += 1
        if p.is_urgent:
            c["urgent"] += 1
            r["urgent"] += 1
    for r in dept.values():
        for c in r["m"].values():
            c["rate"] = _rate(c["urgent"], c["orders"])
        r["rate"] = _rate(r["urgent"], r["orders"])
        r["warn"] = r["rate"] > 30
    department = sorted(dept.values(), key=lambda x: -x["orders"])

    # ================= per-delivery helpers =================
    def deliv_dim(dimfn, metricfn):
        """Gom deliveries theo key(dimfn) × tháng; metricfn(cell, delivery, item)."""
        agg = {}
        for d in delivs:
            m = _mk(d.received_date)
            if m not in mset:
                continue
            po = po_by.get(d.po_id)
            it = item_by.get(d.po_item_id)
            key = dimfn(po, it)
            r = agg.setdefault(key, {"key": key, "m": {}})
            c = r["m"].setdefault(m, {})
            metricfn(c, r, d, it)
        return agg

    # ================= 2) NCC (giao dịch / trễ theo quy định) =================
    def sup_metric(c, r, d, it):
        c["trans"] = c.get("trans", 0) + 1
        r["trans"] = r.get("trans", 0) + 1
        if (d.diff_regulated or 0) < 0:
            c["late"] = c.get("late", 0) + 1
            r["late"] = r.get("late", 0) + 1
    sup_agg = deliv_dim(lambda po, it: (po.supplier_name or po.supplier_code) if po else "(Không rõ)", sup_metric)
    for r in sup_agg.values():
        r.setdefault("trans", 0); r.setdefault("late", 0)
        for c in r["m"].values():
            c["rate"] = _rate(c.get("late", 0), c.get("trans", 0))
        r["rate"] = _rate(r["late"], r["trans"])
        r["warn"] = r["rate"] > 30
    supplier = sorted(sup_agg.values(), key=lambda x: -x["trans"])

    # ================= 3) NSPT (số đơn giao / trễ-đúng-sớm) =================
    def nspt_metric(c, r, d, it):
        dv = d.diff_regulated or 0
        for k in ("orders", "late", "ontime", "early"):
            c.setdefault(k, 0)
        c["orders"] += 1; r["orders"] = r.get("orders", 0) + 1
        if dv < 0:
            c["late"] += 1; r["late"] = r.get("late", 0) + 1
        elif dv == 0:
            c["ontime"] += 1; r["ontime"] = r.get("ontime", 0) + 1
        else:
            c["early"] += 1; r["early"] = r.get("early", 0) + 1
    nspt_agg = deliv_dim(lambda po, it: (po.nspt or "(Không rõ)") if po else "(Không rõ)", nspt_metric)
    for r in nspt_agg.values():
        for k in ("orders", "late", "ontime", "early"):
            r.setdefault(k, 0)
        for c in r["m"].values():
            c["rate"] = _rate(c.get("late", 0), c.get("orders", 0))
        r["rate"] = _rate(r["late"], r["orders"])
    nspt = sorted(nspt_agg.values(), key=lambda x: -x["orders"])

    # ================= 4) PHÂN LOẠI VTBB/NL (tần suất mua / chi phí) =================
    def ig_metric(c, r, d, it):
        c["trans"] = c.get("trans", 0) + 1
        r["trans"] = r.get("trans", 0) + 1
        cost = _recv_amt(it) if it else 0
        c["cost"] = round(c.get("cost", 0) + cost, 2)
        r["cost"] = round(r.get("cost", 0) + cost, 2)
    ig_agg = deliv_dim(lambda po, it: (it.item_group or "(Không rõ)") if it else "(Không rõ)", ig_metric)
    for r in ig_agg.values():
        r.setdefault("trans", 0); r.setdefault("cost", 0)
    item_group = sorted(ig_agg.values(), key=lambda x: -x["cost"])

    # ================= 5) CHI PHÍ VẬN CHUYỂN (theo đơn vị VC) =================
    ship_agg = {}
    ship_detail = []
    for d in delivs:
        if not (d.carrier_code and float(d.shipping_amount or 0) > 0):
            continue
        m = _mk(d.received_date)
        if m not in mset:
            continue
        po = po_by.get(d.po_id); it = item_by.get(d.po_item_id)
        key = d.carrier_name or d.carrier_code
        r = ship_agg.setdefault(key, {"key": key, "m": {}, "freq": 0, "order_value": 0.0, "ship_cost": 0.0})
        c = r["m"].setdefault(m, {"freq": 0, "order_value": 0.0, "ship_cost": 0.0})
        ov = _recv_amt(it) if it else 0
        sc = float(d.shipping_amount or 0)
        c["freq"] += 1; r["freq"] += 1
        c["order_value"] = round(c["order_value"] + ov, 2); r["order_value"] = round(r["order_value"] + ov, 2)
        c["ship_cost"] = round(c["ship_cost"] + sc, 2); r["ship_cost"] = round(r["ship_cost"] + sc, 2)
        ship_detail.append({
            "carrier": key, "month": f"{m[5:7]}/{m[:4]}",
            "product_code": it.product_code if it else "", "misa_code": po.misa_code if po else "",
            "invoice_no": it.invoice_no if it else "", "received_date": d.received_date,
            "qty_order": float(it.qty_order or 0) if it else 0, "qty_received": float(d.received_qty or 0),
            "order_amount": ov, "ship_amount": sc, "rate": _rate(sc, ov),
        })
    for r in ship_agg.values():
        for c in r["m"].values():
            c["rate"] = _rate(c["ship_cost"], c["order_value"])
        r["rate"] = _rate(r["ship_cost"], r["order_value"])
    shipping = sorted(ship_agg.values(), key=lambda x: -x["ship_cost"])

    return {
        "computed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "year": year, "months": month_out,
        "department": department, "supplier": supplier, "nspt": nspt,
        "item_group": item_group, "shipping": shipping, "shipping_detail": ship_detail[:300],
    }


def _key(year, company_id):
    return f"{year or 'all'}|{company_id or 'all'}"


def get_snapshot(db: Session, year, company_id, refresh: bool = False) -> dict:
    key = _key(year, company_id)
    snap = db.query(ReportSnapshot).filter(ReportSnapshot.key == key).first()
    if snap and not refresh:
        try:
            return json.loads(snap.data)
        except Exception:
            pass
    data = compute(db, year, company_id)
    if not snap:
        snap = ReportSnapshot(key=key)
        db.add(snap)
    snap.data = json.dumps(data, ensure_ascii=False)
    snap.computed_at = data["computed_at"]
    db.commit()
    return data
