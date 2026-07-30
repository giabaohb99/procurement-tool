from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import apply_filters, apply_range_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.modules.supplier.model import Supplier

from .model import Contract
from .schema import ContractCreate, ContractUpdate

router = APIRouter(prefix="/api/contracts", tags=["contract"])
FILTERABLE = ["code", "party_type", "party_code", "party_name", "status", "contract_type", "title"]


def expiry_state(end_date: str) -> str:
    if not end_date:
        return ""
    try:
        d = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return ""
    days = (d - datetime.now().date()).days
    if days < 0:
        return "Hết hạn"
    if days <= 30:
        return "Sắp hết hạn"
    return "Còn hạn"


def _fill_party(db: Session, c: Contract):
    """Điền tên đối tượng: nếu là Nhà cung cấp thì tra theo mã NCC."""
    if c.party_type == "Nhà cung cấp" and c.party_code:
        s = db.query(Supplier).filter(Supplier.code == c.party_code).first()
        if s:
            c.party_name = s.name


def _out(c: Contract) -> dict:
    return {"id": c.id, "code": c.code, "party_type": c.party_type, "party_code": c.party_code,
            "party_name": c.party_name, "company_id": c.company_id, "title": c.title,
            "contract_type": c.contract_type, "start_date": c.start_date, "end_date": c.end_date,
            "signed": bool(c.signed), "status": c.status, "note": c.note, "expiry": expiry_state(c.end_date)}


@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("contract", "read"))):
    q = apply_filters(db.query(Contract), Contract, request, FILTERABLE)
    q = apply_range_filters(q, Contract, request, ["end_date"])   # khoảng ngày hết hạn
    signed = request.query_params.get("signed")
    if signed in ("true", "false"):
        q = q.filter(Contract.signed == (signed == "true"))
    # Tình trạng hết hạn (tính theo end_date so với hôm nay)
    expiry = (request.query_params.get("expiry") or "").strip()
    if expiry:
        today = datetime.now().date()
        tstr = today.strftime("%Y-%m-%d")
        t30 = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        if expiry == "Hết hạn":
            q = q.filter(Contract.end_date != "", Contract.end_date < tstr)
        elif expiry == "Sắp hết hạn":
            q = q.filter(Contract.end_date >= tstr, Contract.end_date <= t30)
        elif expiry == "Còn hạn":
            q = q.filter(Contract.end_date > t30)
    total = q.count()
    q = apply_sort_from_request(q, Contract, request, default=Contract.id.desc())
    items = q.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [_out(c) for c in items]})


@router.get("/{cid}")
def get_(cid: int, db: Session = Depends(get_db), user=Depends(require("contract", "read"))):
    c = db.get(Contract, cid)
    if not c:
        raise HTTPException(404, "Không tìm thấy hợp đồng")
    return success(_out(c))


@router.post("")
def create_(data: ContractCreate, db: Session = Depends(get_db), user=Depends(require("contract", "create"))):
    c = Contract(**data.model_dump(exclude={"code"}), created_by=user.id, updated_by=user.id)
    if data.code:
        c.code = data.code
    _fill_party(db, c)
    db.add(c)
    db.commit()
    db.refresh(c)
    if not c.code:
        c.code = f"HD{c.id:05d}"
        db.commit()
    record(db, user.id, "contract", c.id, "create")
    return success(_out(c), "Đã tạo hợp đồng", 201)


@router.patch("/{cid}")
def update_(cid: int, data: ContractUpdate, db: Session = Depends(get_db), user=Depends(require("contract", "write"))):
    c = db.get(Contract, cid)
    if not c:
        raise HTTPException(404, "Không tìm thấy hợp đồng")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    _fill_party(db, c)
    c.updated_by = user.id
    db.commit()
    record(db, user.id, "contract", cid, "update")
    db.refresh(c)
    return success(_out(c), "Đã cập nhật")


@router.delete("/{cid}")
def delete_(cid: int, db: Session = Depends(get_db), user=Depends(require("contract", "delete"))):
    c = db.get(Contract, cid)
    if not c:
        raise HTTPException(404, "Không tìm thấy hợp đồng")
    from app.modules.attachment.service import delete_attachments_for
    delete_attachments_for(db, [("contract", cid)])
    db.delete(c)
    db.commit()
    record(db, user.id, "contract", cid, "delete")
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_contracts(ids: str, db: Session = Depends(get_db), user=Depends(require("contract", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    from app.modules.attachment.service import delete_attachments_for
    for cid in id_list:
        c = db.get(Contract, cid)
        if c:
            delete_attachments_for(db, [("contract", cid)])
            db.delete(c)
            record(db, user.id, "contract", cid, "delete")
    db.commit()
    return success(None, f"Đã xóa {len(id_list)} bản ghi")
