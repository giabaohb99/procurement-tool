"""Báo cáo mua hàng — 1 endpoint trả đủ các chiều phân tích (số liệu thật)."""
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success
from app.modules.inventory.model import Inventory
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from . import service as report_service

router = APIRouter(prefix="/api/reports", tags=["report"])


@router.get("/daily")
def daily(request: Request, db: Session = Depends(get_db), user=Depends(require("report", "read"))):
    """Chi phí theo NGÀY trong 1 tháng (drill-down khi click cột). Nhẹ: lọc theo tháng rồi gom theo ngày."""
    month = request.query_params.get("month")  # 'YYYY-MM'
    company_id = request.query_params.get("company_id")
    q = db.query(Payable)
    if month:
        q = q.filter(Payable.incur_date.like(f"{month}%"))
    if company_id:
        q = q.filter(Payable.company_id == int(company_id))
    agg = {}
    for p in q.all():
        day = p.incur_date or ""
        if not day:
            continue
        e = agg.setdefault(day, {"date": day, "goods": 0.0, "shipping": 0.0, "amount": 0.0})
        t = float(p.total or 0)
        e["amount"] += t
        if p.source_type == "shipping":
            e["shipping"] += t
        else:
            e["goods"] += t
    days = [{"date": k, "day": k[8:10], "goods": round(v["goods"], 2),
             "shipping": round(v["shipping"], 2), "amount": round(v["amount"], 2)}
            for k, v in sorted(agg.items())]
    return success({"month": month, "days": days, "total": round(sum(d["amount"] for d in days), 2)})


@router.get("/matrix")
def matrix(request: Request, db: Session = Depends(get_db), user=Depends(require("report", "read"))):
    """Báo cáo ma trận (NCC/phân loại/NSPT/bộ phận/vận chuyển) — đọc snapshot đã tính sẵn.

    refresh=1 -> tính lại + lưu snapshot (nút 'Cập nhật báo cáo')."""
    year = request.query_params.get("year") or str(datetime.now().year)
    company_id = request.query_params.get("company_id")
    refresh = request.query_params.get("refresh") == "1"
    return success(report_service.get_snapshot(db, year, company_id, refresh=refresh))

PO_STATUSES = ["draft", "submitted", "approved", "partial", "received", "completed", "cancelled", "rejected"]


def _amt(it):
    return float(it.qty_order or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)


def _recv_amt(it):
    return float(it.qty_received or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)


