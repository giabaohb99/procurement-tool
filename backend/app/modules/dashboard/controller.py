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
        
        trends.append({
            "label": d_str,
            "pr": pr_cnt,
            "po": po_cnt
        })

    return success({
        "suppliers": suppliers_count,
        "products": products_count,
        "employees": employees_count,
        "pr_total": pr_total,

        # Details required by user (Real data)
        "pr_pending": pr_pending,                 # Yêu cầu chờ
        "pr_processing": pr_approved,             # Đang xử lý
        "survey_pending": survey_pending,         # Khảo sát chờ
        "po_ordered": po_ordered,                 # PO đã đặt hàng
        "po_delivered": po_delivered,             # Đã giao
        "po_partial": po_partial,                 # Giao chưa đủ
        "po_completed": po_completed,             # Hoàn thành
        "trends": trends,
    })


@router.get("/overview")
def overview(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Dữ liệu tổng hợp cho trang chủ: KPI · chi phí 12 tháng · cơ cấu phân loại · top NCC · cảnh báo · tồn thấp."""
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.purchase_order.model import PurchaseOrder, POItem, PODelivery
    from app.modules.payable.model import Payable
    from app.modules.contract.model import Contract
    from app.modules.inventory.model import Inventory
    from app.modules.survey.model import Survey
    from app.modules.alert.controller import build as build_alerts

    today = datetime.now().date()
    tstr = today.strftime("%Y-%m-%d")
    in7 = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    in30 = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    # ---- Nạp dữ liệu 1 lần ----
    pos = {p.id: p for p in db.query(PurchaseOrder).all()}
    items = {it.id: it for it in db.query(POItem).all()}
    delivs = db.query(PODelivery).filter(PODelivery.received_qty > 0).all()
    invs = db.query(Inventory).all()
    payables = db.query(Payable).filter(Payable.status != "Đã TT").all()

    def item_amt(it):
        a = float(it.amount or 0)
        return a if a > 0 else float(it.qty_order or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)

    # ---- KPI ----
    pr_pending = db.query(PurchaseRequest).filter(PurchaseRequest.status == "submitted").count()
    survey_pending = db.query(Survey).filter(Survey.status == "submitted").count()
    po_ordered = sum(1 for p in pos.values() if p.status in ("approved", "partial", "received"))
    late_deliveries = sum(
        1 for d in db.query(PODelivery).filter(PODelivery.received_qty <= 0).all()
        if (d.expected_date or d.promised_date) and (d.expected_date or d.promised_date) < tstr
    )
    due_soon = sum(float(p.remaining or 0) for p in payables if p.due_date and tstr <= p.due_date <= in7)
    overdue = sum(float(p.remaining or 0) for p in payables if p.due_date and p.due_date < tstr)
    contract_expiring = db.query(Contract).filter(
        Contract.status != "Thanh lý", Contract.end_date != "", Contract.end_date <= in30
    ).count()
    out_of_stock = sum(1 for i in invs if float(i.qty or 0) <= 0)
    inv_value = round(sum(float(i.value or 0) for i in invs), 2)

    # ---- Quét theo ĐƠN ĐẶT (cơ cấu phân loại · top NCC · chi tiêu bộ phận · tổng đơn) ----
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

    def top_list(dic, key_name, val_name, n=5):
        return [{key_name: k, val_name: round(v, 0)} for k, v in sorted(dic.items(), key=lambda x: -x[1])[:n]]

    cat_sorted = sorted(cat.items(), key=lambda x: -x[1])
    cat_total = sum(v for _, v in cat_sorted) or 1
    categories = [{"name": k, "cost": round(v, 0), "pct": round(v / cat_total * 100, 1)} for k, v in cat_sorted[:4]]
    other = sum(v for _, v in cat_sorted[4:])
    if other > 0:
        categories.append({"name": "Khác", "cost": round(other, 0), "pct": round(other / cat_total * 100, 1)})
    top_suppliers = top_list(sup, "name", "value")
    dept_spend = top_list(dept, "name", "value")

    # ---- Chi phí NHẬN theo tháng (năm có dữ liệu gần nhất) ----
    years = {(d.received_date or "")[:4] for d in delivs if d.received_date}
    years.discard("")
    target_year = max(years) if years else str(today.year)
    month_cost = {f"{m:02d}": 0.0 for m in range(1, 13)}
    for d in delivs:
        it = items.get(d.po_item_id)
        rd = d.received_date or ""
        if it and rd[:4] == target_year and len(rd) >= 7:
            month_cost[rd[5:7]] += float(d.received_qty or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)
    cost_12m = [{"label": f"T{int(m)}", "value": round(month_cost[m], 0)} for m in sorted(month_cost)]

    # ---- Trạng thái đơn hàng ----
    ST = [("draft", "Nháp"), ("submitted", "Chờ duyệt"), ("approved", "Đã duyệt"),
          ("partial", "Giao 1 phần"), ("received", "Đã nhận"), ("completed", "Hoàn thành"), ("cancelled", "Đã hủy")]
    scount = {}
    for p in pos.values():
        scount[p.status] = scount.get(p.status, 0) + 1
    po_status = [{"key": k, "label": lb, "value": scount.get(k, 0)} for k, lb in ST if scount.get(k, 0) > 0]

    # ---- Tuổi nợ (aging) theo tiền còn phải trả ----
    aging = {"Chưa đến hạn": 0.0, "1–30 ngày": 0.0, "31–60 ngày": 0.0, "> 60 ngày": 0.0}
    for p in payables:
        rem = float(p.remaining or 0)
        if rem <= 0:
            continue
        if not p.due_date or p.due_date >= tstr:
            aging["Chưa đến hạn"] += rem
        else:
            od = (today - datetime.strptime(p.due_date, "%Y-%m-%d").date()).days
            aging["1–30 ngày" if od <= 30 else "31–60 ngày" if od <= 60 else "> 60 ngày"] += rem
    ap_aging = [{"label": k, "value": round(v, 0)} for k, v in aging.items()]

    # ---- Đơn hàng gần đây ----
    recent = sorted(pos.values(), key=lambda p: (p.order_date or "", p.id), reverse=True)[:8]
    recent_pos = [{
        "id": p.id, "code": p.code, "supplier": p.supplier_name or p.supplier_code,
        "order_date": p.order_date, "status": p.status, "total": round(po_total.get(p.id, 0), 0),
    } for p in recent]

    # ---- Yêu cầu mua gần đây (Recent PRs) ----
    from app.modules.purchase_request.model import PurchaseRequestItem
    recent_prs_query = db.query(PurchaseRequest).order_by(PurchaseRequest.id.desc()).limit(8).all()
    recent_prs = []
    for pr in recent_prs_query:
        total_amt = sum(float(it.amount or 0) for it in db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all())
        recent_prs.append({
            "id": pr.id,
            "code": pr.code,
            "requester": pr.requester,
            "description": pr.purpose or "Yêu cầu mua hàng",
            "department": pr.department or "Mua hàng",
            "date": pr.request_date or (pr.created_at.strftime("%Y-%m-%d") if pr.created_at else tstr),
            "status": pr.status,
            "total": round(total_amt, 0),
        })

    # ---- Tồn thấp + Cảnh báo ----
    low_stock = [
        {"product_code": i.product_code, "product_name": i.product_name, "qty": float(i.qty or 0),
         "unit": i.unit, "warehouse_code": i.warehouse_code}
        for i in sorted(invs, key=lambda x: float(x.qty or 0))[:8]
    ]
    al = build_alerts(db)

    return success({
        "year": target_year,
        "kpi": {
            "pr_pending": pr_pending,
            "po_ordered": po_ordered,
            "late_deliveries": late_deliveries,
            "survey_pending": survey_pending,
            "due_soon": round(due_soon, 0),
            "overdue": round(overdue, 0),
            "contract_expiring": contract_expiring,
            "inv_value": inv_value,
            "out_of_stock": out_of_stock,
        },
        "cost_12m": cost_12m,
        "categories": categories,
        "top_suppliers": top_suppliers,
        "dept_spend": dept_spend,
        "po_status": po_status,
        "ap_aging": ap_aging,
        "recent_pos": recent_pos,
        "recent_prs": recent_prs,
        "low_stock": low_stock,
        "alerts": al["items"][:6],
        "alert_total": al["total"],
    })
