"""API ỦY QUYỀN CÓ THỜI HẠN (I12)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import delegation_service, serializer
from .delegation_model import Delegation

router = APIRouter(prefix="/api/delegations", tags=["approval-delegation"])


class DelegationIn(BaseModel):
    from_employee_id: int = Field(gt=0)
    to_employee_id: int = Field(gt=0)
    entity: str = ""
    #  Hai ô ngày BẮT BUỘC — ủy quyền vô thời hạn là thứ người ta khai một lần
    #  rồi quên, và ba năm sau vẫn còn người ký thay một người đã nghỉ việc.
    from_date: date
    to_date: date
    is_active: bool = True
    reason: str = ""


@router.get("")
def list_delegations(employee_id: int = 0, db: Session = Depends(get_db),
                     user=Depends(require("approval_flow", "read"))):
    query = db.query(Delegation)
    if employee_id:
        query = query.filter(
            (Delegation.from_employee_id == employee_id)
            | (Delegation.to_employee_id == employee_id))
    rows = query.order_by(Delegation.to_date.desc(), Delegation.id.desc()).all()
    return success({"total": len(rows),
                    "items": [serializer.delegation_out(db, row) for row in rows]})


@router.post("")
def create_delegation(data: DelegationIn, db: Session = Depends(get_db),
                      user=Depends(require("approval_flow", "create"))):
    delegation_service.kiem_tra_truoc_khi_luu(
        db, data.from_employee_id, data.to_employee_id, data.entity,
        data.from_date, data.to_date)

    row = Delegation(**data.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    record(db, user.id, "approval_flow", row.id, "create", "Ủy quyền duyệt")
    return success(serializer.delegation_out(db, row), "Đã tạo ủy quyền", 201)


@router.patch("/{delegation_id}")
def update_delegation(delegation_id: int, data: DelegationIn,
                      db: Session = Depends(get_db),
                      user=Depends(require("approval_flow", "write"))):
    row = _load(db, delegation_id)
    delegation_service.kiem_tra_truoc_khi_luu(
        db, data.from_employee_id, data.to_employee_id, data.entity,
        data.from_date, data.to_date, bo_qua_id=row.id)

    for ten, gia_tri in data.model_dump().items():
        setattr(row, ten, gia_tri)
    row.updated_by = user.id
    db.commit()
    db.refresh(row)
    return success(serializer.delegation_out(db, row), "Đã lưu ủy quyền")


@router.delete("/{delegation_id}")
def delete_delegation(delegation_id: int, db: Session = Depends(get_db),
                      user=Depends(require("approval_flow", "delete"))):
    """Ngưng ủy quyền = TẮT, không xóa.

    Dấu vết duyệt trỏ vào `delegation_id`; xóa dòng là bản in mất câu «theo ủy
    quyền số 12» và không tra lại được ủy quyền đó từng có nội dung gì.
    """
    row = _load(db, delegation_id)
    row.is_active = False
    row.updated_by = user.id
    db.commit()
    record(db, user.id, "approval_flow", row.id, "update", "Ngưng ủy quyền")
    return success(None, "Đã ngưng ủy quyền")


def _load(db: Session, delegation_id: int) -> Delegation:
    row = db.get(Delegation, delegation_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy ủy quyền")
    return row
