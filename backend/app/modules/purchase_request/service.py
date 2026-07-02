from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import PurchaseRequest, PurchaseRequestItem
from .schema import PRCreate, PRUpdate

FILTERABLE = ["code", "status", "requester", "department"]
ENTITY = "purchase_request"


def _save_items(db: Session, pr_id: int, items, user_id: int):
    db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr_id).delete()
    for it in items or []:
        data = it.model_dump()
        data["amount"] = round((data.get("qty") or 0) * (data.get("price") or 0), 2)
        db.add(PurchaseRequestItem(pr_id=pr_id, created_by=user_id, updated_by=user_id, **data))
    db.commit()


def items_of(db: Session, pr_id: int):
    return db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr_id).all()


def get_pr(db: Session, pid: int) -> PurchaseRequest:
    obj = db.get(PurchaseRequest, pid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy yêu cầu mua")
    return obj


def list_pr(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(PurchaseRequest.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def create_pr(db: Session, data: PRCreate, user_id: int) -> PurchaseRequest:
    pr = PurchaseRequest(
        code=data.code or "", company_id=data.company_id, requester=data.requester,
        requester_position=data.requester_position, department=data.department,
        head_of_dept=data.head_of_dept, purpose=data.purpose, request_date=data.request_date,
        need_date=data.need_date, is_urgent=data.is_urgent, vat_rate=data.vat_rate,
        note=data.note, status="draft", created_by=user_id, updated_by=user_id,
        show_code_on_print=data.show_code_on_print,
        suggested_supplier=data.suggested_supplier,
        suggested_supplier_tax_code=data.suggested_supplier_tax_code,
        suggested_supplier_contact=data.suggested_supplier_contact,
        quote_filename=data.quote_filename,
        quote_file_url=data.quote_file_url,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    if not pr.code:
        date_str = ""
        if pr.request_date and len(pr.request_date) >= 10 and "-" in pr.request_date:
            parts = pr.request_date.split("-")
            if len(parts) == 3:
                date_str = f"{parts[2]}{parts[1]}{parts[0][-2:]}"
        if not date_str:
            from datetime import datetime
            date_str = datetime.now().strftime("%d%m%y")
            
        prefix = f"PYC{date_str}"
        last_pr = db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{prefix}%")).order_by(PurchaseRequest.code.desc()).first()
        
        seq = 1
        if last_pr and last_pr.code.startswith(prefix):
            try:
                seq = int(last_pr.code[len(prefix):]) + 1
            except ValueError:
                seq = 1
                
        pr.code = f"{prefix}{seq:02d}"
        db.commit()
    _save_items(db, pr.id, data.items, user_id)
    record(db, user_id, ENTITY, pr.id, "create")
    return pr


def update_pr(db: Session, pid: int, data: PRUpdate, user_id: int) -> PurchaseRequest:
    pr = get_pr(db, pid)
    if pr.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi ở trạng thái Nháp/Từ chối")
    for key, value in data.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(pr, key, value)
    pr.updated_by = user_id
    db.commit()
    if data.items is not None:
        _save_items(db, pid, data.items, user_id)
    record(db, user_id, ENTITY, pid, "update")
    db.refresh(pr)
    return pr


def delete_pr(db: Session, pid: int, user_id: int) -> None:
    pr = get_pr(db, pid)
    db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pid).delete()
    db.delete(pr)
    db.commit()
    record(db, user_id, ENTITY, pid, "delete")


def set_status(db: Session, pid: int, status: str, user_id: int, message: str = "") -> PurchaseRequest:
    pr = get_pr(db, pid)
    pr.status = status
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, status, message)
    db.refresh(pr)
    return pr
