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
