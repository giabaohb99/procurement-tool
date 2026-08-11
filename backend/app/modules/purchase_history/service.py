"""Lịch sử mua hàng — ghi snapshot khi dòng ĐMH "Hoàn thành" + truy vấn cho UI."""
import json
import logging
from datetime import date

from sqlalchemy.orm import Session

from .model import PurchaseHistory

log = logging.getLogger(__name__)


def snapshot_line(db: Session, po, item) -> PurchaseHistory | None:
    """Ghi 1 record snapshot cho dòng vừa vào "Hoàn thành".

    Gọi từ `purchase_order.service.auto_advance_line` — chỉ `db.add()`, KHÔNG commit
    (caller commit trong cùng transaction với việc đổi `progress_status`).
    Trả None nếu đã có snapshot cho dòng này (idempotent).
    """
    exists = db.query(PurchaseHistory.id).filter(PurchaseHistory.po_item_id == item.id).first()
    if exists:
        return None

    # Tên pháp nhân — denormalize để bảng lịch sử tự đứng được, không phụ thuộc tab_company sau này
    company_name = ""
    if po.company_id:
        from app.modules.company.model import Company
        row = db.query(Company.name).filter(Company.id == po.company_id).first()
        company_name = row[0] if row else ""

    obj = PurchaseHistory(
        po_item_id=item.id,
        po_id=po.id,
        po_code=po.code or "",
        product_code=item.product_code or "",
        product_name=item.product_name or "",
        supplier_code=po.supplier_code or "",
        supplier_name=po.supplier_name or "",
        company_id=po.company_id or 0,
        company_name=company_name,
        order_date=po.order_date or "",
        unit=item.unit or "",
        qty_order=item.qty_order or 0,
        price=item.price or 0,
        vat=item.vat or 0,
        amount=item.amount or 0,
        completed_at=date.today().strftime("%Y-%m-%d"),
        extra=json.dumps({
            # Phần "Thông tin chung" còn lại của ĐMH
            "pr_code": po.pr_code or "",
            "misa_code": po.misa_code or "",
            "nspt": po.nspt or "",
            "payment_terms": po.payment_terms or "",
            "is_urgent": bool(po.is_urgent),
            "po_note": po.note or "",
            "department": po.department or "",
            # Phần còn lại của dòng hàng
            "item_group": item.item_group or "",
            "spec": item.spec or "",
            "invoice_name": item.invoice_name or "",
            "fg_code": item.fg_code or "",
            "fg_name": item.fg_name or "",
            "qty_received": float(item.qty_received or 0),
            "required_date": item.required_date or "",
            "invoice_no": item.invoice_no or "",
            "invoice_date": item.invoice_date or "",
            "warehouse_code": item.warehouse_code or "",
            "item_note": item.note or "",
        }, ensure_ascii=False),
    )
    db.add(obj)
    return obj


def snapshot_line_safe(db: Session, po, item) -> None:
    """Bọc `snapshot_line` — lỗi ghi lịch sử KHÔNG được chặn luồng tiến độ mua hàng."""
    try:
        snapshot_line(db, po, item)
    except Exception:
        log.exception("Không ghi được lịch sử mua hàng cho po_item_id=%s", getattr(item, "id", None))


def list_history(db: Session, pg: dict, product_code: str = "", supplier_code: str = "",
                 search: str = "", tim_theo_ncc: bool = True) -> tuple[int, list]:
    """Danh sách lịch sử, mới nhất trước. Lọc theo mã SP hoặc mã NCC (dùng chung cho 2 màn).

    `search`: tìm gần đúng trên Mã PO / Tên NCC / Tên SP / Tên công ty — phục vụ ô tìm kiếm
    của popup chọn lịch sử khi lập ĐMH.

    `tim_theo_ncc=False`: BỎ tên NCC khỏi vế tìm kiếm — dùng cho người không có quyền
    `supplier.read`. Nếu vẫn cho tìm theo tên NCC thì dù đã ẩn cột, gõ tên một NCC rồi
    xem có ra dòng nào không là suy ra được ai bán mã hàng đó — che cột thôi chưa đủ.
    """
    query = db.query(PurchaseHistory)
    if product_code:
        query = query.filter(PurchaseHistory.product_code == product_code)
    if supplier_code:
        query = query.filter(PurchaseHistory.supplier_code == supplier_code)
    if search.strip():
        from sqlalchemy import or_
        kw = f"%{search.strip()}%"
        ve = [PurchaseHistory.po_code.like(kw),
              PurchaseHistory.product_name.like(kw),
              PurchaseHistory.company_name.like(kw)]
        if tim_theo_ncc:
            ve.append(PurchaseHistory.supplier_name.like(kw))
        query = query.filter(or_(*ve))
    total = query.count()
    items = (query.order_by(PurchaseHistory.order_date.desc(), PurchaseHistory.id.desc())
             .offset(pg["offset"]).limit(pg["limit"]).all())
    return total, items