@router.get("/procurement")
def procurement(request: Request, db: Session = Depends(get_db),
                user=Depends(require("report", "read"))):
    year = request.query_params.get("year") or str(datetime.now().year)
    company_id = request.query_params.get("company_id")
    today = datetime.now().date().strftime("%Y-%m-%d")

    poq = db.query(PurchaseOrder)
    payq = db.query(Payable)
    invq_rows = db.query(Inventory)
    if company_id:
        poq = poq.filter(PurchaseOrder.company_id == int(company_id))
        payq = payq.filter(Payable.company_id == int(company_id))
        invq_rows = invq_rows.filter(Inventory.company_id == int(company_id))
    if year and year != "all":
        poq = poq.filter(PurchaseOrder.order_date.like(f"{year}%"))
        payq = payq.filter(Payable.period == year)
    pos = poq.all()
    po_ids = [p.id for p in pos]
    po_code = {p.id: p.code for p in pos}
    pays = payq.all()
    items = db.query(POItem).filter(POItem.po_id.in_(po_ids)).all() if po_ids else []
    item_name = {it.id: it.product_name for it in items}
    delivs = (db.query(PODelivery).filter(PODelivery.po_id.in_(po_ids), PODelivery.received_qty > 0).all()
              if po_ids else [])

    # ---- Tổng quan ----
    status_count = {s: 0 for s in PO_STATUSES}
    for p in pos:
        status_count[p.status] = status_count.get(p.status, 0) + 1
    order_value = sum(_amt(it) for it in items)

    def bucket(src):
        rows = [p for p in pays if p.source_type == src]
        tot = sum(float(p.total or 0) for p in rows)
        paid = sum(float(p.paid_amount or 0) for p in rows)
        return {"total": round(tot, 2), "paid": round(paid, 2), "remaining": round(tot - paid, 2)}

    overdue = sum(float(p.remaining or 0) for p in pays
                  if p.status != "Đã TT" and p.due_date and p.due_date < today)

    late = [d for d in delivs if (d.diff_promise or 0) < 0 or (d.diff_regulated or 0) < 0]
    late_list = [{"po_code": po_code.get(d.po_id, ""), "product": item_name.get(d.po_item_id, ""),
                  "promised": d.promised_date, "received": d.received_date,
                  "diff_promise": d.diff_promise, "diff_regulated": d.diff_regulated} for d in late][:20]

    inv_value = float(db.query(func.coalesce(func.sum(Inventory.value), 0))
                      .filter(*( [Inventory.company_id == int(company_id)] if company_id else [] )).scalar() or 0)

    spend = {}
    for p in pays:
        mo = (p.incur_date or "")[:7]
        if mo:
            spend[mo] = spend.get(mo, 0) + float(p.total or 0)
    spend_by_month = [{"month": k, "amount": round(v, 2)} for k, v in sorted(spend.items())]

    # ---- Giá trị theo PO ----
    po_order_val, po_recv_val = {}, {}
    for it in items:
        po_order_val[it.po_id] = po_order_val.get(it.po_id, 0) + _amt(it)
        po_recv_val[it.po_id] = po_recv_val.get(it.po_id, 0) + _recv_amt(it)
    rem_by_po = {}
    for p in pays:
        rem_by_po[p.po_code] = rem_by_po.get(p.po_code, 0) + (float(p.total or 0) - float(p.paid_amount or 0))

    # ---- Breakdown theo dimension header (NCC / NSPT / Bộ phận) ----
    def by_header(attr):
        agg = {}
        for po in pos:
            key = getattr(po, attr) or "(Không rõ)"
            e = agg.setdefault(key, {"key": key, "po_count": 0, "order_value": 0.0, "received_value": 0.0, "debt": 0.0})
            e["po_count"] += 1
            e["order_value"] += po_order_val.get(po.id, 0)
            e["received_value"] += po_recv_val.get(po.id, 0)
            e["debt"] += rem_by_po.get(po.code, 0)
        return [{**v, "order_value": round(v["order_value"], 2), "received_value": round(v["received_value"], 2),
                 "debt": round(v["debt"], 2)} for v in sorted(agg.values(), key=lambda x: -x["order_value"])]

    # NCC dùng tên: map supplier_code -> supplier_name từ PO
    sup_name = {p.supplier_code: (p.supplier_name or p.supplier_code) for p in pos}
    by_supplier = by_header("supplier_code")
    for r in by_supplier:
        r["key"] = sup_name.get(r["key"], r["key"])

    # ---- Breakdown theo phân loại VTBB/NL ----
    ig = {}
    for it in items:
        k = it.item_group or "(Không rõ)"
        e = ig.setdefault(k, {"key": k, "qty_order": 0.0, "qty_received": 0.0, "order_value": 0.0, "received_value": 0.0})
        e["qty_order"] += float(it.qty_order or 0)
        e["qty_received"] += float(it.qty_received or 0)
        e["order_value"] += _amt(it)
        e["received_value"] += _recv_amt(it)
    by_item_group = [{**v, "order_value": round(v["order_value"], 2), "received_value": round(v["received_value"], 2)}
                     for v in sorted(ig.values(), key=lambda x: -x["order_value"])]

    # ---- Chi phí vận chuyển ----
    ship = [p for p in pays if p.source_type == "shipping"]
    sc = {}
    for p in ship:
        e = sc.setdefault(p.supplier_code, {"carrier": p.supplier_name or p.supplier_code, "amount": 0.0, "count": 0})
        e["amount"] += float(p.total or 0)
        e["count"] += 1
    ship_month = {}
    for p in ship:
        mo = (p.incur_date or "")[:7]
        if mo:
            ship_month[mo] = ship_month.get(mo, 0) + float(p.total or 0)
    shipping = {
        "total": round(sum(float(p.total or 0) for p in ship), 2),
        "by_carrier": [{**v, "amount": round(v["amount"], 2)} for v in sorted(sc.values(), key=lambda x: -x["amount"])],
        "by_month": [{"month": k, "amount": round(v, 2)} for k, v in sorted(ship_month.items())],
    }

    # ---- Tồn kho ----
    inv_rows = invq_rows.all()
    inv_by_wh = {}
    for r in inv_rows:
        inv_by_wh[r.warehouse_code] = inv_by_wh.get(r.warehouse_code, 0) + float(r.value or 0)
    inventory = {
        "total": round(inv_value, 2),
        "by_warehouse": [{"warehouse": k, "value": round(v, 2)} for k, v in sorted(inv_by_wh.items(), key=lambda x: -x[1])],
        "top": sorted([{"product_code": r.product_code, "product_name": r.product_name,
                        "warehouse": r.warehouse_code, "qty": float(r.qty or 0),
                        "avg_cost": float(r.avg_cost or 0), "value": float(r.value or 0)} for r in inv_rows],
                      key=lambda x: -x["value"])[:20],
    }

    return success({
        "po_status": status_count, "po_count": len(pos), "order_value": round(order_value, 2),
        "payable_goods": bucket("goods"), "payable_shipping": bucket("shipping"),
        "overdue": round(overdue, 2), "by_supplier": by_supplier,
        "by_nspt": by_header("nspt"), "by_department": by_header("department"),
        "by_item_group": by_item_group, "shipping": shipping, "inventory": inventory,
        "delivery": {"on_time": len(delivs) - len(late), "late": len(late), "total": len(delivs)},
        "late_deliveries": late_list, "inventory_value": round(inv_value, 2),
        "spend_by_month": spend_by_month,
    })
