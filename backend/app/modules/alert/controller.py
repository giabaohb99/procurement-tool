"""Cảnh báo (Phase 3) — tính tại chỗ: giao trễ/sắp tới hạn, công nợ đến hạn/quá hạn, HĐ sắp hết hạn.

Endpoint GET /api/alerts cho chuông/badge. Worker (Celery) sẽ gọi cùng logic để tạo notification + email (bước sau)."""
from datetime import datetime, timedelta
from urllib.parse import quote

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_perm_profile, user_has_permission
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.contract.model import Contract
from app.modules.dashboard.service import load_dismissed_keys
from app.modules.payable.model import Payable
from app.modules.payable.service import ST_PAID
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder

router = APIRouter(prefix="/api/alerts", tags=["alert"])


def build(db: Session, user=None) -> dict:
    """Cảnh báo cho CHUÔNG — chỉ hiện phần người xem CÓ QUYỀN đọc (không gửi email).

    Mỗi khối còn lọc `apply_scope` theo phạm vi dữ liệu của người xem — quyền đọc
    cho qua cửa, nhưng chỉ thấy chứng từ trong phạm vi của mình (vd trưởng phòng
    scope company không thấy hợp đồng pháp nhân khác).

    Mỗi cảnh báo mang `key` ổn định (bản ghi gốc + mức) và BỎ QUA những key người
    xem đã "Đánh dấu làm hết" ở tab Việc cần làm (CR-215) — chuông, tab và
    dashboard cùng một trạng thái. Key kèm mức nên cảnh báo "sắp tới hạn" đã ẩn
    vẫn nổi lại khi leo thang thành "quá hạn"."""
    today = datetime.now().date()
    tstr = today.strftime("%Y-%m-%d")
    items = []

    # Ai được thấy loại cảnh báo nào (theo quyền read). user=None (worker) → thấy tất cả.
    see_delivery = user is None or user_has_permission(db, user, "purchase_order", "read")
    see_payable = user is None or user_has_permission(db, user, "payable", "read")
    see_contract = user is None or user_has_permission(db, user, "contract", "read")
    profile = get_perm_profile(db, user) if user is not None else None
    dismissed = load_dismissed_keys(db, user) if user is not None else set()

    def scoped(query, model, entity):
        return query if profile is None else apply_scope(query, model, entity, user, profile)

    def push(key, item):
        if key not in dismissed:
            items.append({"key": key, **item})

    def d_le(date_str, days):  # date_str <= today+days (và không rỗng)
        return date_str and date_str <= (today + timedelta(days=days)).strftime("%Y-%m-%d")

    # 1) Giao hàng: chưa nhận mà tới/quá hạn
    if see_delivery:
        # po_code chỉ chứa đơn TRONG PHẠM VI người xem — dòng giao của đơn ngoài
        # phạm vi bị bỏ qua ở vòng lặp dưới.
        po_code = {p.id: p.code
                   for p in scoped(db.query(PurchaseOrder), PurchaseOrder, "purchase_order").all()}
        item_name = {it.id: it.product_name for it in db.query(POItem).all()}
        for d in db.query(PODelivery).filter(PODelivery.received_qty <= 0).all():
            if d.po_id not in po_code:
                continue
            # Hạn giao = NCC cam kết giao. Trước đây ưu tiên `expected_date` của lần giao,
            # nhưng cột đó không nơi nào ghi (chỉ có 10 dòng rác nạp tay) nên nó thắng bằng
            # dữ liệu sai — đã bỏ dùng, xem migration e2c5a81f7b60.
            due = d.promised_date
            if not due:
                continue
            link = f"/purchase-orders/{d.po_id}"
            name = item_name.get(d.po_item_id, "")
            if due < tstr:
                push(f"delivery:{d.id}:danger", {"type": "delivery", "level": "danger", "title": f"Giao hàng TRỄ: {po_code.get(d.po_id,'')} · {name} (hẹn {due})", "link": link})
            elif d_le(due, 2):
                push(f"delivery:{d.id}:warn", {"type": "delivery", "level": "warn", "title": f"Sắp tới hạn giao: {po_code.get(d.po_id,'')} · {name} (hẹn {due})", "link": link})

    # 2) Công nợ: chưa trả xong, đến/quá hạn
    if see_payable:
        for p in scoped(db.query(Payable).filter(Payable.status != ST_PAID),
                        Payable, "payable").all():
            if not p.due_date:
                continue
            # Click vào cảnh báo -> nhảy tới màn Công nợ, lọc sẵn theo NCC của khoản nợ
            link = f"/payables?po_code={quote(p.po_code or '')}" if p.po_code else "/payables"
            who = p.supplier_name or p.supplier_code
            if p.due_date < tstr:
                push(f"payable:{p.id}:danger", {"type": "payable", "level": "danger", "title": f"Công nợ QUÁ HẠN: {who} · {p.po_code} (hạn {p.due_date})", "link": link})
            elif d_le(p.due_date, 3):
                push(f"payable:{p.id}:warn", {"type": "payable", "level": "warn", "title": f"Công nợ sắp đến hạn: {who} · {p.po_code} (hạn {p.due_date})", "link": link})

    # 3) Hợp đồng sắp hết hạn / hết hạn
    if see_contract:
        # B-02: mã của bộ `CONTRACT_STATUS` (`app/core/status_codes.py`), trước là "Thanh lý".
        for c in scoped(db.query(Contract).filter(Contract.status != "liquidated"),
                        Contract, "contract").all():
            if not c.end_date:
                continue
            link = f"/contracts/{c.id}"
            who = c.party_name or c.party_code
            if c.end_date < tstr:
                push(f"contract:{c.id}:danger", {"type": "contract", "level": "danger", "title": f"Hợp đồng HẾT HẠN: {c.code} · {who} ({c.end_date})", "link": link})
            elif d_le(c.end_date, 30):
                push(f"contract:{c.id}:warn", {"type": "contract", "level": "warn", "title": f"HĐ sắp hết hạn: {c.code} · {who} ({c.end_date})", "link": link})

    danger = sum(1 for x in items if x["level"] == "danger")
    return {"total": len(items), "danger": danger, "warn": len(items) - danger, "items": items}


@router.get("")
def list_alerts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return success(build(db, user))
