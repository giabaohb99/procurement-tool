from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(days: str = "30", db: Session = Depends(get_db), user=Depends(get_current_user)):
    from app.modules.employee.model import Employee
    from app.modules.product.model import Product
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.supplier.model import Supplier
    from app.modules.survey.model import Survey
    from app.modules.purchase_order.model import PurchaseOrder

    since = None
    if days != "all":
        try:
            n_days = int(days)
            since = datetime.now() - timedelta(days=n_days)
        except ValueError:
            pass

    def filter_since(query, model):
        if since is not None:
            return query.filter(model.created_at >= since)
        return query

    # General statistics
    suppliers_count = filter_since(db.query(Supplier), Supplier).count()
    products_count = filter_since(db.query(Product), Product).count()
    employees_count = filter_since(db.query(Employee), Employee).count()

    # PR / Purchase Request stats
    pr_query = db.query(PurchaseRequest)
    pr_total = filter_since(pr_query, PurchaseRequest).count()
    pr_pending = filter_since(pr_query.filter(PurchaseRequest.status == "submitted"), PurchaseRequest).count()
    pr_approved = filter_since(pr_query.filter(PurchaseRequest.status == "approved"), PurchaseRequest).count()

    # Survey stats (Real data)
    survey_query = db.query(Survey)
    survey_pending = filter_since(survey_query.filter(Survey.status == "submitted"), Survey).count()

    # PO / Purchase Order stats (Real data)
    po_query = db.query(PurchaseOrder)
    po_ordered = filter_since(po_query.filter(PurchaseOrder.status.in_(["approved", "partial", "received"])), PurchaseOrder).count()
    po_delivered = filter_since(po_query.filter(PurchaseOrder.status == "received"), PurchaseOrder).count()
    po_partial = filter_since(po_query.filter(PurchaseOrder.status == "partial"), PurchaseOrder).count()
    po_completed = filter_since(po_query.filter(PurchaseOrder.status == "completed"), PurchaseOrder).count()

    # Generate trend data based on timeframe
    trends = []
    end_date = datetime.now()
    if days == "7":
        steps = 7
        interval_days = 1
    elif days == "30":
        steps = 6
        interval_days = 5
    else:  # all
        steps = 6
        interval_days = 30

    for i in range(steps - 1, -1, -1):
        d = end_date - timedelta(days=i * interval_days)
        d_str = d.strftime("%d/%m")

        start_range = d.replace(hour=0, minute=0, second=0)
        end_range = d.replace(hour=23, minute=59, second=59)
        if interval_days > 1:
            start_range = (d - timedelta(days=interval_days - 1)).replace(hour=0, minute=0, second=0)

        pr_cnt = db.query(PurchaseRequest).filter(
            PurchaseRequest.created_at >= start_range,
            PurchaseRequest.created_at <= end_range
        ).count()

        po_cnt = db.query(PurchaseOrder).filter(
            PurchaseOrder.created_at >= start_range,
            PurchaseOrder.created_at <= end_range
        ).count()

        trends.append({"label": d_str, "pr": pr_cnt, "po": po_cnt})

    return success({
        "suppliers": suppliers_count,
        "products": products_count,
        "employees": employees_count,
        "pr_total": pr_total,
        "pr_pending": pr_pending,
        "pr_processing": pr_approved,
        "survey_pending": survey_pending,
        "po_ordered": po_ordered,
        "po_delivered": po_delivered,
        "po_partial": po_partial,
        "po_completed": po_completed,
        "trends": trends,
    })


