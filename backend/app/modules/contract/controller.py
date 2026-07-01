from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.modules.supplier.model import Supplier

from .model import Contract
from .schema import ContractCreate, ContractUpdate

router = APIRouter(prefix="/api/contracts", tags=["contract"])
FILTERABLE = ["code", "party_type", "party_code", "status", "contract_type", "title"]


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
    total = q.count()
    items = q.order_by(Contract.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
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
    db.delete(c)
    db.commit()
    record(db, user.id, "contract", cid, "delete")
    return success(None, "Đã xóa")
