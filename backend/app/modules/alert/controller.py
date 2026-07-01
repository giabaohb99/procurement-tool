"""Cảnh báo (Phase 3) — tính tại chỗ: giao trễ/sắp tới hạn, công nợ đến hạn/quá hạn, HĐ sắp hết hạn.

Endpoint GET /api/alerts cho chuông/badge. Worker (Celery) sẽ gọi cùng logic để tạo notification + email (bước sau)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.modules.contract.model import Contract
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder

router = APIRouter(prefix="/api/alerts", tags=["alert"])


def build(db: Session) -> dict:
    today = datetime.now().date()
    tstr = today.strftime("%Y-%m-%d")
    items = []

    def d_le(date_str, days):  # date_str <= today+days (và không rỗng)
        return date_str and date_str <= (today + timedelta(days=days)).strftime("%Y-%m-%d")

    # 1) Giao hàng: chưa nhận mà tới/quá hạn
    po_code = {p.id: p.code for p in db.query(PurchaseOrder).all()}
    item_name = {it.id: it.product_name for it in db.query(POItem).all()}
    for d in db.query(PODelivery).filter(PODelivery.received_qty <= 0).all():
        due = d.expected_date or d.promised_date
        if not due:
            continue
        link = f"/purchase-orders/{d.po_id}"
        name = item_name.get(d.po_item_id, "")
        if due < tstr:
            items.append({"type": "delivery", "level": "danger", "title": f"Giao hàng TRỄ: {po_code.get(d.po_id,'')} · {name} (hẹn {due})", "link": link})
        elif d_le(due, 2):
            items.append({"type": "delivery", "level": "warn", "title": f"Sắp tới hạn giao: {po_code.get(d.po_id,'')} · {name} (hẹn {due})", "link": link})

    # 2) Công nợ: chưa trả xong, đến/quá hạn
    for p in db.query(Payable).filter(Payable.status != "Đã TT").all():
        if not p.due_date:
            continue
        link = "/payables"
        who = p.supplier_name or p.supplier_code
        if p.due_date < tstr:
            items.append({"type": "payable", "level": "danger", "title": f"Công nợ QUÁ HẠN: {who} · {p.po_code} (hạn {p.due_date})", "link": link})
        elif d_le(p.due_date, 3):
            items.append({"type": "payable", "level": "warn", "title": f"Công nợ sắp đến hạn: {who} · {p.po_code} (hạn {p.due_date})", "link": link})

    # 3) Hợp đồng sắp hết hạn / hết hạn
    for c in db.query(Contract).filter(Contract.status != "Thanh lý").all():
        if not c.end_date:
            continue
        link = "/contracts"
        who = c.party_name or c.party_code
        if c.end_date < tstr:
            items.append({"type": "contract", "level": "danger", "title": f"Hợp đồng HẾT HẠN: {c.code} · {who} ({c.end_date})", "link": link})
        elif d_le(c.end_date, 30):
            items.append({"type": "contract", "level": "warn", "title": f"HĐ sắp hết hạn: {c.code} · {who} ({c.end_date})", "link": link})

    danger = sum(1 for x in items if x["level"] == "danger")
    return {"total": len(items), "danger": danger, "warn": len(items) - danger, "items": items}


@router.get("")
def list_alerts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return success(build(db))