@router.get("/overview")
def overview(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tổng hợp trang chủ — LỌC THEO QUYỀN + PHẠM VI. Khối nào user không có quyền Xem
    entity tương ứng → trả rỗng (FE tự ẩn). Số liệu tính trong phạm vi của user."""
    from app.core.auth import get_perm_profile
    from app.core.scoping import apply_scope
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
    from app.modules.purchase_order.model import PurchaseOrder, POItem, PODelivery
    from app.modules.payable.model import Payable
    from app.modules.contract.model import Contract
    from app.modules.inventory.model import Inventory
    from app.modules.survey.model import Survey
    from app.modules.alert.controller import build as build_alerts

    prof = get_perm_profile(db, user)

    def can(e):
        return bool(prof["perms_union"].get(e, {}).get("read"))

    today = datetime.now().date()
    tstr = today.strftime("%Y-%m-%d")
    in7 = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    in30 = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    def item_amt(it):
        a = float(it.amount or 0)
        return a if a > 0 else float(it.qty_order or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)

    kpi = {}
    cost_12m, categories, top_suppliers, dept_spend = [], [], [], []
    po_status, ap_aging, recent_pos, recent_prs, low_stock = [], [], [], [], []
    target_year = str(today.year)

    # ===== Yêu cầu mua =====
    if can("purchase_request"):
        prq = apply_scope(db.query(PurchaseRequest), PurchaseRequest, "purchase_request", user, prof)
        kpi["pr_pending"] = prq.filter(PurchaseRequest.status == "submitted").count()
        rprs = apply_scope(db.query(PurchaseRequest), PurchaseRequest, "purchase_request", user, prof) \
            .order_by(PurchaseRequest.id.desc()).limit(8).all()
        for pr in rprs:
            amt = sum(float(it.amount or 0) for it in db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all())
            recent_prs.append({"id": pr.id, "code": pr.code, "requester": pr.requester,
                               "description": pr.purpose or "Yêu cầu mua hàng", "department": pr.department or "",
                               "date": pr.request_date or tstr, "status": pr.status, "total": round(amt, 0)})

    # ===== Đơn mua hàng + phân tích =====
    if can("purchase_order"):
        scoped_pos = apply_scope(db.query(PurchaseOrder), PurchaseOrder, "purchase_order", user, prof).all()
        pos = {p.id: p for p in scoped_pos}
        po_ids = list(pos.keys())
        items = {it.id: it for it in db.query(POItem).filter(POItem.po_id.in_(po_ids)).all()} if po_ids else {}
        delivs = db.query(PODelivery).filter(PODelivery.po_id.in_(po_ids), PODelivery.received_qty > 0).all() if po_ids else []
        kpi["po_ordered"] = sum(1 for p in pos.values() if p.status in ("approved", "partial", "received"))
        late_src = db.query(PODelivery).filter(PODelivery.po_id.in_(po_ids), PODelivery.received_qty <= 0).all() if po_ids else []
        kpi["late_deliveries"] = sum(1 for d in late_src if (d.expected_date or d.promised_date) and (d.expected_date or d.promised_date) < tstr)

        cat, sup, dept, po_total = {}, {}, {}, {}
        for it in items.values():
            amt = item_amt(it)
            po = pos.get(it.po_id)
            po_total[it.po_id] = po_total.get(it.po_id, 0) + amt
            cat[it.item_group or "(Không rõ)"] = cat.get(it.item_group or "(Không rõ)", 0) + amt
            nm = (po.supplier_name or po.supplier_code) if po else "(Không rõ)"
            sup[nm] = sup.get(nm, 0) + amt
            dp = (po.department if po and po.department else "(Không rõ)")
            dept[dp] = dept.get(dp, 0) + amt

        def top_list(dic, kk, vk, n=5):
            return [{kk: k2, vk: round(v, 0)} for k2, v in sorted(dic.items(), key=lambda x: -x[1])[:n]]

        cs = sorted(cat.items(), key=lambda x: -x[1])
        ct = sum(v for _, v in cs) or 1
        categories = [{"name": k2, "cost": round(v, 0), "pct": round(v / ct * 100, 1)} for k2, v in cs[:4]]
        other = sum(v for _, v in cs[4:])
        if other > 0:
            categories.append({"name": "Khác", "cost": round(other, 0), "pct": round(other / ct * 100, 1)})
        top_suppliers = top_list(sup, "name", "value")
        dept_spend = top_list(dept, "name", "value")

        years = {(d.received_date or "")[:4] for d in delivs if d.received_date}
        years.discard("")
        target_year = max(years) if years else str(today.year)
        mc = {f"{m:02d}": 0.0 for m in range(1, 13)}
        for d in delivs:
            it = items.get(d.po_item_id)
            rd = d.received_date or ""
            if it and rd[:4] == target_year and len(rd) >= 7:
                mc[rd[5:7]] += float(d.received_qty or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)
        cost_12m = [{"label": f"T{int(m)}", "value": round(mc[m], 0)} for m in sorted(mc)]

        ST = [("draft", "Nháp"), ("submitted", "Chờ duyệt"), ("approved", "Đã duyệt"),
              ("partial", "Giao 1 phần"), ("received", "Đã nhận"), ("completed", "Hoàn thành"), ("cancelled", "Đã hủy")]
        scount = {}
        for p in pos.values():
            scount[p.status] = scount.get(p.status, 0) + 1
        po_status = [{"key": k2, "label": lb, "value": scount.get(k2, 0)} for k2, lb in ST if scount.get(k2, 0) > 0]

        recent = sorted(pos.values(), key=lambda p: (p.order_date or "", p.id), reverse=True)[:8]
        recent_pos = [{"id": p.id, "code": p.code, "supplier": p.supplier_name or p.supplier_code,
                       "order_date": p.order_date, "status": p.status, "total": round(po_total.get(p.id, 0), 0)} for p in recent]

    # ===== Khảo sát =====
    if can("survey"):
        kpi["survey_pending"] = apply_scope(db.query(Survey), Survey, "survey", user, prof).filter(Survey.status == "submitted").count()

    # ===== Công nợ =====
    if can("payable"):
        pays = apply_scope(db.query(Payable), Payable, "payable", user, prof).filter(Payable.status != "Đã TT").all()
        kpi["due_soon"] = round(sum(float(p.remaining or 0) for p in pays if p.due_date and tstr <= p.due_date <= in7), 0)
        kpi["overdue"] = round(sum(float(p.remaining or 0) for p in pays if p.due_date and p.due_date < tstr), 0)
        aging = {"Chưa đến hạn": 0.0, "1–30 ngày": 0.0, "31–60 ngày": 0.0, "> 60 ngày": 0.0}
        for p in pays:
            rem = float(p.remaining or 0)
            if rem <= 0:
                continue
            if not p.due_date or p.due_date >= tstr:
                aging["Chưa đến hạn"] += rem
            else:
                od = (today - datetime.strptime(p.due_date, "%Y-%m-%d").date()).days
                aging["1–30 ngày" if od <= 30 else "31–60 ngày" if od <= 60 else "> 60 ngày"] += rem
        ap_aging = [{"label": k2, "value": round(v, 0)} for k2, v in aging.items()]

    # ===== Hợp đồng (dùng chung) =====
    if can("contract"):
        kpi["contract_expiring"] = db.query(Contract).filter(
            Contract.status != "Thanh lý", Contract.end_date != "", Contract.end_date <= in30).count()

    # ===== Tồn kho =====
    if can("inventory"):
        invs = apply_scope(db.query(Inventory), Inventory, "inventory", user, prof).all()
        kpi["inv_value"] = round(sum(float(i.value or 0) for i in invs), 2)
        kpi["out_of_stock"] = sum(1 for i in invs if float(i.qty or 0) <= 0)
        low_stock = [{"product_code": i.product_code, "product_name": i.product_name, "qty": float(i.qty or 0),
                      "unit": i.unit, "warehouse_code": i.warehouse_code}
                     for i in sorted(invs, key=lambda x: float(x.qty or 0))[:8]]

    # ===== Cảnh báo (lọc theo quyền từng loại) =====
    def alert_ok(it):
        t = it.get("type")
        return (t == "payable" and can("payable")) or (t == "contract" and can("contract")) or (t == "delivery" and can("purchase_order"))
    al_items = [x for x in build_alerts(db)["items"] if alert_ok(x)]

    can_map = {e: can(e) for e in ["purchase_request", "purchase_order", "survey", "payable", "contract", "inventory", "report"]}

    return success({
        "year": target_year,
        "kpi": kpi,
        "cost_12m": cost_12m,
        "categories": categories,
        "top_suppliers": top_suppliers,
        "dept_spend": dept_spend,
        "po_status": po_status,
        "ap_aging": ap_aging,
        "recent_pos": recent_pos,
        "recent_prs": recent_prs,
        "low_stock": low_stock,
        "alerts": al_items[:6],
        "alert_total": len(al_items),
        "can": can_map,
    })
